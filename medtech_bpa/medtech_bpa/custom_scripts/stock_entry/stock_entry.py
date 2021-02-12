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


def get_qc_disable_items(supplier):
	query = '''SELECT qd.item_code  from `tabQC Disable Supplier` qds join `tabQC Disable` qd 
		on qds.parent = qd.name  where qds.supplier = '{0}' '''.format(supplier)
	qc_disable_items = frappe.db.sql(query, as_dict=1)
	qc_disable_items = [ item.get('item_code') for item in qc_disable_items]
	return qc_disable_items