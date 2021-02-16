from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import nowdate,nowtime, today
from datetime import timedelta,date
import datetime
import calendar
import json
import time
@frappe.whitelist()
def get_planing_master_details(filters=None):
	filters = json.loads(filters)
	data =[]
	planning_master=frappe.db.sql("""SELECT name, from_date, to_date from `tabPlanning Master` where {0} """.format(get_filters_codition(filters)), as_dict=1)

	planning_item = frappe.db.get_value("Planning Master Item", {'planning_master_parent':planning_master[0].get('name')}, 'bom')
	print("========", planning_item)
	bom_data = frappe.db.sql("""SELECT item_code, item_name, bom_no from `tabBOM Item` where parent='{0}'""".format(planning_item), as_dict=1, )


	for bom_item in bom_data:
		bom_item['from_date'] = datetime.date.today()
		bom_item['to_date'] = planning_master[0].get('to_date')
		bom_item['po_qty']=0.0
		bom_item['consider_po_qty']=0.0
		data.append(bom_item)
		bom_childs =[]
		
		lines = get_child_boms(bom_item,bom_childs)
		for l in lines:
			l['from_date'] = datetime.date.today()
			l['to_date'] = planning_master[0].get('to_date')
			l['po_qty']=0.0
			l['consider_po_qty']=0.0
			data.append(l)
	po_data = []
	for row in data:
		actual_qty = frappe.db.sql("""select sum(actual_qty) as qty from tabBin
		where item_code='{0}' """.format(row.item_code), as_dict=1)
		row['current_stock'] = actual_qty[0].get("qty")

		po_details = frappe.db.sql("""SELECT a.name, a.supplier, b.item_code, b.qty from `tabPurchase Order` a join `tabPurchase Order Item` b on a.name=b.parent where a.docstatus=1 and a.schedule_date<='{0}' and b.item_code='{1}'""".format(row.to_date, row.item_code), as_dict=1)

		for po in po_details:
			if not frappe.db.get_value("Purchase Receipt Item", {'purchase_order':po.get('name')}, 'purchase_order'):
				po_data.append(po)
	supplier = []
	for row in data:			
		for poqty in po_data:
			if row.item_code == poqty.item_code:
				row['po_qty']+=poqty.qty
				supplier.append(poqty.supplier)
				row['supplier']=(list(set(supplier)))
		row['consider_po_qty']=row.current_stock+row.po_qty

	path = 'medtech_bpa/medtech_bpa/page/supplier_wise_rm_wis/supplier_wise_rm_wis.html'
	html=frappe.render_template(path,{'data':data})
	return {'html':html}


def get_filters_codition(filters):
	print(filters)
	conditions = "1=1"
	if filters.get("planning_master"):
		conditions += " and name = '{0}'".format(filters.get('planning_master'))
	return conditions


def get_child_boms(bom_item,bom_childs):
	if bom_item.get("item_code") and bom_item.get("bom_no"):
		bom_name = frappe.db.get_value("BOM",{'item':bom_item.get("item_code")},"name")
		if bom_name:

			childs = frappe.get_all("BOM Item",{"parent":bom_name},["item_code","name","parent", "item_name", 'bom_no'])

			for row in childs:
				item = frappe.db.get_value("BOM", {"name":row.get("parent")}, "item")
				row['parent_bomname'] = item

			bom_childs += childs

			if len(childs)>0:
				for c in childs:
					get_child_boms(c,bom_childs)
	return bom_childs