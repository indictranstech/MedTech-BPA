# -*- coding: utf-8 -*-
# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from six import iteritems
from frappe.model.document import Document
from frappe import _
from collections import OrderedDict
from frappe.utils import floor, flt, today, cint
from frappe.model.mapper import get_mapped_doc, map_child_doc
from erpnext.stock.get_item_details import get_conversion_factor
from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note as create_delivery_note_from_sales_order

class ProductionPickList(Document):
	def before_save(self):
		work_order_doc = frappe.get_doc("Work Order",self.work_order)
		prod_pick_list = frappe.get_all("Production Pick List",'name')
		production_pick_list = [item.name for item in prod_pick_list]
		for item in self.locations:
			if item.picked_qty > 0 :
				stock_entry = frappe.new_doc("Stock Entry")
				if stock_entry:
					stock_entry.stock_entry_type = 'Material Transfer for Manufacture'
					stock_entry.company = self.company
					stock_entry.work_order = self.work_order
					stock_entry.production_pick_list = self.name if self.name in production_pick_list else None
					stock_entry.from_warehouse = item.warehouse
					stock_entry.to_warehouse = work_order_doc.wip_warehouse
					stock_entry.append("items",{
							"item_code": item.item_code,
								"qty": item.picked_qty,
								"s_warehouse": item.warehouse,
								"t_warehouse": work_order_doc.wip_warehouse
						})
					stock_entry.save()
					stock_entry.submit()
					actual_balance = frappe.db.get_value("Work Order Item",{'parent':self.work_order,'item_code':item.item_code
						},'transferred_qty')
					item.check_balance = (item.check_balance + item.picked_qty)
					item.balance_qty = flt(item.qty - actual_balance) if flt(item.qty - actual_balance) > 0 else 0
					item.picked_qty = 0
					actual_stock = get_available_item_locations_for_other_item(item.item_code,item.warehouse,item.qty,self.company)
					item.stock_qty = actual_stock[0].get("qty")
		# recalculate balance qty according to total transferred for all items
		for item in self.locations:
			actual_balance = frappe.db.get_value("Work Order Item",{'parent':self.work_order,'item_code':item.item_code
						},'transferred_qty')
			item.balance_qty = item.qty - actual_balance

	
	def set_item_locations(self, save=False):
		items = self.aggregate_item_qty()
		self.item_location_map = frappe._dict()

		from_warehouses = None
		if self.parent_warehouse:
			from_warehouses = frappe.db.get_descendants('Warehouse', self.parent_warehouse)

		if not from_warehouses:
			from_warehouses = self.parent_warehouse
		
		# Create replica before resetting, to handle empty table on update after submit.
		locations_replica  = self.get('locations')

		# reset
		self.delete_key('locations')
		for item_doc in items:
			item_code = item_doc.item_code

			self.item_location_map.setdefault(item_code,
				get_available_item_locations(item_code, from_warehouses, self.item_count_map.get(item_code), self.company))

			locations = get_items_with_location_and_quantity(item_doc, self.item_location_map, self.docstatus)

			item_doc.idx = None
			item_doc.name = None

			for row in locations:
				location = item_doc.as_dict()
				qty_to_be_issued = frappe.db.get_value("Work Order Item",{'parent':self.work_order,'item_code':location.get("item_code")},'qty_to_be_issued')
				bom = frappe.db.get_value("Work Order",{'name':self.work_order},'bom_no')
				uom = frappe.db.get_value("BOM Item",{'parent':bom,'item_code':location.get("item_code")},'uom')
				stock_uom = frappe.db.get_value("BOM Item",{'parent':bom,'item_code':location.get("item_code")},'stock_uom')
				# uom_explod = frappe.db.get_value("BOM Explosion Item",{'name':bom,'item_code':location.get("item_code")},'uom')
				stock_uom_explod = frappe.db.get_value("BOM Explosion Item",{'parent':bom,'item_code':location.get("item_code")},'stock_uom')
				# uom = frappe.db.get_value("Item",{'name':location.get("item_code")},'stock_uom')
				row.update({
					'qty': qty_to_be_issued,
					'balance_qty':qty_to_be_issued,
					'uom' : uom if uom else stock_uom_explod,
					'stock_uom' : stock_uom if stock_uom else stock_uom_explod

				})
				location.update(row)
				self.append('locations', location)

		# If table is empty on update after submit, set stock_qty, picked_qty to 0 so that indicator is red
		# and give feedback to the user. This is to avoid empty Pick Lists.
		if not self.get('locations') and self.docstatus == 1:
			for location in locations_replica:
				location.stock_qty = 0
				location.picked_qty = 0
				self.append('locations', location)
			frappe.msgprint(_("Please Restock Items and Update the Pick List to continue. To discontinue, cancel the Pick List."),
				 title=_("Out of Stock"), indicator="red")

		if save:
			self.save()

	def aggregate_item_qty(self):
		locations = self.get('locations')
		self.item_count_map = {}
		# aggregate qty for same item
		item_map = OrderedDict()
		for item in locations:
			if not item.item_code:
				frappe.throw("Row #{0}: Item Code is Mandatory".format(item.idx))
			item_code = item.item_code
			reference = item.sales_order_item or item.material_request_item
			key = (item_code, item.uom, reference)

			item.idx = None
			item.name = None

			if item_map.get(key):
				item_map[key].qty += item.qty
				item_map[key].stock_qty += item.stock_qty
			else:
				item_map[key] = item

			# maintain count of each item (useful to limit get query)
			self.item_count_map.setdefault(item_code, 0)
			# self.item_count_map[item_code] += item.stock_qty

		return item_map.values()


