# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals
import frappe

from frappe.model.document import Document
import json
from frappe.utils import nowdate, cstr, flt, cint, now, getdate,get_datetime,time_diff_in_seconds,add_to_date,time_diff_in_seconds,add_days, today
from datetime import datetime,date, timedelta
import time
from collections import OrderedDict

import json
# import pandas as pd
# import xlsxwriter
# import csv
# import openpyxl
# from xlsxwriter import Workbook
from frappe import _
import time
import io
import numpy as np
from io import BytesIO
from frappe.utils import cint, flt
from datetime import datetime
from collections import OrderedDict

@frappe.whitelist()
def get_rm_report_details(planning_master= ''):
	# planning master
	pm_dates = get_pm_details(planning_master)
	# planning master detail
	pm_from_date = frappe.db.get_value('Planning Master', {'name' : planning_master}, 'from_date')
	# date list
	pm_date_list = [(pmi.get('date')).strftime('%d-%m-%Y') for pmi in pm_dates]
	pm_date_ll = [pmi.get('date') for pmi in pm_dates]
	# item_detail
	item_data = get_item_details(planning_master)
	# pp detail
	pp_details = get_production_planning_details(planning_master, pm_from_date)
	# po_detail
	po_qty_detail = get_po_qty_detail(planning_master, pm_from_date)
	# ohs
	ohs_detail = get_ohs_qty()
	# required qty
	req_qty = get_required_qty_date_wise(planning_master)
	# date wise po
	po_date_wise = get_po_qty_date_wise(planning_master)


	table_data = []
	final_dict = dict()
	date_wise_details =dict()
	if item_data:
		for item in item_data:
			final_dict[item] = {
				'item_code' : item,
				'stock_uom' : item_data.get(item),
				'planned_qty' : pp_details.get(item) or 0,
				'pending_qty' : po_qty_detail.get(item) or 0,
				'ohs_qty' : ohs_detail.get(item)
			}
			count = 1
			for date in pm_date_ll:
				update_dict = final_dict.get(item)
				if count == 1:
					with_po = (update_dict.get('ohs_qty') + update_dict.get('pending_qty') + po_date_wise.get(item).get(date)) - (update_dict.get('planned_qty') + req_qty.get(item).get(date))
					with_out_po = (update_dict.get('ohs_qty')) - (update_dict.get('planned_qty') + req_qty.get(item).get(date))
				else:
					with_po = (prev_with_po + po_date_wise.get(item).get(date)) - req_qty.get(item).get(date)
					with_out_po = prev_with_out_po - req_qty.get(item).get(date)
				prev_with_po = with_po
				prev_with_out_po = with_out_po
				count = count + 1
				update_dict[date.strftime('%d-%m-%Y')] = {
					'required_qty' : req_qty.get(item).get(date),
					'expected_po' : po_date_wise.get(item).get(date),
					'with_po' : with_po,
					'with_out_po' : with_out_po
				}


		for row in final_dict:
			table_data.append(final_dict.get(row))


	data = dict()
	data['date_list'] = pm_date_list
	data['table_data'] = table_data

	return data


# Filters conditions
def get_filters_codition(planning_master):
	conditions = "and 1=1"
	if planning_master:
		conditions += " and pm.name = '{0}'".format(planning_master)
	return conditions


def get_pm_details(planning_master):
	query = frappe.db.sql("SELECT distinct(pmi.date) from `tabPlanning Master Item` pmi join `tabPlanning Master` pm on pmi.planning_master_parent = pm.name where pm.name = '{0}' order by pmi.date asc".format(planning_master), as_dict =1)
	return query


def get_item_details(planning_master):
	item_list = frappe.db.sql("select bi.item_code, bi.stock_uom from `tabBOM Explosion Item` bi join `tabBOM` b on bi.parent = b.name join `tabPlanning Master Item` pmi on bi.parent = pmi.bom where b.docstatus = 1 and pmi.planning_master_parent = '{0}' group by bi.item_code".format(planning_master), as_dict =1)
	result = {item.item_code : item.stock_uom for item in item_list}
	return result


def get_production_planning_details(planning_master, pm_from_date):
	pp_details = frappe.db.sql("select  mri.parent, mri.item_code, case when pp.posting_date <= '{0}' then mri.quantity end as quantity, mri.uom  from  `tabProduction Plan` pp join `tabMaterial Request Plan Item` mri on mri.parent = pp.name join `tabBOM Explosion Item` bi on bi.item_code = mri.item_code join `tabBOM` b on b.name = bi.parent join `tabPlanning Master Item` pmi on pmi.bom = b.name where pp.docstatus = 1 and pp.status in ('Not Started', 'Submitted', 'In Process') and pmi.planning_master_parent = '{1}'  group by mri.item_code, mri.parent".format(pm_from_date, planning_master), as_dict=1)
	item_dict = dict()

	for item in pp_details:
		if item.item_code in item_dict:
			item_dict[item.item_code] = item_dict.get(item.item_code) + (item.quantity or 0)
		else:
			item_dict[item.item_code] = item.quantity or 0
	return item_dict


