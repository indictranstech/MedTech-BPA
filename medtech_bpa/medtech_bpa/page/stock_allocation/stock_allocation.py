import frappe
from frappe.utils import flt, today
import json

@frappe.whitelist()
def get_pending_so(**kwargs):
	data = {"items": [], "customer": "", "pending_bal": 0, "closing_bal": 0}
	customer = ''
	if kwargs.get("stock_allocation_party"):
		customer = kwargs.get("stock_allocation_party")
		query = """
			select
				so.name, so.customer, so.status, 
				so.transaction_date, soi.item_code, soi.qty, soi.rate, 
				soi.amount
			from
				`tabSales Order` so
			left join
				`tabSales Order Item` soi
			on
				so.name = soi.parent where so.customer = '{}'
			and so.delivery_status = 'Not Delivered'""".format(customer)
		so_data = frappe.db.sql(query, as_dict=True)

		data["items"] = so_data
		data["customer"] = customer
		data["pending_bal"] = 249000
		data["closing_bal"] = 1000
	return data

@frappe.whitelist()
def save_stock_allocation(data)	:
	if data:
		data = json.loads(data)
		sa = frappe.new_doc("Stock Allocation")
		sa.customer = data.get("customer")
		sa.posting_date = today()

		for k, v in data.get("items", {}).items():
			sa.append("items", {
				"item_code": k,
				"qty": v[0],
				"rate": v[1],
				"amount": int(v[0]) * flt(v[1]),
				"against_sales_order": v[2],
				"remarks": v[4]
			})
		sa.flags.ignore_permissions = True
		sa.save()
		frappe.db.commit()
		return "Success"