def validate_item_locations(pick_list):
	if not pick_list.locations:
		frappe.throw(_("Add items in the Item Locations table"))

def get_items_with_location_and_quantity(item_doc, item_location_map, docstatus):
	available_locations = item_location_map.get(item_doc.item_code)
	locations = []

	# if stock qty is zero on submitted entry, show positive remaining qty to recalculate in case of restock.
	remaining_stock_qty = item_doc.qty 
	# if (docstatus == 1 and item_doc.stock_qty == 0) else item_doc.stock_qty

	while remaining_stock_qty > 0 and available_locations:
		item_location = available_locations.pop(0)
		item_location = frappe._dict(item_location)

		stock_qty = remaining_stock_qty 
		# if item_location.qty >= remaining_stock_qty else item_location.qty
		# qty = stock_qty / (item_doc.conversion_factor or 1)

		uom_must_be_whole_number = frappe.db.get_value('UOM', item_doc.uom, 'must_be_whole_number')
		# if uom_must_be_whole_number:
		# 	# qty = floor(qty)
		# 	# stock_qty = qty * item_doc.conversion_factor
		# 	if not stock_qty: break

		serial_nos = None
		if item_location.serial_no:
			serial_nos = '\n'.join(item_location.serial_no[0: cint(stock_qty)])

		locations.append(frappe._dict({
			'stock_qty': item_location.qty,
			'warehouse': item_location.warehouse
		}))

		# remaining_stock_qty -= stock_qty

		# qty_diff = item_location.qty - stock_qty
		# if extra quantity is available push current warehouse to available locations
		# if qty_diff > 0:
		# 	item_location.qty = qty_diff
		# 	if item_location.serial_no:
		# 		# set remaining serial numbers
		# 		item_location.serial_no = item_location.serial_no[-int(qty_diff):]
		# 	available_locations = [item_location] + available_locations

	# update available locations for the item
	item_location_map[item_doc.item_code] = available_locations
	return locations

def get_available_item_locations(item_code, from_warehouses, required_qty, company, ignore_validation=False):
	locations = []
	locations = get_available_item_locations_for_other_item(item_code, from_warehouses, required_qty, company)

	total_qty_available = sum(location.get('qty') for location in locations)

	remaining_qty = required_qty - total_qty_available

	if remaining_qty > 0 and not ignore_validation:
		frappe.msgprint(_('{0} units of Item {1} is not available.')
			.format(remaining_qty, frappe.get_desk_link('Item', item_code)),
			title=_("Insufficient Stock"))

	return locations

