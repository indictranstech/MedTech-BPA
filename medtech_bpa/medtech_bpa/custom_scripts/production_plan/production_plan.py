from __future__ import unicode_literals
from frappe.model.document import Document
import frappe
from frappe.utils import nowdate,nowtime, today
from erpnext.manufacturing.doctype.production_plan.production_plan import ProductionPlan


# from __future__ import unicode_literals
import frappe, json, copy
from frappe import msgprint, _
from six import string_types, iteritems

# from frappe.model.document import Document
from frappe.utils import cstr, flt, cint, nowdate, add_days, comma_and, now_datetime, ceil
from frappe.utils.csvutils import build_csv_response
from erpnext.manufacturing.doctype.bom.bom import validate_bom_no, get_children
from erpnext.manufacturing.doctype.work_order.work_order import get_item_details
from erpnext.setup.doctype.item_group.item_group import get_item_group_defaults
from erpnext.manufacturing.doctype.production_plan.production_plan import get_items_for_material_requests
from erpnext.manufacturing.doctype.production_plan.production_plan import get_bin_details

def validate(doc,method):
	items = [item.item_code for item in doc.mr_items]
	mr_warehouse_list = [item.warehouse for item in doc.material_request_warehouses]
	mr_warehouse_list.append(doc.for_warehouse)
	wip_warehouse_list = [item.warehouse for item in doc.wip_warehouses_production_plan]
	wip_warehouse_list.append(doc.wip_warehouse)
	stock_qty_in_material_issue_warehouse = get_stock_balance(items,doc.posting_date,mr_warehouse_list)
	stock_qty_in_wip_warehouse = get_stock_balance(items,doc.posting_date,wip_warehouse_list)
	for item in doc.mr_items:
		if item.item_code in stock_qty_in_material_issue_warehouse:
			item.qty_in_material_issue_warehouse = stock_qty_in_material_issue_warehouse.get(item.item_code)
		if item.item_code in stock_qty_in_wip_warehouse:
			item.qty_in_wip_warehouse = stock_qty_in_wip_warehouse.get(item.item_code)
		item.quantity_to_be_issued = (item.quantity - item.qty_in_wip_warehouse) if (item.quantity - item.qty_in_wip_warehouse) > 0 else 0
		item.shortage_or_excess_quantity = (item.qty_in_material_issue_warehouse - item.quantity_to_be_issued)

def on_submit(doc,method):
	# Create work order in backend
	ProductionPlan.make_work_order(doc)
	wo_list = frappe.get_list("Work Order", filters={"production_plan":doc.name,"docstatus": ("<", "1")})
	for item in wo_list:
		work_order_doc = frappe.get_doc("Work Order",item)
		work_order_doc.flags.ignore_permissions = 1
		work_order_doc.submit()
	doc.reload()
	
def get_stock_balance(item_set,date,wip_warehouse):
	from_warehouses = []
	if wip_warehouse:
		for row in wip_warehouse:
			warehouse_list = frappe.db.get_descendants('Warehouse', row)
			if warehouse_list:
				for item in warehouse_list:
					from_warehouses.append(item)
			else:
				from_warehouses.append(row)
	# if not from_warehouses:
	# 	from_warehouses = [wip_warehouse]

	if len(from_warehouses) == 1:
		stock_qty = frappe.db.sql("SELECT item.item_code, sum(IFNULL (bin.actual_qty,0.0)) as ohs from `tabItem` item LEFT JOIN `tabBin` bin on item.item_code = bin.item_code  and item.disabled = 0 and bin.warehouse = '{0}' group by item.item_code".format(from_warehouses[0]), as_dict=1,debug=1)
	else:
		stock_qty = frappe.db.sql("SELECT item.item_code, sum(IFNULL (bin.actual_qty,0.0)) as ohs from `tabItem` item LEFT JOIN `tabBin` bin on item.item_code = bin.item_code  and item.disabled = 0 and bin.warehouse in {0} group by item.item_code".format(tuple(from_warehouses)), as_dict=1,debug=1)
	stock_dict = {row.item_code : row.ohs for row in stock_qty}
	return stock_dict


