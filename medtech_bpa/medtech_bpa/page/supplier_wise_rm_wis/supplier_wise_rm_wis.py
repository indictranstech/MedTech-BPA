from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import nowdate,nowtime, today, flt
from datetime import timedelta,date
import datetime
import calendar
import json
import time

@frappe.whitelist()
def get_planing_master_details(filters=None):
	filters = json.loads(filters)
	data =[]
	from_date = datetime.date.today()
	planning_master=frappe.db.sql("""SELECT name, from_date, to_date from `tabPlanning Master` where {0} """.format(get_filters_codition(filters)), as_dict=1)

	bom_name = frappe.db.sql("""SELECT name, bom, amount from `tabPlanning Master Item` where planning_master_parent='{0}' and date>='{1}' and date<='{2}'""".format(planning_master[0].get('name'), from_date, planning_master[0].get('to_date')), as_dict=1)

	bom_items=[]
	for row in bom_name:
		bom_data = frappe.db.sql("""SELECT a.name, a.quantity, b.qty, b.item_code, b.item_name, b.bom_no from `tabBOM` a join `tabBOM Item` b on a.name=b.parent where a.name='{0}'""".format(row.bom), as_dict=1)
		
		for bom in bom_data:
			bom['planning_master_item'] = row.name
			bom_items.append(bom)

	for bom_item in bom_items:
		data.append(bom_item)
		bom_childs =[]
		lines = get_child_boms(bom_item,bom_childs)
		for l in lines:
			l['quantity'] = frappe.db.get_value("BOM", {'name':l.parent}, 'quantity')
			data.append(l)

	planing_qty=0.0
	for plan_qty in bom_name:
		for row in data:
			if row.planning_master_item==plan_qty.name:
				planing_qty=flt(row.qty)/flt(row.quantity)*flt(plan_qty.amount)
				row["planing_qty"]=planing_qty

	values_by_item = {}
	for d in data:
		values_by_item.setdefault(d['item_code'], []).append(int(d['planing_qty']))

	new_data=[{'item_code':m, 'planing_qty':sum(vs)} for m, vs in values_by_item.items()]
	
	for row in new_data:
		row['from_date'] = from_date
		row['to_date'] = planning_master[0].get('to_date')
		row['po_qty']=0.0
		row['consider_po_qty']=0.0
	

	po_data = []
	for row in new_data:
		
		actual_qty = frappe.db.sql("""select sum(actual_qty) as qty from tabBin
		where item_code='{0}' """.format(row.get('item_code')), as_dict=1)
		row['current_stock'] = actual_qty[0].get("qty")
		print(actual_qty, row.get('item_code'))
		po_details = frappe.db.sql("""SELECT a.name, a.supplier, b.item_code, b.qty from `tabPurchase Order` a join `tabPurchase Order Item` b on a.name=b.parent where a.docstatus=1 and a.schedule_date<='{0}' and b.item_code='{1}'""".format(row.get('to_date'), row.get('item_code')), as_dict=1)

		for po in po_details:
			if not frappe.db.get_value("Purchase Receipt Item", {'purchase_order':po.get('name')}, 'purchase_order'):
				po_data.append(po)
	supplier = []
	for row in new_data:			
		for poqty in po_data:
			if row.get('item_code') == poqty.item_code:
				row['po_qty']+=poqty.qty
				supplier.append(poqty.supplier)
				row['supplier']=(list(set(supplier)))
		row['consider_po_qty']=(row.get('current_stock')+row.get('po_qty'))-row.get('planing_qty')
		row['no_consider_po_qty']=row.get('current_stock')-row.get('planing_qty')

	path = 'medtech_bpa/medtech_bpa/page/supplier_wise_rm_wis/supplier_wise_rm_wis.html'
	html=frappe.render_template(path,{'data':new_data})
	return {'html':html}


def get_filters_codition(filters):
	conditions = "1=1"
	if filters.get("planning_master"):
		conditions += " and name = '{0}'".format(filters.get('planning_master'))
	return conditions


def get_child_boms(bom_item,bom_childs):
	if bom_item.get("item_code") and bom_item.get("bom_no"):
		bom_name = frappe.db.get_value("BOM",{'item':bom_item.get("item_code")},"name")
		if bom_name:

			childs = frappe.get_all("BOM Item",{"parent":bom_name},["item_code","parent", "item_name", 'bom_no', 'qty'])

			for row in childs:
				row['planning_master_item'] = bom_item.planning_master_item

			bom_childs += childs

			if len(childs)>0:
				for c in childs:
					get_child_boms(c,bom_childs)
	return bom_childs