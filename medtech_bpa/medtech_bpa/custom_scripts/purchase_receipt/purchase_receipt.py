from __future__ import unicode_literals
from frappe.model.document import Document
import frappe
from frappe.utils import flt,today, get_link_to_form
from frappe import _

def validate(doc, method):
	if doc.is_return:
		setting_doc = frappe.get_single('MedTech Settings')
		if setting_doc.get('rejected_warehouse') == doc.set_warehouse:
			doc.return_for_warehouse = "Purchase Return"
		elif setting_doc.get('short_warehouse') == doc.set_warehouse:
			doc.return_for_warehouse = "Debit Note"
		elif setting_doc.get('excess_warehouse') == doc.set_warehouse:
			doc.return_for_warehouse = "Credit Note"
		else:
			doc.return_for_warehouse = ''

	# fix variable rate
	set_po_item_rate(doc)

	if doc.items:
		if doc.is_return != 1 and doc.get('__islocal')!= 1:
			qc_disable_items = get_qc_disable_items(doc.supplier)
			qc_required_items =[]
			for item in doc.items:
				if item.item_code not in qc_disable_items and not item.quality_inspection and doc.workflow_state =="For Receipt" and doc.is_return != 1:
					frappe.msgprint(_("Create Quality Inspection for Item {0}").format(frappe.bold(item.item_code)))
					qc_required_items.append(item.item_code)
		for item in doc.items:
			if item.quality_inspection:
				quality_inspection_data  = frappe.db.get_value("Quality Inspection", item.quality_inspection, ["rejected_quantity","rejected_warehouse"],as_dict=1)

				item.custom_rejected_qty = quality_inspection_data.get('rejected_quantity')
				item.rejected_warehouse = quality_inspection_data.get('rejected_warehouse')

			if item.physically_verified_quantity and item.billed_qty:
				diff = flt(item.physically_verified_quantity) -  flt(item.billed_qty)
				if diff < 0:
					item.short_quantity =  abs(diff)
					item.excess_quantity = 0
				elif diff >= 0: 
					item.excess_quantity = diff
					item.short_quantity =  0

				item.qty = item.billed_qty
				accepted_qty = item.qty - abs(item.short_quantity) + item.excess_quantity - item.custom_rejected_qty

				item.actual_accepted_qty = accepted_qty
	
			
def before_submit(doc, method):
	qc_disable_items = get_qc_disable_items(doc.supplier)
	get_warehouse = frappe.get_single('MedTech Settings')
	qc_check = 0
	if doc.is_return == 0:
		for item in doc.items:
			if item.item_code in qc_disable_items:
				item.warehouse = get_warehouse.rm_warehouse
			elif item.quality_inspection:
				item.warehouse = get_warehouse.rm_warehouse
				qc_check = 1
			else:
				item.warehouse = get_warehouse.qc_warehouse
		doc.set_warehouse = get_warehouse.rm_warehouse if qc_check == 1 else get_warehouse.qc_warehouse
		

def set_po_item_rate(doc):
	if doc.items:
		for item in doc.items:
			if item.purchase_order_item:
				rate = frappe.db.get_value('Purchase Order Item', item.purchase_order_item, 'rate')
				if item.maintain_fix_rate == 1 and rate != item.rate:
					frappe.throw('Not allowed to change the rate for <b>Row {0}</b> as <b>Maintain Fix Rate</b> is checked on the purchase order {1}'.format(item.idx, get_link_to_form('Purchase Order', item.purchase_order)))


def before_save(doc,method):
	# po_ref = 0
	# for item in doc.items:
	# 	if item.purchase_order:
	# 		po_ref = 1
	# 		break;

	# if doc.is_return != 1 and doc.get('__islocal') and po_ref == 0:
	# 	map_pr_qty_to_po_qty(doc)
	if doc.is_return != 1:
		map_pr_qty_to_po_qty(doc)


