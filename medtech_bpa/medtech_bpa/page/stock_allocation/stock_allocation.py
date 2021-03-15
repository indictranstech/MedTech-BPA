import json
import frappe
from frappe import _
from frappe.utils import flt, today, add_days
from erpnext.accounts.report.general_ledger.general_ledger import execute

@frappe.whitelist()
def get_pending_so(**kwargs):
	try:
		data = {"items": [], "customer": "", "pending_bal": 0, "closing_bal": 0}
		customer = ''

		if kwargs.get("stock_allocation_party"):

			customer = kwargs.get("stock_allocation_party")

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

			for row in gl_data[1]:
				if row.get("voucher_no") == kwargs.get("payment_entry"):
					closing_bal = row.get("balance")

			query = """
				select
					so.name, so.customer, so.status, 
					so.transaction_date, soi.item_code, soi.item_name,
					(soi.qty - soi.delivered_qty) as qty, soi.rate, soi.amount,
					b.actual_qty as stock_qty
				from
					`tabSales Order` so
				left join
					`tabSales Order Item` soi
				on
					so.name = soi.parent
				left join
					`tabBin` b
				on soi.item_code = b.item_code and soi.warehouse = b.warehouse
				where
					so.customer = '{}'
					and so.delivery_status in ('Not Delivered', 'Partly Delivered')
					and so.docstatus = 1""".format(customer)
			so_data = frappe.db.sql(query, as_dict=True)

			data["items"] = so_data
			data["customer"] = customer
			data["pending_bal"] = closing_bal * -1
			data["closing_bal"] = closing_bal
			data["ledger_bal"] = ledger_bal
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

			for k, v in data.get("items", {}).items():
				if v[3]:
					sa.append("items", {
						"item_code": k,
						"qty": v[0],
						"rate": v[1],
						"amount": int(v[0]) * flt(v[1]),
						"against_sales_order": v[2],
						"is_approved": v[3],
						"remarks": v[4]
					})
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
			dn = frappe.new_doc("Delivery Note")
			dn.customer = sa.customer

			for row in sa.items:
				data = row.as_dict()
				dn.append("items", {
					"item_code": data.get("item_code"),
					"item_name": data.get("item_name"),
					"qty": data.get("qty"),
					"rate": data.get("rate"),
					"amount": data.get("amount"),
					"description": data.get("remarks") or  data.get("item_code"),
					"against_sales_order": data.get("against_sales_order"),
				})
			dn.flags.ignore_permissions = True
			dn.save()
			dn.submit()
			return dn.name
	except Exception as e:
		print("################################", str(e))
		frappe.msgprint(_("Something went wrong, while submitting the document"))