def get_available_item_locations_for_other_item(item_code, from_warehouses, required_qty, company):
	# gets all items available in different warehouses
	wip_warehouse = frappe.db.get_single_value("Manufacturing Settings", 'default_wip_warehouse')
	warehouses = [x.get('name') for x in frappe.get_list("Warehouse", {'company': company}, "name")]
	if wip_warehouse in warehouses:
		warehouses.remove(wip_warehouse)
	
	filters = frappe._dict({
		'item_code': item_code,
		'warehouse': ['in', warehouses],
		'actual_qty': ['>=', 0]
	})

	if from_warehouses:
		if wip_warehouse in from_warehouses:
			from_warehouses.remove(wip_warehouse)
		filters.warehouse = ['in', from_warehouses]

	item_locations = frappe.get_all('Bin',
		fields=['warehouse', 'actual_qty as qty'],
		filters=filters,
		# limit=required_qty,
		order_by='creation')

	return item_locations

@frappe.whitelist()
def get_pending_work_orders(doctype, txt, searchfield, start, page_length, filters, as_dict):
	return frappe.db.sql("""
		SELECT
			`name`, `company`, `planned_start_date`
		FROM
			`tabWork Order`
		WHERE
			`status` not in ('Completed', 'Stopped')
			AND `qty` > `material_transferred_for_manufacturing`
			AND `docstatus` = 1
			AND `company` = %(company)s
			AND `name` like %(txt)s
		ORDER BY
			if(locate(%(_txt)s, name), locate(%(_txt)s, name), 99999), name
		LIMIT
			%(start)s, %(page_length)s""",
		{
			'txt': "%%%s%%" % txt,
			'_txt': txt.replace('%', ''),
			'start': start,
			'page_length': frappe.utils.cint(page_length),
			'company': filters.get('company')
		}, as_dict=as_dict)

@frappe.whitelist()
def get_item_details(item_code, uom=None):
	details = frappe.db.get_value('Item', item_code, ['stock_uom', 'name'], as_dict=1)
	details.uom = uom or details.stock_uom
	if uom:
		details.update(get_conversion_factor(item_code, uom))

	return details
@frappe.whitelist()
def create_pick_list(source_name, target_doc=None, for_qty=None):
	for_qty = for_qty or json.loads(target_doc).get('for_qty')
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
			target.qty = qty
			target.stock_qty = qty
			target.uom = frappe.get_value('Item', source.item_code, 'stock_uom')
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
			'postprocess': update_item_quantity,
			'condition': lambda doc: abs(doc.transferred_qty) < abs(doc.required_qty)
		},
	}, target_doc)

	doc.for_qty = for_qty

	doc.set_item_locations()

	return doc
@frappe.whitelist()
def get_work_orders(production_plan,item):
	work_order = frappe.db.get_value("Work Order",{'production_plan':production_plan,'production_item':item},'name')
	return work_order
@frappe.whitelist()
def get_items_from_production_plan(production_plan):
	items = frappe.get_list("Production Plan Item",{'parent':production_plan},'item_code')
	item_list = [item.item_code for item in items]
	rm_warehouse = frappe.db.get_value("Production Plan",{'name':production_plan},'for_warehouse')
	return item_list,rm_warehouse

@frappe.whitelist()
def get_pending_work_orders(doctype, txt, searchfield, start, page_length, filters, as_dict):

	return frappe.db.sql("""
		SELECT
			`name`, `company`, `planned_start_date` , `production_plan` , `production_item`
		FROM
			`tabWork Order`
		WHERE
			`status` not in ('Completed', 'Stopped')
			AND `qty` > `material_transferred_for_manufacturing`
			AND `docstatus` = 1
			AND `company` = %(company)s
			AND `production_plan` = %(production_plan)s
			AND `production_item` = %(production_item)s
			AND `name` like %(txt)s
		ORDER BY
			if(locate(%(_txt)s, name), locate(%(_txt)s, name), 99999), name
		LIMIT
			%(start)s, %(page_length)s""",
		{
			'txt': "%%%s%%" % txt,
			'_txt': txt.replace('%', ''),
			'start': start,
			'page_length': frappe.utils.cint(page_length),
			'company': filters.get('company'),
			'production_plan':filters.get('production_plan'),
			'production_item':filters.get('production_item')
		}, as_dict=as_dict)