@frappe.whitelist()
def map_pr_qty_to_po_qty(doc):
	po_list_data = get_purchase_order(doc.supplier)
	item_list = []
	for item in doc.items:
		item_temp_qty = item.qty
		for po in po_list_data:
			po_temp_qty = po.get("remaining_qty")
			if po.get("item_code") == item.item_code and po_temp_qty > 0 and item_temp_qty > 0:
				if item_temp_qty > po_temp_qty:
					temp = {
						'item_code': item.item_code,
						'item_name': item.item_name,
						'item_group':item.item_group,
						'description': item.description,
						'uom': item.uom,
						'rate':item.rate,
						'price_list_rate':item.price_list_rate,
						'conversion_factor':item.conversion_factor,
						'cost_center':item.cost_center,
						'stock_uom': item.stock_uom,
						'qty':  po_temp_qty,
						'physically_verified_quantity':po_temp_qty,
						'received_qty':po_temp_qty,
						'purchase_order' : po.get('name'),
						'purchase_order_item' : po.get('pi_name'),
						'warehouse' : po.get('warehouse')
					}
					item_temp_qty = item_temp_qty  - po_temp_qty
					po_temp_qty = po_temp_qty -item_temp_qty
					po['remaining_qty'] = po_temp_qty
					item_list.append(temp)

				elif item_temp_qty <= po_temp_qty:

					temp = {
						'item_code': item.item_code,
						'item_name': item.item_name,
						'item_group':item.item_group,
						'description': item.description,
						'uom': item.uom,
						'rate':item.rate,
						'price_list_rate':item.price_list_rate,
						'conversion_factor':item.conversion_factor,
						'cost_center':item.cost_center,
						'stock_uom': item.stock_uom,
						'qty':  item_temp_qty,
						'physically_verified_quantity':item_temp_qty,
						'received_qty':item_temp_qty,
						'purchase_order' : po.get('name'),
						'purchase_order_item' : po.get('pi_name'),
						'warehouse' : po.get('warehouse')
					}
					
					po_temp_qty = po_temp_qty - item_temp_qty
					# item_temp_qty = item_temp_qty  - item_temp_qty
					item_temp_qty = 0
					item_list.append(temp)
					po['remaining_qty'] = po_temp_qty

		if item_temp_qty > 0:

			temp = {
				'item_code': item.item_code,
				'item_name': item.item_name,
				'item_group':item.item_group,
				'description': item.description,
				'uom': item.uom,
				'rate':item.rate,
				'price_list_rate':item.price_list_rate,
				'conversion_factor':item.conversion_factor,
				'cost_center':item.cost_center,
				'stock_uom': item.stock_uom,
				'qty':  item_temp_qty,
				'physically_verified_quantity':item_temp_qty,
				'received_qty':item_temp_qty,
				'warehouse':item.warehouse
			}
			item_list.append(temp)

	
	previous_items = doc.items 
	doc.items = []
	
	for item in item_list:
		doc.append("items", {
			'item_code': item.get('item_code'),
			'item_name': item.get('item_name'),
			'item_group':item.get('item_group'),
			'description': item.get('description'),
			'uom': item.get('uom'),
			'rate':item.get('rate'),
			'base_rate':item.get('rate'),
			'price_list_rate':item.get('price_list_rate'),
			'conversion_factor':item.get('conversion_factor'),
			'cost_center':item.get('cost_center'),
			'stock_uom': item.get('stock_uom'),
			'qty':  item.get('qty'),
			'billed_qty':  item.get('qty'),
			'physically_verified_quantity':item.get('physically_verified_quantity'),
			'received_qty':item.get('received_qty'),
			'purchase_order' : item.get('purchase_order'),
			'purchase_order_item' : item.get('purchase_order_item'),
			'warehouse' : item.get('warehouse')
		})


@frappe.whitelist()
def get_purchase_order(supplier):
	query = '''SELECT pi.name as pi_name,pi.item_code,pi.qty, po.name,pi.received_qty,pi.returned_qty, ((pi.qty - pi.received_qty) +pi.returned_qty) as remaining_qty, pi.warehouse 
			from `tabPurchase Order Item` pi join `tabPurchase Order` po on pi.parent = po.name 
			where po.supplier = '{0}' and ((pi.qty - pi.received_qty) - pi.returned_qty) > 0 and po.docstatus = 1 and po.status not in ('Closed', 'Completed', 'To Bill') 
			order by po.transaction_date,po.modified asc'''.format(supplier)
	po_list = frappe.db.sql(query, as_dict=1,debug=1)
	return po_list