@frappe.whitelist()
def download_raw_materials(doc):
	if isinstance(doc, string_types):
		doc = frappe._dict(json.loads(doc))

	item_list = [['Item Code', 'Description', 'Stock UOM', 'Warehouse', 'Required Qty as per BOM',
		'Projected Qty', 'Actual Qty', 'Ordered Qty', 'Reserved Qty for Production',
		'Safety Stock', 'Required Qty','Qty in Material Issue Warehouse','Qty in WIP Warehouse','Qty to be Issued','Shortage/Excess Qty']]
	for d in get_items_for_material_requests(doc):
		item_list.append([d.get('item_code'), d.get('description'), d.get('stock_uom'), d.get('warehouse'),
			d.get('required_bom_qty'), d.get('projected_qty'), d.get('actual_qty'), d.get('ordered_qty'),
			d.get('reserved_qty_for_production'), d.get('safety_stock'), d.get('quantity'),d.get('qty_in_material_issue_warehouse'),d.get('qty_in_wip_warehouse'),d.get('quantity_to_be_issued'),d.get('shortage_or_excess_quantity')])

		if not doc.get('for_warehouse'):
			row = {'item_code': d.get('item_code')}
			for bin_dict in get_bin_details(row, doc.company, all_warehouse=True):
				if d.get("warehouse") == bin_dict.get('warehouse'):
					continue

				item_list.append(['', '', '', bin_dict.get('warehouse'), '',
					bin_dict.get('projected_qty', 0), bin_dict.get('actual_qty', 0),
					bin_dict.get('ordered_qty', 0), bin_dict.get('reserved_qty_for_production', 0)])
	build_csv_response(item_list, doc.name)


# customized code for download csv and include custom qty fields in csv
@frappe.whitelist()
def get_items_for_material_requests(doc, warehouses=None):
	if isinstance(doc, string_types):
		doc = frappe._dict(json.loads(doc))

	warehouse_list = []
	if warehouses:
		if isinstance(warehouses, string_types):
			warehouses = json.loads(warehouses)

		for row in warehouses:
			child_warehouses = frappe.db.get_descendants('Warehouse', row.get("warehouse"))
			if child_warehouses:
				warehouse_list.extend(child_warehouses)
			else:
				warehouse_list.append(row.get("warehouse"))

	if warehouse_list:
		warehouses = list(set(warehouse_list))

		if doc.get("for_warehouse") and doc.get("for_warehouse") in warehouses:
			warehouses.remove(doc.get("for_warehouse"))

		warehouse_list = None

	doc['mr_items'] = []

	po_items = doc.get('po_items') if doc.get('po_items') else doc.get('items')
	# Check for empty table or empty rows
	if not po_items or not [row.get('item_code') for row in po_items if row.get('item_code')]:
		frappe.throw(_("Items to Manufacture are required to pull the Raw Materials associated with it."),
			title=_("Items Required"))

	company = doc.get('company')
	ignore_existing_ordered_qty = doc.get('ignore_existing_ordered_qty')
	include_safety_stock = doc.get('include_safety_stock')

	so_item_details = frappe._dict()
	for data in po_items:
		planned_qty = data.get('required_qty') or data.get('planned_qty')
		ignore_existing_ordered_qty = data.get('ignore_existing_ordered_qty') or ignore_existing_ordered_qty
		warehouse = doc.get('for_warehouse')

		item_details = {}
		if data.get("bom") or data.get("bom_no"):
			if data.get('required_qty'):
				bom_no = data.get('bom')
				include_non_stock_items = 1
				include_subcontracted_items = 1 if data.get('include_exploded_items') else 0
			else:
				bom_no = data.get('bom_no')
				include_subcontracted_items = doc.get('include_subcontracted_items')
				include_non_stock_items = doc.get('include_non_stock_items')

			if not planned_qty:
				frappe.throw(_("For row {0}: Enter Planned Qty").format(data.get('idx')))

			if bom_no:
				if data.get('include_exploded_items') and include_subcontracted_items:
					# fetch exploded items from BOM
					item_details = get_exploded_items(item_details,
						company, bom_no, include_non_stock_items, planned_qty=planned_qty)
				else:
					item_details = get_subitems(doc, data, item_details, bom_no, company,
						include_non_stock_items, include_subcontracted_items, 1, planned_qty=planned_qty)
		elif data.get('item_code'):
			item_master = frappe.get_doc('Item', data['item_code']).as_dict()
			purchase_uom = item_master.purchase_uom or item_master.stock_uom
			conversion_factor = 0
			for d in item_master.get("uoms"):
				if d.uom == purchase_uom:
					conversion_factor = d.conversion_factor

			item_details[item_master.name] = frappe._dict(
				{
					'item_name' : item_master.item_name,
					'default_bom' : doc.bom,
					'purchase_uom' : purchase_uom,
					'default_warehouse': item_master.default_warehouse,
					'min_order_qty' : item_master.min_order_qty,
					'default_material_request_type' : item_master.default_material_request_type,
					'qty': planned_qty or 1,
					'is_sub_contracted' : item_master.is_subcontracted_item,
					'item_code' : item_master.name,
					'description' : item_master.description,
					'stock_uom' : item_master.stock_uom,
					'conversion_factor' : conversion_factor,
					'safety_stock': item_master.safety_stock
				}
			)

		sales_order = doc.get("sales_order")

		for item_code, details in iteritems(item_details):
			so_item_details.setdefault(sales_order, frappe._dict())
			if item_code in so_item_details.get(sales_order, {}):
				so_item_details[sales_order][item_code]['qty'] = so_item_details[sales_order][item_code].get("qty", 0) + flt(details.qty)
			else:
				so_item_details[sales_order][item_code] = details

	mr_items = []
	for sales_order, item_code in iteritems(so_item_details):
		item_dict = so_item_details[sales_order]
		for details in item_dict.values():
			bin_dict = get_bin_details(details, doc.company, warehouse)
			bin_dict = bin_dict[0] if bin_dict else {}

			if details.qty > 0:
				items = get_material_request_items(details, sales_order, company,
					ignore_existing_ordered_qty, include_safety_stock, warehouse, bin_dict,doc)
				if items:
					mr_items.append(items)

	if not ignore_existing_ordered_qty and warehouses:
		new_mr_items = []
		for item in mr_items:
			get_materials_from_other_locations(item, warehouses, new_mr_items, company)

		mr_items = new_mr_items

	if not mr_items:
		to_enable = frappe.bold(_("Ignore Existing Projected Quantity"))
		warehouse = frappe.bold(doc.get('for_warehouse'))
		message = _("As there are sufficient raw materials, Material Request is not required for Warehouse {0}.").format(warehouse) + "<br><br>"
		message += _("If you still want to proceed, please enable {0}.").format(to_enable)

		frappe.msgprint(message, title=_("Note"))

	return mr_items
