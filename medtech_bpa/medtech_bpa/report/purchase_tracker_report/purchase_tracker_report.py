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
			pri.billed_qty as "billed_qty",
			pri.excess_quantity as "excess_qty",
			pri.short_quantity as "short_qty",
			pri.custom_rejected_qty as "rej_qty",
			pri.actual_accepted_qty as "accepted_qty",
			(pri.billed_qty- pri.actual_accepted_qty) as diff,
			if((select 
				sum(pris.received_qty) 
				from `tabPurchase Receipt` prs 
				INNER JOIN `tabPurchase Receipt Item` pris ON prs.name = pris.parent
				where prs.is_return=1 and prs.docstatus = 1 and prs.return_against = pr.name and pris.item_name = pri.item_name and prs.return_for_warehouse = 'Rejected Warehouse'
				) is null,0,(select 
				sum(pris.received_qty) 
				from `tabPurchase Receipt` prs 
				INNER JOIN `tabPurchase Receipt Item` pris ON prs.name = pris.parent
				where prs.is_return=1 and prs.docstatus = 1 and prs.return_against = pr.name and pris.item_name = pri.item_name and prs.return_for_warehouse = 'Rejected Warehouse'
				)) as "purchase_rtn_qty",
			pr.name,
			if((select 
				sum(pris.received_qty) 
				from `tabPurchase Receipt` prs 
				INNER JOIN `tabPurchase Receipt Item` pris ON prs.name = pris.parent
				where prs.is_return=1 and prs.docstatus = 1 and prs.return_against = pr.name and pris.item_name = pri.item_name and prs.return_for_warehouse in ('Short Warehouse', 'Excess Warehouse')
				) is null,0,(select 
				sum(pris.received_qty) 
				from `tabPurchase Receipt` prs 
				INNER JOIN `tabPurchase Receipt Item` pris ON prs.name = pris.parent
				where prs.is_return=1 and prs.docstatus = 1 and prs.return_against = pr.name and pris.item_name = pri.item_name and prs.return_for_warehouse in ('Short Warehouse', 'Excess Warehouse')
				)) as "debit_note_qty",
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
			(pri.physically_verified_quantity-if((select  
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
			""".format(validate_filters(filters)), as_dict = 1)
	
	final_data = []
	for row in query_data:
		row_data = []
		row_data.append(row.get('pri_item_name'))
		row_data.append(row.get('pr_supplier'))
		row_data.append(row.get('po_no'))
		row_data.append(row.get('vir_no'))
		row_data.append(row.get('supplier_bill_no'))
		row_data.append(row.get('po_qty'))
		row_data.append(row.get('po_date'))
		row_data.append(row.get('req_by_date'))
		row_data.append(row.get('exp_deli_date'))
		row_data.append(row.get('vir_date'))
		row_data.append(row.get('billed_qty'))
		row_data.append(row.get('excess_qty'))
		row_data.append(row.get('short_qty'))
		row_data.append(row.get('rej_qty'))
		row_data.append(row.get('accepted_qty'))
		row_data.append(row.get('diff'))
		row_data.append(row.get('purchase_rtn_qty'))
		row_data.append(0)
		row_data.append(row.get('debit_note_qty'))
		row_data.append((abs(row.get('diff')) - abs(row.get('purchase_rtn_qty')) - abs(row.get('debit_note_qty')) + 0))
		row_data.append(row.get('bill_booked'))
		row_data.append(row.get('pending_for_payment'))
		final_data.append(row_data)
	return final_data


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
			"width": 226
		},
		{
			"fieldname": "pr_supplier",
			"label": _("Supplier Name"),
			"fieldtype": "Link",
			"options": "Supplier",
			"width": 190
		},
		{
			"fieldname": "po_no",
			"label": _("PO No."),
			"fieldtype": "Link",
			"options": "Purchase Order",
			"width": 141
		},
		{
			"fieldname": "vir_no",
			"label": _("VIR No."),
			"fieldtype": "Link",
			"options": "Purchase Receipt",
			"width": 153
		},
		{
			"fieldname": "supplier_bill_no",
			"label": _("Supplier Bill No."),
			"fieldtype": "Data",
			"width": 112
		},
		{
			"fieldname": "po_qty",
			"label": _("PO Qty"),
			"fieldtype": "Float",
			"width": 80
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
			"width": 121
		},
		{
			"fieldname": "exp_deli_date",
			"label": _("Expected Delivery Date"),
			"fieldtype": "Date",
			"width": 159
		},
		{
			"fieldname": "vir_date",
			"label": _("VIR Date"),
			"fieldtype": "Date",
			"width": 100
		},
		{
			"fieldname": "billed_qty",
			"label": _("Billed Qty"),
			"fieldtype": "Float",
			"width": 100
		},
		{
			"fieldname": "excess_qty",
			"label": _("Excess Qty"),
			"fieldtype": "Float",
			"width": 100
		},
		{
			"fieldname": "short_qty",
			"label": _("Short Qty"),
			"fieldtype": "Float",
			"width": 100
		},
		{
			"fieldname": "rej_qty",
			"label": _("Rejected Qty"),
			"fieldtype": "Float",
			"width": 100
		},
		{
			"fieldname": "accepted_qty",
			"label": _("Accepted Qty"),
			"fieldtype": "Float",
			"width": 100
		},
		{
			"fieldname": "diff",
			"label": _("Diffrence (Bill Vs Accept)"),
			"fieldtype": "Float",
			"width": 163
		},
		{
			"fieldname": "purchase_rtn_qty",
			"label": _("Purchase Return Qty"),
			"fieldtype": "Float",
			"width": 140
		},
		{
			"fieldname": "credit_note_qty",
			"label": _("Credit Note Qty"),
			"fieldtype": "Float",
			"width": 112
		},
		{
			"fieldname": "debit_note_qty",
			"label": _("Debit Note Qty"),
			"fieldtype": "Float",
			"width": 110
		},
		{
			"fieldname": "deviation",
			"label": _("Deviation"),
			"fieldtype": "Float",
			"width": 100
		},
		{
			"fieldname": "bill_booked",
			"label": _("Bill Booked"),
			"fieldtype": "Float",
			"width": 100
		},
		{
			"fieldname": "pending_for_payment",
			"label": _("Pending for Invoice/Debit Note"),
			"fieldtype": "Float",
			"width": 140
		}
		
	]
