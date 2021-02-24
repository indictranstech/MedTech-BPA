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
	precision=frappe.db.get_singles_value('System Settings', 'float_precision')
	planning_master = filters.get("planning_master")
	# fetch date_data 
	date_data = get_date_data(planning_master)

	data.update({'date_data':date_data})


	# fetch date_data_with_amount
	date_wise_planning_details = date_wise_planning_master(planning_master)

	data.update({'date_data_with_amount':date_wise_planning_details})

	company = frappe.db.get_single_value("Global Defaults",'default_company')
	# fetch warehouse list from medtech settings
	fg_warehouse_list = get_warehouses()
	ohs_dict = get_current_stock(fg_warehouse_list)
	# pending_po_dict = get_expected_stock()

	# fetch planning_data from planning_master item
	planning_data = get_planning_data(planning_master)

	for row in date_wise_planning_details:
		for item in planning_data:
			if row.item_code == item.item_code:
				item.update({row.date:row.amount})


	item_dict = dict()
	final_dict = dict()

	# fetch raw materials data from BOM and stock data
	for item in planning_data:
		bom_data = get_bom_data(item.get('bom'))
		item.update({'bom_data':bom_data})

	item_details = {item.item_code : item for item in planning_data}
	remaining_dict = dict()
	check_date = dict()
	for date in date_wise_planning_details:
		fg_detail = item_details.get(date.get('item_code'))

		for raw in fg_detail.get('bom_data'):
			required_qty = raw.get('stock_qty') * date.get('amount')

			if raw.get('item_code') not in remaining_dict:
				current_stock = ohs_dict.get(raw.get('item_code')) or 0
				stock_expected = get_expected_stock(raw.get('item_code'), date.get('date'))
				stock_exp = stock_expected[0].get("qty") if stock_expected else 0
				virtual_stock = current_stock + stock_exp

				remaining_qty = virtual_stock - required_qty

				remaining_dict[raw.get('item_code')] = remaining_qty if remaining_qty > 0 else 0
				raw[date.get('date')] = flt(remaining_qty, precision) if remaining_qty < 0 else flt(required_qty, precision)
				check_date[raw.get('item_code')] = date.get('date')
			else:
				if date.get('date') == check_date.get(raw.get('item_code')):
					virtual_stock = remaining_dict.get(raw.get('item_code'))
				else:
					stock_expected = get_expected_stock(raw.get('item_code'), date.get('date'))
					stock_exp = stock_expected[0].get("qty") if stock_expected else 0
					check_date[raw.get('item_code')] = date.get('date')
					virtual_stock = stock_exp + remaining_dict.get(raw.get('item_code'))

				remaining_qty = virtual_stock - required_qty

				remaining_dict[raw.get('item_code')] = remaining_qty if remaining_qty > 0 else 0
				raw[date.get('date')] = flt(remaining_qty, precision) if remaining_qty < 0 else flt(required_qty, precision)

	data.update({'planning_data':item_details})
	path = 'medtech_bpa/medtech_bpa/page/plan_availability/plan_availability.html'
	html=frappe.render_template(path,{'data':data})
	return {'html':html}


def get_filters_codition(filters):
	conditions = "1=1"
	if filters.get("planning_master"):
		conditions += " and planning_master_parent = '{0}'".format(filters.get('planning_master'))
	return conditions

# fetch planning dates
def get_date_data(planning_master):
	date_data = frappe.db.sql(""" SELECT DISTINCT a.date from `tabPlanning Master Item` a join `tabPlanning Master` b on a.planning_master_parent = b.name  where a.planning_master_parent= '{0}' group by a.date order by a.date""".format(planning_master), as_dict=1)
	return date_data

# fetch planning_qty and dates
def date_wise_planning_master(planning_master):
	date_data_with_amount = frappe.db.sql(""" SELECT a.item_code, a.date, a.amount from `tabPlanning Master Item` a join `tabPlanning Master` b on a.planning_master_parent = b.name  where a.planning_master_parent= '{0}' order by a.date asc""".format(planning_master), as_dict=1)
	return date_data_with_amount

# fetch FG data and it's details
def get_planning_data(planning_master):
	planning_data = frappe.db.sql(""" SELECT DISTINCT a.item_code,a.item_name, a.uom, sum(a.amount) as amount ,a.bom from `tabPlanning Master Item` a join `tabPlanning Master` b on a.planning_master_parent = b.name  where a.planning_master_parent= '{0}' group by a.item_code """.format(planning_master), as_dict=1)
	return planning_data

# fetch warehouse from medtech settings
def get_warehouses():
	fg_warehouse = frappe.db.sql("SELECT warehouse from `tabFG Warehouse Group`", as_dict = 1)
	fg_warehouse_list = tuple([item.warehouse for item in fg_warehouse])
	return fg_warehouse_list

def get_bom_data(bom):
	bom_data = frappe.db.sql("""SELECT b.item_code,b.stock_uom,b.stock_qty  from `tabBOM` a join `tabBOM Explosion Item` b on b.parent = a.name where a.name = '{0}'""".format(bom),as_dict=1)
	return bom_data

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

def get_current_stock(fg_warehouse_list):
	current_stock = frappe.db.sql("""SELECT item_code,sum(actual_qty) as qty from `tabBin` where warehouse in {0} group by item_code """.format(fg_warehouse_list),as_dict=1)
	ohs_dict = {item.item_code : item.qty for item in current_stock}
	return ohs_dict


def get_expected_stock(item,date):
	stock_expected = frappe.db.sql("""SELECT i.item_code, ifnull(sum((i.qty-i.received_qty)),0) as qty from `tabPurchase Order Item` i join `tabPurchase Order` p on p.name = i.parent where i.item_code = '{0}' and i.expected_delivery_date between '{1}' and '{2}' """.format(item,nowdate(),date),as_dict=1)
	return stock_expected



@frappe.whitelist()
def get_planning_dates(planning_master):
	planning_dates = frappe.db.sql("""SELECT from_date ,to_date from `tabPlanning Master` where name = '{0}'""".format(planning_master),as_dict=1)
	date_dict = dict()
	date_dict['from_date'] =planning_dates[0].get('from_date').strftime('%d-%m-%Y')
	date_dict['to_date'] = planning_dates[0].get("to_date").strftime('%d-%m-%Y') 
	return date_dict