def get_materials_from_other_locations(item, warehouses, new_mr_items, company):
	from erpnext.stock.doctype.pick_list.pick_list import get_available_item_locations
	locations = get_available_item_locations(item.get("item_code"),
		warehouses, item.get("quantity"), company, ignore_validation=True)

	if not locations:
		new_mr_items.append(item)
		return

	required_qty = item.get("quantity")
	for d in locations:
		if required_qty <=0: return

		new_dict = copy.deepcopy(item)
		quantity = required_qty if d.get("qty") > required_qty else d.get("qty")

		if required_qty > 0:
			new_dict.update({
				"quantity": quantity,
				"material_request_type": "Material Transfer",
				"from_warehouse": d.get("warehouse")
			})

			required_qty -= quantity
			new_mr_items.append(new_dict)

	if required_qty:
		item["quantity"] = required_qty
		new_mr_items.append(item)

@frappe.whitelist()
def get_bin_details(row, company, for_warehouse=None, all_warehouse=False):
	if isinstance(row, string_types):
		row = frappe._dict(json.loads(row))

	company = frappe.db.escape(company)
	conditions, warehouse = "", ""

	conditions = " and warehouse in (select name from `tabWarehouse` where company = {0})".format(company)
	if not all_warehouse:
		warehouse = for_warehouse or row.get('source_warehouse') or row.get('default_warehouse')

	if warehouse:
		lft, rgt = frappe.db.get_value("Warehouse", warehouse, ["lft", "rgt"])
		conditions = """ and warehouse in (select name from `tabWarehouse`
			where lft >= {0} and rgt <= {1} and name=`tabBin`.warehouse and company = {2})
		""".format(lft, rgt, company)

	return frappe.db.sql(""" select ifnull(sum(projected_qty),0) as projected_qty,
		ifnull(sum(actual_qty),0) as actual_qty, ifnull(sum(ordered_qty),0) as ordered_qty,
		ifnull(sum(reserved_qty_for_production),0) as reserved_qty_for_production, warehouse from `tabBin`
		where item_code = %(item_code)s {conditions}
		group by item_code, warehouse
	""".format(conditions=conditions), { "item_code": row['item_code'] }, as_dict=1)


