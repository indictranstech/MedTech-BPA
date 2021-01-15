# Copyright (c) 2013, Govt and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
	columns, data = get_columns(), get_data(filters)
	return columns, data

def get_data(filters):
	query_data = frappe.db.sql("""
		SELECT
			pri.item_name as "pri_item_name",
			pr.supplier as "pr_supplier",
			pri.purchase_order as "po_no",
			pr.name as "vir_no",
			(select pi.bill_no  
				from `tabPurchase Invoice` pi  
				LEFT JOIN `tabPurchase Invoice Item` pii ON pi.name = pii.parent  
				where pi.is_return !=1 and pi.docstatus = 1 and pii.purchase_receipt = pr.name and pii.item_name = pri.item_name limit 1) as "supplier_bill_no",
			poi.qty as "po_qty",
			po.transaction_date as "po_date",
			poi.schedule_date as "req_by_date",
			poi.expected_delivery_date as "exp_deli_date",
			pr.posting_date as "vir_date",
			pri.received_qty as "received_qty",
			pri.excess_quantity as "excess_qty",
			pri.short_quantity as "short_qty",
			pri.rejected_qty as "rej_qty",
			pri.qty as "accepted_qty",
			(pri.received_qty- pri.qty) as diff,
			if((select 
				sum(pris.received_qty) 
				from `tabPurchase Receipt` prs 
				INNER JOIN `tabPurchase Receipt Item` pris ON prs.name = pris.parent
				where prs.is_return=1 and prs.docstatus = 1 and prs.return_against = pr.name and pris.item_name = pri.item_name
				) is null,0,(select 
				sum(pris.received_qty) 
				from `tabPurchase Receipt` prs 
				INNER JOIN `tabPurchase Receipt Item` pris ON prs.name = pris.parent
				where prs.is_return=1 and prs.docstatus = 1 and prs.return_against = pr.name and pris.item_name = pri.item_name
				)) as "purchase_rtn_qty",
			pr.name,
			if ((select  sum(piiss.qty)  from `tabPurchase Invoice` piss  INNER JOIN `tabPurchase Invoice Item` piiss ON piss.name = piiss.parent where piss.is_return=1 and piiss.docstatus = 1 and piiss.purchase_receipt = pr.name and piiss.item_name = pri.item_name) is null ,0,(select  sum(piiss.qty)  from `tabPurchase Invoice` piss  INNER JOIN `tabPurchase Invoice Item` piiss ON piss.name = piiss.parent where piss.is_return=1 and piiss.docstatus = 1 and piiss.purchase_receipt = pr.name and piiss.item_name = pri.item_name)) as "debit_note_qty",
			pr.name,
			if((select  
				sum(pii.qty) 
				from `tabPurchase Invoice` pi 
				INNER JOIN `tabPurchase Invoice Item` pii ON pi.name = pii.parent 
				where pi.is_return !=1 and pi.docstatus = 1 and pii.purchase_receipt = pr.name and pii.item_name = pri.item_name) is null ,0,(select  
				sum(pii.qty) 
				from `tabPurchase Invoice` pi 
				LEFT JOIN `tabPurchase Invoice Item` pii ON pi.name = pii.parent 
				where pi.is_return !=1 and pi.docstatus = 1 and pii.purchase_receipt = pr.name and pii.item_name = pri.item_name)) as "bill_booked",
			(pri.received_qty-if((select  
				sum(pii.qty) 
				from `tabPurchase Invoice` pi 
				LEFT JOIN `tabPurchase Invoice Item` pii ON pi.name = pii.parent 
				where pi.is_return !=1 and pi.docstatus = 1 and pii.purchase_receipt = pr.name and pii.item_name = pri.item_name) is null ,0,(select  
				sum(pii.qty) 
				from `tabPurchase Invoice` pi 
				LEFT JOIN `tabPurchase Invoice Item` pii ON pi.name = pii.parent 
				where pi.is_return !=1 and pi.docstatus = 1 and pii.purchase_receipt = pr.name and pii.item_name = pri.item_name))) as "pending_for_payment"

		from 
			`tabPurchase Receipt` pr
			INNER JOIN `tabPurchase Receipt Item` pri ON pr.name = pri.parent 
			LEFT JOIN `tabPurchase Order` po ON pri.purchase_order = po.name 
			INNER JOIN `tabPurchase Order Item` poi ON po.name = poi.parent and pri.item_name = poi.item_name
		where {0} and pr.is_return != 1 AND pr.docstatus = 1
		order by pr.creation
			""".format(validate_filters(filters)),debug=1)
	return query_data

