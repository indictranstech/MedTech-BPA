import json
import frappe
from frappe import _
from frappe.utils import flt, today, add_days
from erpnext.accounts.report.general_ledger.general_ledger import execute

@frappe.whitelist()
def get_pending_so(**kwargs):
	try:
		data = {"items": [], "customer": "", "pending_bal": 0, "closing_bal": 0}
		sa_data = {}
		customer = ''
		unpaid_dn_amt = 0
		sa_total_amt = 0
		sa_items = {}
		payment_entry = kwargs.get("payment_entry")
		customer = kwargs.get("customer") or \
			kwargs.get("stock_allocation_party")

		if customer:

			# unpaid delivery note amount
			unpaid_dn_amt = frappe.db.sql("""
				select
					sum(
						CASE when per_billed > 0
						THEN grand_total - per_billed/100
						ELSE grand_total END
					) as unpaid_amt
				from `tabDelivery Note`
				where status in ('To Bill') and docstatus = 1
				and customer = '{}'
			""".format(customer), as_dict=True)
			unpaid_dn_amt = unpaid_dn_amt[0]["unpaid_amt"] or 0

			# warehouse
			warehouse = frappe.db.get_singles_value("MedTech Settings", "rm_warehouse")
	
			warehouse_cond = ''
			if warehouse:
				warehouse_cond += "and b.warehouse = '{}'".format(warehouse)
			else:
				warehouse_cond += "and soi.warehouse = b.warehouse"

			#filters for general ledger
			filters = frappe._dict({
				"to_date": today(),
				"from_date": add_days(today(), -30),
				"company": frappe.defaults.get_user_default("Company"),
				"party": [customer],
				"party_type": "Customer",
				"group_by": "Group by Voucher (Consolidated)",
				"cost_center": [], "project": []
			})

			closing_bal = ledger_bal = pending_bal = 0

			#general_ledger_report data for closing bal
			gl_data = execute(filters)
			data_ = gl_data[1] if len(data) else []
			ledger_bal = data_[-1]["balance"]

			# gl data for closing balance
			filters.update({
				"to_date": kwargs.get("posting_date"),
				"from_date": add_days(kwargs.get("posting_date"), -30)
			})

			gl_data = execute(filters)

			if not payment_entry:
				pe_data = frappe.db.sql("""select name
					from `tabPayment Entry` where party = '{0}'
					and docstatus = 1  and posting_date = '{1}'
					order by creation desc limit 1
				""".format(customer, kwargs.get("posting_date")), as_dict=True)
				if len(pe_data):
					payment_entry = pe_data[0]["name"]

			if payment_entry:
				for row in gl_data[1]:
					if row.get("voucher_no") == payment_entry:
						closing_bal = row.get("balance")

			query = """
				select
					so.name, so.customer, so.workflow_state as status, 
					so.transaction_date, soi.item_code, soi.item_name,
					(soi.qty - soi.delivered_qty) as qty,
					CASE WHEN (soi.rate_with_tax = 0)
						THEN soi.rate
						ELSE soi.rate_with_tax
					END as rate, soi.amount,
					b.actual_qty as stock_qty, 0 as carton_qty, 0 as revised_amt, 0 as approval, '' as remark
				from
					`tabSales Order` so
				left join
					`tabSales Order Item` soi
				on
					so.name = soi.parent
				left join
					`tabBin` b
				on soi.item_code = b.item_code
				{}
				where
					so.customer = '{}'
					and (soi.qty - soi.delivered_qty) > 0
					and so.status != 'Closed'
					
					and so.docstatus = 1
			""".format(warehouse_cond, customer)
			# and so.delivery_status in ('Not Delivered', 'Partly Delivered')
			# and so.workflow_state = 'PI Pending'
			so_data = frappe.db.sql(query, as_dict=True)

			# existing stock allocation data merge
			if int(kwargs.get("fetch_existing", 0)):
				sa = frappe.db.get_value("Stock Allocation", {
					"customer": customer,
					"docstatus": 0
				})
				if sa:
					sa_doc = frappe.get_doc("Stock Allocation", sa)

					# localstorage seq: [0:qty, 1:rate, 2:amount, 3:sales_order, 4:is_approved, 5:remark]
					for row in sa_doc.items:
						sa_items[row.item_code] = [row.qty, row.rate, row.amount,
							row.against_sales_order, row.is_approved, row.remarks
						]

					# merge
					for r in so_data:
						if r.item_code in sa_items and \
						r.name == sa_items[r.item_code][3]:
							r["carton_qty"] = sa_items[r.item_code][0]
							r["rate"] = sa_items[r.item_code][1]
							r["revised_amt"] = sa_items[r.item_code][2]
							r["approval"] = sa_items[r.item_code][4]
							r["remark"] = sa_items[r.item_code][5]
							sa_total_amt += sa_items[r.item_code][2]

					sa_data["total_amount"] = sa_total_amt
			# get on hand stock
			ohs_detail = get_ohs_qty()
			for row in so_data:
				if row.item_code in ohs_detail:
					row['actual_stock_qty'] = ohs_detail.get(row.item_code)
			data["sa_items"] = sa_items
			data["sa_total_amt"] = sa_total_amt
			data["items"] = so_data
			data["customer"] = customer
			data["pending_bal"] = (closing_bal * -1) - (unpaid_dn_amt + sa_total_amt)
			data["closing_bal"] = closing_bal * -1
			data["ledger_bal"] = ledger_bal * -1
			data["unpaid_dn_amt"] = unpaid_dn_amt
	
		return data
	except Exception as e:
		print("#################### Error:", str(e))
		frappe.msgprint(_("Something went wrong, while fetching the data."))

