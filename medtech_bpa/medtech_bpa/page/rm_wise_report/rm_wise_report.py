# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals
import frappe

from frappe.model.document import Document
import json
from frappe.utils import nowdate, cstr, flt, cint, now, getdate,get_datetime,time_diff_in_seconds,add_to_date,time_diff_in_seconds,add_days
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
	pm_dates = get_pm_details(planning_master)
	pm_date_list = [(pmi.get('date')).strftime('%d-%m-%Y') for pmi in pm_dates]
	item_detail = get_item_details(planning_master)
	# item_detail_dict = {item.item_code : item.quantity if item.item_code not in item_dict else for item in item_detail}
	# for item in item_detail:

	print("------------------------------------------>>>>")
	print(item_detail)
	# print(item_detail_dict)
	
	print("------------------------------------------>>>>")
	table_data = []
	item_dict = dict()
	for item in item_detail:
		print('------->>>>', item, item.item_code)
		if item.item_code in item_dict:
			update_dict = item_dict.get(item.item_code)
			update_dict['planned_qty'] = update_dict.get('planned_qty') + item.quantity
		else:
			item_dict[item.item_code] = {
				'item_code' : item.item_code,
				'planned_qty' : item.quantity,
				'stock_uom' : item.uom
			}
			print("iiiiiii------>",item_dict)
	print("+++++++++++++++++++++++++")
	print(item_dict)

	for row in item_dict:
		table_data.append(item_dict.get(row))

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
	query = frappe.db.sql("select mri.parent, mri.item_code, case when pp.posting_date < '{0}' then mri.quantity end, mri.uom from `tabMaterial Request Plan Item` mri join `tabProduction Plan` pp on mri.parent = pp.name join `tabProduction Plan Item` ppi on pp.name = ppi.parent join `tabPlanning Master Item` pmi on ppi.item_code = pmi.item_code where pp.docstatus = 1 and pp.status in ('Not Started', 'Submitted', 'In Process') and pmi.planning_master_parent = '{1}' group by mri.item_code, mri.parent".format(planning_master), as_dict =1, debug=1)
	return query


	


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