@frappe.whitelist()
def get_qc_disable_items(supplier):
	query = '''SELECT qd.item_code  from `tabQC Disable Supplier` qds join `tabQC Disable` qd 
		on qds.parent = qd.name  where qds.supplier = '{0}' '''.format(supplier)
	qc_disable_items = frappe.db.sql(query, as_dict=1)
	qc_disable_items = [ item.get('item_code') for item in qc_disable_items]
	return qc_disable_items


@frappe.whitelist()
def on_submit(doc, method):
	excess_qty_items = []
	short_qty_items =[]
	rejected_qty_items = []

	for item in doc.items:
		if item.custom_rejected_qty > 0:
			rejected_qty_items.append(item)
		if item.excess_quantity > 0:
			excess_qty_items.append(item)
		elif item.short_quantity > 0:
			short_qty_items.append(item)

	get_warehouse = frappe.get_single('MedTech Settings')
	if len(excess_qty_items) > 0:
		target_warehouse = get_warehouse.excess_warehouse
		make_material_receipt(excess_qty_items,doc, target_warehouse)
	if len(short_qty_items) > 0:
		target_warehouse = get_warehouse.short_warehouse
		make_material_issue(short_qty_items,doc, target_warehouse)
	if len(rejected_qty_items) > 0:
		target_warehouse = get_warehouse.rejected_warehouse
		make_material_transfer(rejected_qty_items,doc, target_warehouse)

@frappe.whitelist()
def make_material_receipt(items,doc, target_warehouse):
	current_date = frappe.utils.today()
	if items:
		stock_entry = frappe.new_doc("Stock Entry")
		if stock_entry:
			stock_entry.posting_date = current_date
			stock_entry.stock_entry_type = "Material Excess From Supplier"
			stock_entry.purchase_receipt = doc.name
			for item in items:
				stock_entry.append("items",{
					'item_code': item.get('item_code'),
					'item_name': item.get('item_name'),
					'item_group':item.get('item_group'),
					'description': item.get('description'),
					'uom': item.get('uom'),
					'qty':flt(item.get('excess_quantity')),
					's_warehouse': item.get('warehouse'),
					't_warehouse': target_warehouse,
					'basic_rate' : item.get('rate')
				})
			stock_entry.save(ignore_permissions = True)
			stock_entry.submit()		
	

@frappe.whitelist()
def make_material_issue(items,doc, target_warehouse):
	try:
		current_date = frappe.utils.today()
		if items:
			stock_entry = frappe.new_doc("Stock Entry")
			if stock_entry:
				stock_entry.posting_date = current_date
				stock_entry.stock_entry_type = "Material Short From Supplier"
				stock_entry.purchase_receipt = doc.name
				for item in items:
					stock_entry.append("items",{
						'item_code': item.get('item_code'),
						'item_name': item.get('item_name'),
						'item_group':item.get('item_group'),
						'description': item.get('description'),
						'uom': item.get('uom'),
						'qty':flt(item.get('short_quantity')),
						's_warehouse': item.get('warehouse'),
						't_warehouse': target_warehouse,
						'basic_rate' : item.get('rate')
					})
				stock_entry.save(ignore_permissions = True)
				stock_entry.submit()
				frappe.db.commit()				
	except Exception as e:
		raise e
				


@frappe.whitelist()
def make_material_transfer(items,doc, target_warehouse):
	try:
		current_date = frappe.utils.today()
		if items:
			stock_entry = frappe.new_doc("Stock Entry")
			if stock_entry:
				stock_entry.posting_date = current_date
				stock_entry.stock_entry_type = "Rejected Material Transfer"
				stock_entry.purchase_receipt = doc.name
				for item in items:
					stock_entry.append("items",{
						'item_code': item.get('item_code'),
						'item_name': item.get('item_name'),
						'item_group':item.get('item_group'),
						'description': item.get('description'),
						'uom': item.get('uom'),
						'qty': item.get('custom_rejected_qty'),
						's_warehouse': item.get('warehouse'),
						't_warehouse': target_warehouse,
						'basic_rate' : item.get('rate')
					})
				stock_entry.save(ignore_permissions = True)
				stock_entry.submit()
				frappe.db.commit()				
	except Exception as e:
		raise e
				