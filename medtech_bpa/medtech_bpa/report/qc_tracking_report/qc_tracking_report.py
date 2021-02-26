# Copyright (c) 2013, Indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import date_diff,nowdate,getdate


def execute(filters=None):
	columns, data = [], []
	data = get_data(filters)
	columns = get_columns()
	return columns, data

def get_data(filters):
	if filters:
		purchase_receipt = filters.get("purchase_receipt")
		query ='''SELECT pr.name as pr_name,pri.item_code,pri.qty, pri.name,pri.received_qty,pri.custom_rejected_qty, pr.posting_date, 
			CASE
				WHEN  pri.quality_inspection IS NULL  THEN  'Pending'
				WHEN  pri.quality_inspection IS NOT NULL  
				THEN  (select case when qi.docstatus = 1 then 'Submitted' else  'In Progress' END AS status from `tabQuality Inspection` qi where qi.name = pri.quality_inspection)
			END AS status,
			CASE
				WHEN  pri.quality_inspection IS NULL  THEN pr.posting_date
				WHEN  pri.quality_inspection IS NOT NULL THEN( select case when qi.docstatus = 1 then qi.submission_date else date(qi.creation) END AS days from `tabQuality Inspection` qi where qi.name = pri.quality_inspection)
			END AS days
			from `tabPurchase Receipt Item` pri join `tabPurchase Receipt` pr on pri.parent = pr.name
			where pr.is_return = 0 and pr.name ='{0}' order by pr.posting_date,pr.modified asc'''.format(purchase_receipt)
		result = frappe.db.sql(query,as_dict=1)
		result_list =[]
		for data in result:
			if data.get('status') =='Pending' and data.get('days') and data.get('posting_date'):
				# print((getdate(data.get('posting_date')) - getdate(nowdate())).days)
				data['days'] = abs((getdate(data.get('posting_date')) - getdate(nowdate())).days)
			elif data.get('status') =='In Progress' and data.get('days',) :
				# print((getdate(data.get('days')) - getdate(nowdate())).days)
				data['days'] = abs((getdate(data.get('days')) - getdate(nowdate())).days)
			elif data.get('status') =='Submitted' and data.get('days') and data.get('posting_date'):
				# print((getdate(data.get('posting_date')) - getdate(data.get('days'))).days)
				data['days'] = abs((getdate(data.get('posting_date')) - getdate(data.get('days'))).days)
			temp = [ 
					data.get('pr_name'),data.get('item_code'),data.get('qty'),data.get('received_qty'),
					data.get('custom_rejected_qty'),data.get('posting_date'),data.get('status'),data.get('days')
			]
			result_list.append(temp)
		return result_list
	else:
		query ='''SELECT pr.name as pr_name,pri.item_code,pri.qty,pri.received_qty,pri.custom_rejected_qty, pr.posting_date, 
			CASE
				WHEN  pri.quality_inspection IS NULL  THEN  'Pending'
				WHEN  pri.quality_inspection IS NOT NULL  
				THEN  (select case when qi.docstatus = 1 then 'Submitted' else  'In Progress' END AS status from `tabQuality Inspection` qi where qi.name = pri.quality_inspection)
			END AS status,
			CASE
				WHEN  pri.quality_inspection IS NULL  THEN pr.posting_date
				WHEN  pri.quality_inspection IS NOT NULL THEN( select case when qi.docstatus = 1 then qi.submission_date else date(qi.creation) END AS days from `tabQuality Inspection` qi where qi.name = pri.quality_inspection)
			END AS days
			from `tabPurchase Receipt Item` pri join `tabPurchase Receipt` pr on pri.parent = pr.name
			where pr.is_return =0 order by pr.posting_date,pr.modified asc'''
		result = frappe.db.sql(query,as_dict=1)
		result_list = []
		for data in result:
			if data.get('status') =='Pending' and data.get('days') and data.get('posting_date'):
				# print((getdate(data.get('posting_date')) - getdate(nowdate())).days)
				data['days'] = abs((getdate(data.get('posting_date')) - getdate(nowdate())).days)
			elif data.get('status') =='In Progress' and data.get('days',) :
				# print((getdate(data.get('days')) - getdate(nowdate())).days)
				data['days'] = abs((getdate(data.get('days')) - getdate(nowdate())).days)
			elif data.get('status') =='Submitted' and data.get('days') and data.get('posting_date'):
				# print((getdate(data.get('posting_date')) - getdate(data.get('days'))).days)
				data['days'] = abs((getdate(data.get('posting_date')) - getdate(data.get('days'))).days)
			temp = [ 
					data.get('pr_name'),data.get('item_code'),data.get('qty'),data.get('received_qty'),
					data.get('custom_rejected_qty'),data.get('posting_date'),data.get('status'),data.get('days')
			]
			result_list.append(temp)
		return result_list

def get_columns():
	
	return [
		{
			"fieldname": "vis",
			"label": _("VIR"),
			"fieldtype": "Link",
			"options": "Purchase Receipt",
			"width": 200
		},
		{
			"fieldname": "item_code",
			"label": _("Item Code"),
			"fieldtype": "Data",
			"width": 250
		},
		{
			"fieldname": "qty",
			"label": _("Qty"),
			"fieldtype": "float",
			"width": 100
		},
		{
			"fieldname": "received_qty",
			"label": _("Received Qty"),
			"fieldtype": "float",
			"width": 100
		},
		{
			"fieldname": "custom_rejected_qty",
			"label": _("Rejected Qty"),
			"fieldtype": "float",
			"width": 100
		},
		{
			"fieldname": "po_date",
			"label": _("Posting Date"),
			"fieldtype": "Date",
			"width": 100
		},
		{
			"fieldname": "status",
			"label": _("Status"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "days",
			"label": _("Days"),
			"fieldtype": "Data",
			"width": 100
		}
	]


	
