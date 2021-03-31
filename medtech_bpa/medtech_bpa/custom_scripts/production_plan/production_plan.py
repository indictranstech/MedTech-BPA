from __future__ import unicode_literals
from frappe.model.document import Document
import frappe
from frappe.utils import nowdate,nowtime, today
from erpnext.manufacturing.doctype.production_plan.production_plan import ProductionPlan

def validate(doc,method):
	items = [item.item_code for item in doc.mr_items]
	mr_warehouse_list = [item.warehouse for item in doc.material_request_warehouses]
	mr_warehouse_list.append(doc.for_warehouse)
	wip_warehouse_list = [item.warehouse for item in doc.wip_warehouses_production_plan]
	wip_warehouse_list.append(doc.wip_warehouse)
	stock_qty_in_material_issue_warehouse = get_stock_balance(items,doc.posting_date,mr_warehouse_list)
	stock_qty_in_wip_warehouse = get_stock_balance(items,doc.posting_date,wip_warehouse_list)
	for item in doc.mr_items:
		if item.item_code in stock_qty_in_material_issue_warehouse:
			item.qty_in_material_issue_warehouse = stock_qty_in_material_issue_warehouse.get(item.item_code)
		if item.item_code in stock_qty_in_wip_warehouse:
			item.qty_in_wip_warehouse = stock_qty_in_wip_warehouse.get(item.item_code)
		item.quantity_to_be_issued = (item.quantity - item.qty_in_wip_warehouse) if (item.quantity - item.qty_in_wip_warehouse) > 0 else 0
		item.shortage_or_excess_quantity = (item.qty_in_material_issue_warehouse - item.quantity_to_be_issued)

def on_submit(doc,method):
	# Create work order in backend
	ProductionPlan.make_work_order(doc)
	wo_list = frappe.get_list("Work Order", filters={"production_plan":doc.name,"docstatus": ("<", "1")})
	for item in wo_list:
		work_order_doc = frappe.get_doc("Work Order",item)
		work_order_doc.flags.ignore_permissions = 1
		work_order_doc.submit()
	doc.reload()
	
def get_stock_balance(item_set,date,wip_warehouse):
	from_warehouses = []
	if wip_warehouse:
		for row in wip_warehouse:
			warehouse_list = frappe.db.get_descendants('Warehouse', row)
			if warehouse_list:
				for item in warehouse_list:
					from_warehouses.append(item)
			else:
				from_warehouses.append(row)
	# if not from_warehouses:
	# 	from_warehouses = [wip_warehouse]

	if len(from_warehouses) == 1:
		stock_qty = frappe.db.sql("SELECT item.item_code, sum(IFNULL (bin.actual_qty,0.0)) as ohs from `tabItem` item LEFT JOIN `tabBin` bin on item.item_code = bin.item_code  and item.disabled = 0 and bin.warehouse = '{0}' group by item.item_code".format(from_warehouses[0]), as_dict=1,debug=1)
	else:
		stock_qty = frappe.db.sql("SELECT item.item_code, sum(IFNULL (bin.actual_qty,0.0)) as ohs from `tabItem` item LEFT JOIN `tabBin` bin on item.item_code = bin.item_code  and item.disabled = 0 and bin.warehouse in {0} group by item.item_code".format(tuple(from_warehouses)), as_dict=1,debug=1)
	stock_dict = {row.item_code : row.ohs for row in stock_qty}
	return stock_dict


