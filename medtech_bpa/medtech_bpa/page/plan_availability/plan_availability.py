from __future__ import unicode_literals
import frappe

from frappe.model.document import Document
from frappe.utils import nowdate, cstr, flt, cint, now, getdate,get_datetime,time_diff_in_seconds,add_to_date,time_diff_in_seconds,add_days,today
from datetime import datetime,date, timedelta
from frappe.model.naming import make_autoname
import time
import json
import pandas as pd
from frappe import _
from erpnext.manufacturing.doctype.bom.bom import get_bom_items_as_dict
@frappe.whitelist()
def get_planning_master_data(filters=None):
	filters = json.loads(filters)
	data = {}
	date_data = frappe.db.sql(""" SELECT DISTINCT a.date from `tabPlanning Master Item` a join `tabPlanning Master` b on a.planning_master_parent = b.name  where a.planning_master_parent= '{0}' group by a.date order by a.date""".format(filters.get("planning_master")), as_dict=1)
	data.update({'date_data':date_data})
	date_data_with_amount = frappe.db.sql(""" SELECT a.item_code, a.date, a.amount from `tabPlanning Master Item` a join `tabPlanning Master` b on a.planning_master_parent = b.name  where a.planning_master_parent= '{0}' """.format(filters.get("planning_master")), as_dict=1)
	data.update({'date_data_with_amount':date_data_with_amount})
	planning_data = frappe.db.sql(""" SELECT DISTINCT a.item_code,a.item_name, a.uom, sum(a.amount) as amount ,a.bom from `tabPlanning Master Item` a join `tabPlanning Master` b on a.planning_master_parent = b.name  where a.planning_master_parent= '{0}' group by a.item_code """.format(filters.get("planning_master")), as_dict=1)
	company = frappe.db.get_single_value("Global Defaults",'default_company')
	fg_warehouse = frappe.db.sql("SELECT warehouse from `tabFG Warehouse Group`", as_dict = 1)
	fg_warehouse_list = tuple([item.warehouse for item in fg_warehouse])
	for row in date_data_with_amount:
		for item in planning_data:
			if row.item_code == item.item_code:
				item.update({row.date:row.amount})
	for row in planning_data:
		bom_data = frappe.db.sql("""SELECT b.item_code,b.stock_uom,b.stock_qty  from `tabBOM` a join `tabBOM Explosion Item` b on b.parent = a.name where a.name = '{0}'""".format(row.get('bom')),as_dict=1)
		reqd_qty_data = []
		for col in date_data_with_amount:
			if col.item_code == row.item_code:
				raw_materials = get_bom_items_as_dict(row.get('bom'),company,col.get("amount"))
				for item in bom_data:
					if item.item_code in raw_materials:
						
						current_stock = frappe.db.sql("""SELECT item_code,sum(actual_qty) as qty from `tabBin` where item_code = '{0}' and warehouse in {1}""".format(item.item_code,fg_warehouse_list),as_dict=1)
						stock_expected = frappe.db.sql("""SELECT i.item_code,sum((i.qty-i.received_qty)) as qty from `tabPurchase Order Item` i join `tabPurchase Order` p on p.name = i.parent where i.item_code = '{0}' and p.schedule_date = '{1}' """.format(item.item_code,col.date),as_dict=1)
						virtual_stock = flt(current_stock[0].get('qty')) + flt(stock_expected[0].get("qty")) if stock_expected else 0 
						actual_qty_req = flt(flt(virtual_stock) - flt(raw_materials.get(item.item_code).qty),3)
						item.update({col.date:flt(actual_qty_req if actual_qty_req < 0 else raw_materials.get(item.item_code).qty) })
		row.update({'bom_data':bom_data})

	data.update({'planning_data':planning_data})
	path = 'medtech_bpa/medtech_bpa/page/plan_availability/plan_availability.html'
	html=frappe.render_template(path,{'data':data})
	return {'html':html}
def get_filters_codition(filters):
	print(filters)
	conditions = "1=1"
	if filters.get("planning_master"):
		conditions += " and planning_master_parent = '{0}'".format(filters.get('planning_master'))
	return conditions
def get_available_item_qty(item_code, warehouses, company):
	# gets all items available in different warehouses
	warehouses = [x.get('name') for x in frappe.get_list("Warehouse", {'company': company}, "name")]

	filters = frappe._dict({
		'item_code': item_code,
		'warehouse': ['in', warehouses],
		'actual_qty': ['>=', 0]
	})

	item_locations = frappe.get_all('Bin',
		fields=['warehouse', 'actual_qty as qty'],
		filters=filters,
		# limit=required_qty,
		order_by='creation')

	return item_locations