def validate_filters(filters):
	conditions = '1 = 1' 
	if filters.get("from_date"): 
		conditions += " and pr.posting_date >= '{0}'".format(filters.get("from_date"))
	if filters.get("to_date"): 
		conditions += " and pr.posting_date <= '{0}'".format(filters.get("to_date"))	 
	return conditions	

def get_columns():
	
	return [
		{
			"fieldname": "pri_item_name",
			"label": _("Item Name"),
			"fieldtype": "Data",
			"options": "Purchae Receipt"
		},
		{
			"fieldname": "pr_supplier",
			"label": _("Supplier Name"),
			"fieldtype": "Data"
		},
		{
			"fieldname": "po_no",
			"label": _("PO No."),
			"fieldtype": "Data"
		},
		{
			"fieldname": "vir_no",
			"label": _("VIR No."),
			"fieldtype": "Data"
		},
		{
			"fieldname": "supplier_bill_no",
			"label": _("Supplier Bill No."),
			"fieldtype": "Data"
		},
		{
			"fieldname": "po_qty",
			"label": _("PO Qty"),
			"fieldtype": "Data"
		},
		{
			"fieldname": "po_date",
			"label": _("PO Date"),
			"fieldtype": "Date",
			"width": 80
		},
		{
			"fieldname": "req_by_date",
			"label": _("Required By Date"),
			"fieldtype": "Date",
			"width": 80
		},
		{
			"fieldname": "exp_deli_date",
			"label": _("Expected Delivery Date"),
			"fieldtype": "Date",
			"width": 80
		},
		{
			"fieldname": "vir_date",
			"label": _("VIR Date"),
			"fieldtype": "Date",
			"width": 80
		},
		{
			"fieldname": "received_qty",
			"label": _("Received Qty"),
			"fieldtype": "Data"
		},
		{
			"fieldname": "excess_qty",
			"label": _("Excess Qty"),
			"fieldtype": "Data"
		},
		{
			"fieldname": "short_qty",
			"label": _("Short Qty"),
			"fieldtype": "Data"
		},
		{
			"fieldname": "rej_qty",
			"label": _("Rejected Qty"),
			"fieldtype": "Data"
		},
		{
			"fieldname": "accepted_qty",
			"label": _("Accepted Qty"),
			"fieldtype": "Data"
		},
		{
			"fieldname": "diff",
			"label": _("Diffrence (Bill Vs Accept)"),
			"fieldtype": "Data"
		},
		{
			"fieldname": "purchase_rtn_qty",
			"label": _("Purchase Return Qty"),
			"fieldtype": "Data"
		},
		{
			"fieldname": "",
			"label": _("Credit Note Qty"),
			"fieldtype": "Data"
		},
		{
			"fieldname": "debit_note_qty",
			"label": _("Debit Note Qty"),
			"fieldtype": "Data"
		},
		{
			"fieldname": "",
			"label": _("Deviation"),
			"fieldtype": "Data"
		},
		{
			"fieldname": "bill_booked",
			"label": _("Bill Booked"),
			"fieldtype": "Data"
		},
		{
			"fieldname": "pending_for_payment",
			"label": _("Pending for Payment"),
			"fieldtype": "Data"
		}
		
	]
