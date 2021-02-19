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

	# po_date_wise = get_po_qty_date_wise(planning_master)

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
		update_dict = final_dict.get(item)
		for date in pm_date_list:
			update_dict[date] = {
				'required_qty' : req_qty.get(item).get(date)
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
	query = frappe.db.sql("select pi.parent, pi.name, pi.item_code, case when po.schedule_date < '{0}' then (pi.qty - pi.received_qty) end as quantity from `tabPurchase Order` po join `tabPurchase Order Item` pi on pi.parent = po.name  join `tabBOM Explosion Item` bi on bi.item_code = pi.item_code join `tabBOM` b on b.name = bi.parent  join `tabPlanning Master Item` pmi on pmi.bom = b.name where po.docstatus = 1  and po.per_received < 100  and pmi.planning_master_parent = '{1}' group by pi.item_code, pi.parent order by pi.name".format(pm_from_date, planning_master), as_dict =1)
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
	print('++++++++++++++++++++++++++++++++req_dictttttt+++++++++++++++++++++++++++++++')
	required_date_wise = frappe.db.sql("select bi.item_code, pmi.date, bi.stock_qty, sum(pmi.amount), (bi.stock_qty * sum(pmi.amount)) as cal_qty from `tabBOM Explosion Item` bi join `tabBOM` b on b.name = bi.parent  join `tabPlanning Master Item` pmi on pmi.bom = b.name where pmi.planning_master_parent = '{0}' group by pmi.date, bi.item_code".format(planning_master), as_dict = 1)
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
	query = frappe.db.sql("select pi.parent, po.schedule_date, pi.item_code, (pi.qty - pi.received_qty) as quantity from `tabPurchase Order` po join `tabPurchase Order Item` pi on pi.parent = po.name  join `tabBOM Explosion Item` bi on bi.item_code = pi.item_code join `tabBOM` b on b.name = bi.parent  join `tabPlanning Master Item` pmi on pmi.bom = b.name where po.docstatus = 1  and po.per_received < 100  and pmi.planning_master_parent = '{0}' group by po.schedule_date, pi.item_code, pi.parent order by pi.item_code".format(planning_master), as_dict =1, debug =1)
	req_dict = dict()
	for item in query:
		if item.item_code in req_dict:
			update_dict = req_dict.get(item.item_code)
			print(update_dict)
			print(update_dict[item.date],' = ', update_dict.get(item.date),' + ', item.cal_qty)
			if item.date in update_dict:
				update_dict[item.date] = update_dict.get(item.date) + item.cal_qty
		else:
			req_dict[item.item_code] = {
				item.date : item.cal_qty
			}
	print('*************************************************************')
	print(req_dict)
	print("*************************************************************")
	return req_dict




# @frappe.whitelist()
# def create_file(project= '', from_date = '', to_date= '', po = '', item= '', po_toc_status = ''):
# 	data = get_po_report_details(project, from_date, to_date, po, item, po_toc_status)
# 	file = str(time.time())
# 	now = datetime.now()
# 	fname = "PO_Report_" + now.strftime("%H:%M:%S") + ".xlsx"
# 	file_name = make_xlsx_csv(data, fname)
# 	return file_name

# def make_xlsx_csv(data, fname):
# 	# Create a workbook and add a worksheet.
# 	file = frappe.utils.get_site_path("public")+"/"+ fname
# 	workbook = xlsxwriter.Workbook(file)
# 	worksheet = workbook.add_worksheet()
# 	bold = workbook.add_format({'bold': True})
# 	worksheet.set_column('A:BE', 18)
# 	headers_list = ["PO NO","PO Date","Part Code","Part Description","Job No","Supplier Name","Part Qty","Received Qty","Balanced Qty","Rate","Amount","Lead Time","Remark","Item Category","Inventory On Hand","TOG","Occurance","Nett Balance Quantity","On Order","On Hand plus On Order","Order Color"]

# 	col = 0
# 	for header_data in headers_list:
# 		cell_Style_format = workbook.add_format({'bold': True, 'font_color': "#FFFFFF", 'bg_color': "#5e64ff", 'align': 'center','border':1})
# 		worksheet.write(1, col, header_data, cell_Style_format)
# 		col = col + 1

# 	final_data_list = []
# 	all_data_details = data
# 	for details in all_data_details:
# 		temp = []
# 		temp.append(details.get("po_no"))
# 		temp.append(details.get("po_date"))
# 		temp.append(details.get("part_code"))
# 		temp.append(details.get("part_description"))
# 		temp.append(details.get("job_no"))
# 		temp.append(details.get("supplier_name"))
# 		temp.append(details.get("po_qty"))
# 		temp.append(details.get("received_qty"))
# 		temp.append(details.get("bal_qty"))
# 		temp.append(details.get("rate"))
# 		temp.append(details.get("amount"))
# 		temp.append(details.get("lead_time"))
# 		temp.append(details.get("remark"))
# 		temp.append(details.get("item_category"))
# 		temp.append(details.get("inventory_on_hand"))
# 		temp.append(details.get("tog"))
# 		temp.append(details.get("occurance"))
# 		temp.append(details.get("net_balance_qty"))
# 		temp.append(details.get("on_order"))
# 		temp.append(details.get("on_hand_plus_order"))
# 		temp.append(details.get("order_color"))
# 		final_data_list.append(temp)
# 	row_cnt = 2
# 	col_cnt = 0
# 	for final_data in final_data_list:
# 		col_cnt = 0
# 		for value in final_data:
# 			format2 = workbook.add_format({'border':1,'border_color':'#000000'})
# 			worksheet.write(row_cnt, col_cnt, value,format2)
# 			col_cnt += 1
# 		row_cnt += 1

# 	workbook.close()
# 	return fname


# # ---------- Export Function API to Download created file
# @frappe.whitelist()
# def download_xlsx(name):
# 	import openpyxl
# 	file_path = frappe.utils.get_site_path("public")
# 	wb = openpyxl.load_workbook(file_path+'/'+name)
# 	xlsx_file = io.BytesIO()
# 	wb.save(xlsx_file)
# 	xlsx_file.seek(0)
# 	frappe.local.response.filecontent=xlsx_file.getvalue()
# 	frappe.local.response.type = "download"
# 	filename = name
# 	frappe.local.response.filename = filename
# 	return filename

# @frappe.whitelist()
# def get_buffer_levels():
# 	buffer_levels_timeline_terms = data = frappe.db.sql("SELECT terms FROM `tabBuffer Levels` where buffer_type = 'Timeline'", as_list = 1)
# 	buffer_levels_timeline_terms.insert(0, "")
# 	return buffer_levels_timeline_terms
