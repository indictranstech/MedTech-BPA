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
	from_warehouses = None
	if wip_warehouse:
		from_warehouses = frappe.db.get_descendants('Warehouse', wip_warehouse)
		
	if not from_warehouses:
		from_warehouses = [wip_warehouse]

	if len(from_warehouses) == 1:
		stock_qty = frappe.db.sql("SELECT item.item_code, sum(IFNULL (bin.actual_qty,0.0)) as ohs from `tabItem` item LEFT JOIN `tabBin` bin on item.item_code = bin.item_code  and item.disabled = 0 and bin.warehouse = '{0}' group by item.item_code".format(from_warehouses[0]), as_dict=1,debug=1)
	else:
		stock_qty = frappe.db.sql("SELECT item.item_code, sum(IFNULL (bin.actual_qty,0.0)) as ohs from `tabItem` item LEFT JOIN `tabBin` bin on item.item_code = bin.item_code  and item.disabled = 0 and bin.warehouse in {0} group by item.item_code".format(tuple(from_warehouses)), as_dict=1,debug=1)
	stock_dict = {row.item_code : row.ohs for row in stock_qty}
	return stock_dict
