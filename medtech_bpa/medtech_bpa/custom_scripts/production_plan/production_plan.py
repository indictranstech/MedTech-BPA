from __future__ import unicode_literals
from frappe.model.document import Document
import frappe
from frappe.utils import nowdate,nowtime, today
from erpnext.manufacturing.doctype.production_plan.production_plan import ProductionPlan

def validate(doc,method):
	items = [item.item_code for item in doc.mr_items]
	stock_qty_in_material_issue_warehouse = get_stock_balance(items,doc.posting_date,doc.for_warehouse)
	stock_qty_in_wip_warehouse = get_stock_balance(items,doc.posting_date,doc.wip_warehouse)
	for item in doc.mr_items:
		if item.item_code in stock_qty_in_material_issue_warehouse:
			item.qty_in_material_issue_warehouse = stock_qty_in_material_issue_warehouse.get(item.item_code)
		if item.item_code in stock_qty_in_wip_warehouse:
			item.qty_in_wip_warehouse = stock_qty_in_wip_warehouse.get(item.item_code)
		item.quantity_to_be_issued = (item.quantity - item.qty_in_wip_warehouse)
		item.shortage_or_excess_quantity = (item.qty_in_material_issue_warehouse - item.quantity_to_be_issued)

def on_submit(doc,method):
	# Create work order in backend
	ProductionPlan.make_work_order(doc)
	wo_list = frappe.get_list("Work Order", filters={"production_plan":doc.name,"docstatus": ("<", "1")})
	for item in wo_list:
		work_order_doc = frappe.get_doc("Work Order",item)
		work_order_doc.flags.ignore_permissions = 1
		work_order_doc.submit()
	
def get_stock_balance(item_set,date,wip_warehouse):
	"""Returns stock balance quantity at given warehouse on given posting date or current date.
	If `with_valuation_rate` is True, will return tuple (qty, rate)"""
	if len(item_set) == 0:
		frappe.throw("Please select item".format(date))
	elif len(item_set) == 1:
		stock_qty = frappe.db.sql(""" SELECT b.item_code, b.actual_qty,b.stock_uom from `tabBin` b where b.item_code = '{0}' and b.actual_qty > 0 order by b.modified asc """.format(item_set[0]), as_dict = 1)
	else:
		stock_qty = frappe.db.sql(""" SELECT b.item_code, b.actual_qty,b.stock_uom from `tabBin` b where b.item_code in {0} and b.actual_qty > 0 order by b.modified asc """.format(tuple(item_set)), as_dict = 1)
	from erpnext.stock.stock_ledger import get_previous_sle
	stock_dict = {}
	posting_time = nowtime()
	for item in item_set:
		last_entry = get_previous_sle({
			"item_code": item,
			"warehouse" : wip_warehouse,
			"posting_date": date,
			"posting_time": posting_time })
		total_qty = last_entry.qty_after_transaction if last_entry else 0.0
		stock_dict[item] = total_qty
	return stock_dict