def get_po_qty_detail(planning_master, pm_from_date):
	query = frappe.db.sql("select pi.parent, pi.name, pi.item_code, case when pi.expected_delivery_date < '{0}' then (pi.qty - pi.received_qty) end as quantity from `tabPurchase Order` po join `tabPurchase Order Item` pi on pi.parent = po.name  join `tabBOM Explosion Item` bi on bi.item_code = pi.item_code join `tabBOM` b on b.name = bi.parent  join `tabPlanning Master Item` pmi on pmi.bom = b.name where po.docstatus = 1  and po.per_received < 100  and pmi.planning_master_parent = '{1}' group by pi.item_code, pi.parent order by pi.name".format(pm_from_date, planning_master), as_dict =1)
	item_dict = dict()
	for item in query:
		if item.item_code in item_dict:
			item_dict[item.item_code] = item_dict.get(item.item_code) + (item.quantity or 0)
		else:
			item_dict[item.item_code] = item.quantity or 0
	return item_dict


def get_ohs_qty():
	# warehouse list
	fg_warehouse = frappe.db.sql("select warehouse from `tabFG Warehouse Group`", as_dict = 1)
	if fg_warehouse:
		fg_warehouse_ll = ["'" + row.warehouse + "'" for row in fg_warehouse]
		fg_warehouse_list = ','.join(fg_warehouse_ll)
	else:
	    fg_warehouse_list = "' '"

	# group list
	fg_item_group = frappe.db.sql("select item_group from `tabFG Item Group`", as_dict = 1)
	if fg_item_group:
	    fg_group_list = ["'" + row.item_group + "'" for row in fg_item_group]
	    fg_item_group_list = ','.join(fg_group_list)
	else:
	    fg_item_group_list = "' '"

	ohs_query = frappe.db.sql("SELECT item.item_code, sum(IFNULL (bin.actual_qty,0.0)) as ohs from `tabItem` item LEFT JOIN `tabBin` bin on item.item_code = bin.item_code  and item.disabled = 0 and bin.warehouse in ({0}) group by item.item_code".format(fg_warehouse_list), as_dict=1)
	ohs_detail = {row.item_code : row.ohs for row in ohs_query}
	return ohs_detail


def get_required_qty_date_wise(planning_master):
	required_date_wise = frappe.db.sql("select bi.item_code, pmi.date, bi.stock_qty, sum(pmi.amount), (bi.stock_qty * sum(pmi.amount)) as cal_qty from `tabBOM Explosion Item` bi join `tabBOM` b on b.name = bi.parent  join `tabPlanning Master Item` pmi on pmi.bom = b.name where pmi.planning_master_parent = '{0}' group by pmi.date, bi.item_code".format(planning_master), as_dict = 1, debug=1)
	req_dict = dict()
	for item in required_date_wise:
		if item.item_code in req_dict:
			update_dict = req_dict.get(item.item_code)
			update_dict[item.date] = item.cal_qty
		else:
			req_dict[item.item_code] = {
				item.date : item.cal_qty
			}
	return req_dict


def get_po_qty_date_wise(planning_master):
	query = frappe.db.sql("select pi.parent, pi.expected_delivery_date as schedule_date, pi.item_code, (pi.qty - pi.received_qty) as quantity from `tabPurchase Order` po join `tabPurchase Order Item` pi on pi.parent = po.name  join `tabBOM Explosion Item` bi on bi.item_code = pi.item_code join `tabBOM` b on b.name = bi.parent  join `tabPlanning Master Item` pmi on pmi.bom = b.name where po.docstatus = 1  and po.per_received < 100 and pmi.date = pi.expected_delivery_date and pmi.planning_master_parent = '{0}' group by pi.expected_delivery_date, pi.item_code, pi.parent order by pi.item_code".format(planning_master), as_dict =1, debug =1)
	req_dict = dict()

	item_list = get_item_details(planning_master)
	for item in query:
		if item.item_code in req_dict:
			update_dict = req_dict.get(item.item_code)
			if item.schedule_date in update_dict:
				update_dict[item.schedule_date] = update_dict.get(item.schedule_date) + item.quantity
			else:
				update_dict[item.schedule_date] = item.quantity
		else:
			req_dict[item.item_code] = {
				item.schedule_date : item.quantity
			}

	pm_date_list = get_pm_details(planning_master)
	date_list = [pmi.get('date') for pmi in pm_date_list]
	for item in item_list:
		if item in req_dict:
			data = req_dict.get(item)
			for date in date_list:
				if date not in data:
					data[date] = 0
		else:
			req_dict[item] = dict()
			data = req_dict.get(item)
			for date in date_list:
				data[date] = 0
	return req_dict