@frappe.whitelist()
def save_stock_allocation(data)	:
	try:
		data = json.loads(data)
		if data:
			existing_allocation = frappe.db.get_value("Stock Allocation", {
				"customer": data.get("customer"),
				"docstatus": 0
			})
			if existing_allocation:
				sa = frappe.get_doc("Stock Allocation", existing_allocation)
				sa.items = []
			else:
				sa = frappe.new_doc("Stock Allocation")
				sa.customer = data.get("customer")
				sa.posting_date = today()

			total_amt = 0
			for k, v in data.get("items", {}).items():
				# [qty, rate, amount, sales_order, is_approved, remark]
				if v[3]:
					total_amt += int(v[0]) * flt(v[1])
					sa.append("items", {
						"item_code": k,
						"qty": v[0],
						"rate": v[1],
						"amount": int(v[0]) * flt(v[1]),
						"against_sales_order": v[3],
						"is_approved": v[4],
						"remarks": v[5]
					})
			sa.total_amount = total_amt
			sa.flags.ignore_permissions = True
			sa.save()
			frappe.db.commit()
			return sa.name
	except Exception as e:
		print("#####################################", str(e))
		frappe.msgprint(_("Something went wrong while creating/updating Stock Allocation"))


@frappe.whitelist()
def submit_stock_allocation(data):
	try:
		if data:
			sa = save_stock_allocation(data)
			sa = frappe.get_doc("Stock Allocation", sa)
			sa.flags.ignore_permissions = True
			sa.submit()

			# deliver note
			is_exist = frappe.db.get_value("Delivery Note", {
				"stock_allocation": sa.name
			})
			if is_exist:
				dn = frappe.get_doc("Delivery Note", is_exist)
			else:
				dn = frappe.new_doc("Delivery Note")
				dn.customer = sa.customer
				dn.stock_allocation = sa.name

			# warehouse
			warehouse = frappe.db.get_singles_value("MedTech Settings", "rm_warehouse")

			for row in sa.items:
				data = row.as_dict()
				so = data.get("against_sales_order")
				soi_ref = frappe.db.get_value("Sales Order Item", {
					"parent": so,
					"item_code": data.get("item_code")
				})
				so_rate = frappe.db.get_value("Sales Order Item",{"parent":so,"item_code":data.get("item_code")},'rate')
		
				row_data = {
					"item_code": data.get("item_code"),
					"item_name": data.get("item_name"),
					"qty": data.get("qty"),
					"rate": so_rate,
					"amount": data.get("amount"),
					"description": data.get("remarks") or  data.get("item_code"),
					"against_sales_order": so,
					"so_detail": soi_ref or ""
				}
				if warehouse:
					row_data["warehouse"] = warehouse
				dn.append("items", row_data)
			dn.flags.ignore_permissions = True
			dn.is_allocated = True
			dn.set_missing_values()
			dn.save()
			# dn.submit()
			return {"stock_allocation": sa.name, "delivery_note": dn.name}
	except Exception as e:
		print("################################", str(e))
		frappe.msgprint(_("Something went wrong, while submitting the document"))

@frappe.whitelist()		
def get_ohs_qty():
	# warehouse list
	fg_warehouse = frappe.db.sql("select warehouse from `tabFG Warehouse Group`", as_dict = 1)
	from_warehouses = []

	if fg_warehouse:
		# fg_warehouse_ll = ["'" + row.warehouse + "'" for row in fg_warehouse]
		# fg_warehouse_list = ','.join(fg_warehouse_ll)
		for row in fg_warehouse:
			warehouse_list = frappe.db.get_descendants('Warehouse', row.warehouse)
			if warehouse_list:
				for item in warehouse_list:
					from_warehouses.append(item)
			else:
				from_warehouses.append(row.warehouse)
		fg_warehouse_ll = ["'" + row + "'" for row in from_warehouses]
		fg_warehouse_list = ','.join(fg_warehouse_ll)
	else:
	    fg_warehouse_list = "' '"

	ohs_query = frappe.db.sql("SELECT item.item_code, sum(IFNULL (bin.actual_qty,0.0)) as ohs from `tabItem` item LEFT JOIN `tabBin` bin on item.item_code = bin.item_code  and item.disabled = 0 and bin.warehouse in ({0}) group by item.item_code".format(fg_warehouse_list), as_dict=1)
	ohs_detail = {row.item_code : row.ohs for row in ohs_query}
	return ohs_detail
