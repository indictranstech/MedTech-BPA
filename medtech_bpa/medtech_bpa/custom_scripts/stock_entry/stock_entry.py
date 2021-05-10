from __future__ import unicode_literals
from frappe.model.document import Document
import frappe
from frappe.utils import flt,today
from frappe import _


def after_insert(doc, method):
	get_warehouse = frappe.get_single('MedTech Settings')
	rm_warehouse_list = [item.warehouse for item in get_warehouse.rm_warehouse_list]
	rm_child_warehouse_list = []
	for warehouse in rm_warehouse_list:
		child_warehouse = frappe.db.get_descendants('Warehouse', warehouse)
		if child_warehouse:
			for row in child_warehouse:
				rm_child_warehouse_list.append(row)
		else:
			rm_child_warehouse_list.append(warehouse)
	qc_warehouse_list = [item.warehouse for item in get_warehouse.qc_warehouse_list]
	qc_child_warehouse_list = []
	for warehouse in qc_warehouse_list:
		child_warehouse = frappe.db.get_descendants('Warehouse', warehouse)
		if child_warehouse:
			for row in child_warehouse:
				qc_child_warehouse_list.append(row)
		else:
			qc_child_warehouse_list.append(warehouse)
	supplier = frappe.db.get_value('Purchase Receipt', doc.purchase_receipt, 'supplier')
	qc_disable_items = get_qc_disable_items(supplier)
	if doc.stock_entry_type == 'Material Transfer':
		if doc.items:
			for item in doc.items:
				if item.item_code not in qc_disable_items and item.t_warehouse in rm_child_warehouse_list and  item.s_warehouse in qc_child_warehouse_list:
						doc.inspection_required = 1


def on_submit(doc, method):
	update_qc_reference_on_vir(doc)


def get_qc_disable_items(supplier):
	query = '''SELECT qd.item_code  from `tabQC Disable Supplier` qds join `tabQC Disable` qd 
		on qds.parent = qd.name  where qds.supplier = '{0}' '''.format(supplier)
	qc_disable_items = frappe.db.sql(query, as_dict=1)
	qc_disable_items = [ item.get('item_code') for item in qc_disable_items]
	return qc_disable_items

@frappe.whitelist()
def get_work_orders(production_plan,item):
	work_order = frappe.db.get_value("Work Order",{'production_plan':production_plan,'production_item':item},'name')
	return work_order

@frappe.whitelist()
def get_items_from_production_plan(production_plan):
	items = frappe.get_list("Production Plan Item",{'parent':production_plan},'item_code')
	item_list = [item.item_code for item in items]
	return item_list


def update_qc_reference_on_vir(doc):
	get_warehouse = frappe.get_single('MedTech Settings')
	rm_warehouse_list = [item.warehouse for item in get_warehouse.rm_warehouse_list]
	rm_child_warehouse_list = []
	for warehouse in rm_warehouse_list:
		child_warehouse = frappe.db.get_descendants('Warehouse', warehouse)
		if child_warehouse:
			for row in child_warehouse:
				rm_child_warehouse_list.append(row)
		else:
			rm_child_warehouse_list.append(warehouse)
	qc_warehouse_list = [item.warehouse for item in get_warehouse.qc_warehouse_list]
	qc_child_warehouse_list = []
	for warehouse in qc_warehouse_list:
		child_warehouse = frappe.db.get_descendants('Warehouse', warehouse)
		if child_warehouse:
			for row in child_warehouse:
				qc_child_warehouse_list.append(row)
		else:
			qc_child_warehouse_list.append(warehouse)
	if doc.stock_entry_type == 'Material Transfer':
		if doc.items:
			for item in doc.items:
				if item.t_warehouse in rm_child_warehouse_list and  item.s_warehouse in qc_child_warehouse_list and item.quality_inspection:
					rejected_qty = frappe.db.get_value('Quality Inspection', {'name' : item.quality_inspection}, 'rejected_quantity') or 0

					if rejected_qty > 0:
						# create mr for rejected warehouse
						current_date = frappe.utils.today()
						stock_entry = frappe.new_doc("Stock Entry")
						if stock_entry:
							stock_entry.posting_date = current_date
							stock_entry.stock_entry_type = "Rejected Material Transfer"
							stock_entry.purchase_receipt = doc.purchase_receipt
							stock_entry.append("items",{
								'item_code': item.get('item_code'),
								'item_name': item.get('item_name'),
								'item_group':item.get('item_group'),
								'description': item.get('description'),
								'uom': item.get('uom'),
								'qty': rejected_qty,
								's_warehouse': item.t_warehouse,
								't_warehouse': get_warehouse.rejected_warehouse,
								'basic_rate' : item.get('rate')
							})
							stock_entry.save(ignore_permissions = True)
							stock_entry.submit()
							frappe.db.commit()	

					frappe.db.sql("Update `tabPurchase Receipt Item` set quality_inspection = '{0}', custom_rejected_qty = '{1}' where parent = '{2}' and item_code = '{3}'".format(item.quality_inspection, rejected_qty, doc.purchase_receipt, item.item_code))
					frappe.db.commit()