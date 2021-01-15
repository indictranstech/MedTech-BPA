from __future__ import unicode_literals
from frappe.model.document import Document
import frappe
from frappe.utils import flt


def validate(doc, method):
	if doc.items:
		for item in doc.items:

			if item.quality_inspection:
				quality_inspection_data  = frappe.db.get_value("Quality Inspection", item.quality_inspection, ["rejected_quantity","rejected_warehouse"],as_dict=1)
				item.rejected_qty = quality_inspection_data.get('rejected_quantity')
				item.rejected_warehouse = quality_inspection_data.get('rejected_warehouse')

			if item.physically_verified_quantity and item.received_qty:
				diff = flt(item.physically_verified_quantity) -  flt(item.received_qty)
				if diff < 0:
					item.short_quantity =  abs(diff)
					item.excess_quantity = 0
				elif diff >= 0: 
					item.excess_quantity = diff
					item.short_quantity =  0

				# accepted_qty = item.received_qty - abs(item.short_quantity) + item.excess_quantity - item.rejected_qty
				# accepted_qty = item.received_qty -  item.rejected_qty
				# item.qty = accepted_qty
			
def before_save(doc,method):
	if doc.is_return != 1:
		map_pr_qty_to_po_qty(doc)
		
@frappe.whitelist()
def map_pr_qty_to_po_qty(doc):
	po_list_data = get_purchase_order(doc.supplier)
	print("----------po_list_data----------",po_list_data)
	for item in doc.items:
		exists = 0
		for po in po_list_data:
			print("-------po-----",po)
			print("--item----",item)
			if po.get("item_code") == item.item_code and po.get("remaining_qty") > 0:
				if item.qty > po.get("remaining_qty"):
					item.qty = 0
					frappe.throw("Allowed quantity for '{0}' at row '{1}' is '{2}'".format(item.item_code,item.idx, po.get('remaining_qty')))
				elif item.qty <= po.get("remaining_qty"):
					item.purchase_order = po.get('name')
					item.purchase_order_item = po.get('pi_name')
					item.warehouse = po.get('warehouse')
					exists = 1
					break
			else:
				continue

		# if item is not available in any of Purchase order throw error
		if exists == 0 :
			pass
			# frappe.throw("Item '{0}' at row '{1}' is not present in any Purchase order".format(item.item_code, item.idx))	
	
@frappe.whitelist()
def get_purchase_order(supplier):
	query = '''SELECT pi.name as pi_name,pi.item_code,pi.qty, po.name,pi.received_qty,pi.returned_qty, ((pi.qty - pi.received_qty) +pi.returned_qty) as remaining_qty, pi.warehouse 
			from `tabPurchase Order Item` pi join `tabPurchase Order` po on pi.parent = po.name 
			where po.supplier = '{0}' and ((pi.qty - pi.received_qty) +pi.returned_qty) > 0 and po.docstatus = 1 and po.status not in ('Closed', 'Completed', 'To Bill') 
			order by po.transaction_date,po.modified asc'''.format(supplier)
	po_list = frappe.db.sql(query, as_dict=1)
	return po_list
