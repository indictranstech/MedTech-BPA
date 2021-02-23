from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import nowdate,nowtime, today, flt
from datetime import timedelta,date
import datetime
import calendar
import json
import time
from erpnext.stock.stock_ledger import get_previous_sle
import operator
import itertools

@frappe.whitelist()
def get_planing_master_details(filters=None):
	filters = json.loads(filters)
	data =[]
	from_date = datetime.date.today()
	planning_master=frappe.db.sql("""SELECT name, from_date, to_date from `tabPlanning Master` where {0} """.format(get_filters_codition(filters)), as_dict=1)

	bom_name = frappe.db.sql("""SELECT name, bom, amount from `tabPlanning Master Item` where planning_master_parent='{0}' and date>='{1}' and date<='{2}'""".format(planning_master[0].get('name'), planning_master[0].get('from_date'), planning_master[0].get('to_date')), as_dict=1)

	unic_bom = []
	bom_items=[]
	for row in bom_name:
		if row.bom not in unic_bom:
			unic_bom.append(row.bom)
		bom_data = frappe.db.sql("""SELECT a.name, a.quantity, b.item_code, b.item_name, b.stock_qty from `tabBOM` a join `tabBOM Explosion Item` b on a.name=b.parent where a.name='{0}'""".format(row.bom), as_dict=1)
		
		for bom in bom_data:
			bom['planning_master_item'] = row.name
			bom_items.append(bom)


	#planing_qty calculation from bom and planning master item
	planing_qty=0.0
	for plan_qty in bom_name:
		for row in bom_items:
			if row.planning_master_item==plan_qty.name:
				planing_qty=flt(row.stock_qty)/flt(row.quantity)*flt(plan_qty.amount)
				row["planing_qty"]=planing_qty

	#group_by planning qty base on item_code
	values_by_item = {}
	for d in bom_items:
		values_by_item.setdefault(d['item_code'], []).append(int(d['planing_qty']))
	new_data=[{'item_code':k, 'planing_qty':sum(v)} for k, v in values_by_item.items()]

	
	warehouse = frappe.db.sql("""SELECT warehouse from `tabFG Warehouse Group` where parent='MedTech Settings'""", as_dict=1)

	posting_time = nowtime()
	for row in new_data:
		row['from_date'] = from_date.strftime('%d-%m-%Y')
		row['to_date'] = (planning_master[0].get('to_date')).strftime('%d-%m-%Y')
		row['po_qty']=0.0
		row['consider_po_qty']=0.0
		row['current_stock'] = 0.0

		#current stock calculation of item
		for wh in warehouse:
			last_entry = get_previous_sle({
				"item_code": row.get('item_code'),
				"warehouse" : wh.warehouse,
				"posting_date": from_date,
				"posting_time": posting_time })
			row['current_stock'] += last_entry.qty_after_transaction if last_entry else 0.0

	#calculate pending po qty
	po_data = []
	for row in new_data:
		po_details = frappe.db.sql("""SELECT a.name, a.supplier, b.item_code, b.qty from `tabPurchase Order` a join `tabPurchase Order Item` b on a.name=b.parent where a.docstatus=1 and b.expected_delivery_date <= '{0}' and b.item_code='{1}'""".format(row.get('to_date'), row.get('item_code')), as_dict=1)

		for po in po_details:
			accept_qty = frappe.db.get_values("Purchase Receipt Item", {'purchase_order':po.get('name'), 'item_code':po.get('item_code')}, ['item_code', 'actual_accepted_qty', 'parent', 'purchase_order'], as_dict=1)
			if accept_qty and po.get('item_code') == accept_qty[0].get('item_code'):
				po['qty'] = po.get('qty')-accept_qty[0].get('actual_accepted_qty')

			po_data.append(po)

	#calculate pending po qty for supplier
	supplier = []
	for row in new_data:			
		for poqty in po_data:
			if row.get('item_code') == poqty.item_code:
				row['po_qty']+=round(poqty.qty, 3)
				supplier.append({'supplier':poqty.supplier, 'qty':poqty.qty, 'item_code':poqty.item_code})
	
	outputList=[]
	for i,g in itertools.groupby(supplier, key=operator.itemgetter("item_code")):
		outputList.append(list(g))
	
	for row in new_data:
		for out in outputList:
			if row.get('item_code') == out[0].get('item_code'):
				values_by_supplier = {}
				for d in out:
					values_by_supplier.setdefault(d['supplier'], []).append(int(d['qty']))
				supplier_data=[{'supplier':k, 'qty':sum(v)} for k, v in values_by_supplier.items()]
				row['supplier']=supplier_data

		row['consider_po_qty']=(row.get('current_stock')+row.get('po_qty'))-row.get('planing_qty')
		row['no_consider_po_qty']=row.get('current_stock')-row.get('planing_qty')


	#Production plan qty calculation
	pp_item = []
	for row in unic_bom:
		pp_data = frappe.db.sql("""SELECT c.item_code, c.quantity from `tabProduction Plan` a join `tabProduction Plan Item` b on a.name=b.parent join `tabMaterial Request Plan Item` c on a.name=c.parent where b.bom_no='{0}' and a.docstatus=1 and (a.status='Submitted' or a.status='In Process') and a.posting_date>'{1}' and posting_date<'{2}'""".format(row, planning_master[0].get('from_date'), from_date), as_dict=1)
		for row in pp_data:
			pp_item.append(row)

	#group_by pp qty base on item_code
	values_by_item = {}
	for d in pp_item:
		values_by_item.setdefault(d['item_code'], []).append(int(d['quantity']))
	pp_data=[{'item_code':k, 'qty':sum(v)} for k, v in values_by_item.items()]

	for row in new_data:
		for pp in pp_data:
			if row.get('item_code') == pp.get('item_code'):
				row['consider_po_qty'] = round((row.get('consider_po_qty')-pp.get('qty')),3)
				row['no_consider_po_qty'] = round((row.get('no_consider_po_qty')-pp.get('qty')),3)


	path = 'medtech_bpa/medtech_bpa/page/supplier_wise_rm_wis/supplier_wise_rm_wis.html'
	html=frappe.render_template(path,{'data':new_data})
	return {'html':html}


def get_filters_codition(filters):
	conditions = "1=1"
	if filters.get("planning_master"):
		conditions += " and name = '{0}'".format(filters.get('planning_master'))
	return conditions