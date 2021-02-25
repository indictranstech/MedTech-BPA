from __future__ import unicode_literals
from frappe.model.document import Document
import frappe
from frappe.utils import flt,today
from frappe import _


def after_insert(doc, method):
	get_warehouse = frappe.get_single('MedTech Settings')
	supplier = frappe.db.get_value('Purchase Receipt', doc.purchase_receipt, 'supplier')
	qc_disable_items = get_qc_disable_items(supplier)
	if doc.stock_entry_type == 'Material Transfer':
		if doc.items:
			for item in doc.items:
				if item.item_code not in qc_disable_items and item.t_warehouse == get_warehouse.rm_warehouse and  item.s_warehouse == get_warehouse.qc_warehouse:
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
	if doc.stock_entry_type == 'Material Transfer':
		if doc.items:
			for item in doc.items:
				if item.t_warehouse == get_warehouse.rm_warehouse and  item.s_warehouse == get_warehouse.qc_warehouse and item.quality_inspection:
					frappe.db.sql("Update `tabPurchase Receipt Item` set quality_inspection = '{0}' where parent = '{1}' and item_code = '{2}'".format(item.quality_inspection, doc.purchase_receipt, item.item_code))
					frappe.db.commit()
