from __future__ import unicode_literals
from frappe.model.document import Document
import frappe
from frappe.utils import nowdate
import json
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt, get_datetime, getdate, date_diff, cint, nowdate, get_link_to_form, time_diff_in_hours

def on_submit(doc,method):
	production_plan_doc = frappe.get_doc("Production Plan",doc.production_plan)
	for row in production_plan_doc.mr_items:
		for item in doc.required_items:
			if item.item_code == row.item_code:
				actual_qty = get_available_item_qty_in_wip(item.item_code,doc.wip_warehouse,doc.company)
				qty_to_be_issued = (item.required_qty - row.qty_in_wip_warehouse) if (item.required_qty - row.qty_in_wip_warehouse) > 0 else 0
				frappe.db.set_value("Work Order Item",{'parent':doc.name,'item_code':item.item_code},'qty_to_be_issued',qty_to_be_issued)
				frappe.db.commit()
				# if len(actual_qty) > 0:
				# 	item.qty_to_be_issued = item.required_qty - actual_qty[0].get("qty")
				# else:
				# 	item.qty_to_be_issued = item.required_qty
	# doc.save()
	# doc.submit()
@frappe.whitelist()
def create_pick_list(source_name, target_doc=None, for_qty=None):
	# for_qty = for_qty or json.loads(target_doc).get('for_qty')
	for_qty = frappe.db.get_value("Work Order",source_name,'qty')
	max_finished_goods_qty = frappe.db.get_value('Work Order', source_name, 'qty')
	def update_item_quantity(source, target, source_parent):
		pending_to_issue = flt(source.required_qty) - flt(source.transferred_qty)
		desire_to_transfer = flt(source.required_qty) / max_finished_goods_qty * flt(for_qty)

		qty = 0
		if desire_to_transfer <= pending_to_issue:
			qty = desire_to_transfer
		elif pending_to_issue > 0:
			qty = pending_to_issue

		if qty:
			target.stock_uom = target.uom
			target.conversion_factor = 1
		else:
			target.delete()

	doc = get_mapped_doc('Work Order', source_name, {
		'Work Order': {
			'doctype': 'Production Pick List',
			'validation': {
				'docstatus': ['=', 1]
			}
		},
		'Work Order Item': {
			'doctype': 'Production Pick List Item',
			"field_map" : {
				"item_code" : "item_code",
				"uom":"uom",
				# "qty_to_be_issued":"qty"
			},
			'postprocess': update_item_quantity,
			'condition': lambda doc: abs(doc.transferred_qty) < abs(doc.required_qty)
		},
	}, target_doc)

	doc.for_qty = for_qty

	doc.set_item_locations()

	return doc
def get_available_item_qty_in_wip(item_code, warehouse, company):
	# gets all items available in different warehouses
	warehouses = [x.get('name') for x in frappe.get_list("Warehouse", {'company': company}, "name")]

	filters = frappe._dict({
		'item_code': item_code,
		'warehouse': ['=', warehouse],
		'actual_qty': ['>=', 0]
	})

	item_locations = frappe.get_all('Bin',
		fields=['warehouse', 'actual_qty as qty'],
		filters=filters,
		# limit=required_qty,
		order_by='creation')

	return item_locations