# Copyright (c) 2013, Indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import date_diff,nowdate,getdate


def execute(filters=None):
	columns, data = [], []
	get_data(filters=None)
	return columns, data

def get_data(filters=None):
	if filters:
		pass
	else:
		query ='''SELECT pr.name as pr_name,pri.item_code,pri.qty, pri.name,pri.received_qty,pri.rejected_qty, pr.posting_date, 
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
		print("----------result----------",result)
		for data in result:
			print("--------------",data)
			# if data.get('status') =='Pending' and data.get('days') and data.get('posting_date'):
			# 	print("------getdate(data.get('posting_date'))-------",getdate(data.get('posting_date')))
			# 	print("getdate(nowdate())",getdate(nowdate()))
			# 	print("-------------------",type( getdate(nowdate())), type(getdate(data.get('posting_date'))))
			# 	print("------------date_diff( getdate(data.get('posting_date')) - getdate(nowdate()))---------",date_diff( getdate(data.get('posting_date')) - getdate(nowdate())))
			# 	data['days'] = date_diff( getdate(data.get('posting_date')) - getdate(nowdate()))
			# elif data.get('status') =='In Progress' and data.get('days',) :
			# 	data['days'] = date_diff( getdate(data.get('days')) - getdate(nowdate()))
			# elif data.get('status') =='Submitted' and data.get('days') and data.get('posting_date'):
			# 	data['days'] = date_diff( getdate(data.get('posting_date')) - getdate(data.get('days')))


		print("-----------result-",result)

	