def get_material_request_items(row, sales_order, company,
	ignore_existing_ordered_qty, include_safety_stock, warehouse, bin_dict,doc):
	total_qty = row['qty']
	required_qty = 0
	if ignore_existing_ordered_qty or bin_dict.get("projected_qty", 0) < 0:
		required_qty = total_qty
	elif total_qty > bin_dict.get("projected_qty", 0):
		required_qty = total_qty - bin_dict.get("projected_qty", 0)
	if required_qty > 0 and required_qty < row['min_order_qty']:
		required_qty = row['min_order_qty']
	item_group_defaults = get_item_group_defaults(row.item_code, company)

	if not row['purchase_uom']:
		row['purchase_uom'] = row['stock_uom']

	if row['purchase_uom'] != row['stock_uom']:
		if not row['conversion_factor']:
			frappe.throw(_("UOM Conversion factor ({0} -> {1}) not found for item: {2}")
				.format(row['purchase_uom'], row['stock_uom'], row.item_code))
		required_qty = required_qty / row['conversion_factor']

	if frappe.db.get_value("UOM", row['purchase_uom'], "must_be_whole_number"):
		required_qty = ceil(required_qty)
	custom_qty_list = frappe.get_list("Material Request Plan Item",filters={'parent':doc.name,'item_code':row.item_code},fields={'qty_in_material_issue_warehouse','qty_in_wip_warehouse','quantity_to_be_issued','shortage_or_excess_quantity'})
	if include_safety_stock:
		required_qty += flt(row['safety_stock'])

	if required_qty > 0:
		return {
			'item_code': row.item_code,
			'item_name': row.item_name,
			'quantity': required_qty,
			'required_bom_qty': total_qty,
			'stock_uom': row.get("stock_uom"),
			'warehouse': warehouse or row.get('source_warehouse') \
				or row.get('default_warehouse') or item_group_defaults.get("default_warehouse"),
			'safety_stock': row.safety_stock,
			'actual_qty': bin_dict.get("actual_qty", 0),
			'projected_qty': bin_dict.get("projected_qty", 0),
			'ordered_qty': bin_dict.get("ordered_qty", 0),
			'reserved_qty_for_production': bin_dict.get("reserved_qty_for_production", 0),
			'min_order_qty': row['min_order_qty'],
			'material_request_type': row.get("default_material_request_type"),
			'sales_order': sales_order,
			'description': row.get("description"),
			'uom': row.get("purchase_uom") or row.get("stock_uom"),
			'qty_in_material_issue_warehouse' : custom_qty_list[0].get('qty_in_material_issue_warehouse'),
			'qty_in_wip_warehouse' : custom_qty_list[0].get("qty_in_wip_warehouse"),
			'quantity_to_be_issued' : custom_qty_list[0].get('quantity_to_be_issued'),
			'shortage_or_excess_quantity' : custom_qty_list[0].get('shortage_or_excess_quantity')
		}

def get_subitems(doc, data, item_details, bom_no, company, include_non_stock_items,
	include_subcontracted_items, parent_qty, planned_qty=1):
	items = frappe.db.sql("""
		SELECT
			bom_item.item_code, default_material_request_type, item.item_name,
			ifnull(%(parent_qty)s * sum(bom_item.stock_qty/ifnull(bom.quantity, 1)) * %(planned_qty)s, 0) as qty,
			item.is_sub_contracted_item as is_sub_contracted, bom_item.source_warehouse,
			item.default_bom as default_bom, bom_item.description as description,
			bom_item.stock_uom as stock_uom, item.min_order_qty as min_order_qty, item.safety_stock as safety_stock,
			item_default.default_warehouse, item.purchase_uom, item_uom.conversion_factor
		FROM
			`tabBOM Item` bom_item
			JOIN `tabBOM` bom ON bom.name = bom_item.parent
			JOIN tabItem item ON bom_item.item_code = item.name
			LEFT JOIN `tabItem Default` item_default
				ON item.name = item_default.parent and item_default.company = %(company)s
			LEFT JOIN `tabUOM Conversion Detail` item_uom
				ON item.name = item_uom.parent and item_uom.uom = item.purchase_uom
		where
			bom.name = %(bom)s
			and bom_item.docstatus < 2
			and item.is_stock_item in (1, {0})
		group by bom_item.item_code""".format(0 if include_non_stock_items else 1),{
			'bom': bom_no,
			'parent_qty': parent_qty,
			'planned_qty': planned_qty,
			'company': company
		}, as_dict=1)

	for d in items:
		if not data.get('include_exploded_items') or not d.default_bom:
			if d.item_code in item_details:
				item_details[d.item_code].qty = item_details[d.item_code].qty + d.qty
			else:
				item_details[d.item_code] = d

		if data.get('include_exploded_items') and d.default_bom:
			if ((d.default_material_request_type in ["Manufacture", "Purchase"] and
				not d.is_sub_contracted) or (d.is_sub_contracted and include_subcontracted_items)):
				if d.qty > 0:
					get_subitems(doc, data, item_details, d.default_bom, company,
						include_non_stock_items, include_subcontracted_items, d.qty)
	return item_details