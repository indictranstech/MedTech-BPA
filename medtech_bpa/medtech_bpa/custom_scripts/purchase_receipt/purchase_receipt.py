from __future__ import unicode_literals
from frappe.model.document import Document
import frappe
from frappe.utils import flt


def validate(doc, method):
	if doc.items:
		for item in doc.items:
			item.qty = 0
			short_qty = 0
			item.short_quantity = 0
			excess_qty = 0
			item.excess_quantity = 0
			item.rejected_qty = 0

			if item.quality_inspection:
				rejected_quantity = frappe.db.get_value("Quality Inspection", item.quality_inspection, "rejected_quantity")
				item.rejected_qty = rejected_quantity

			if item.physically_verified_quantity and item.received_qty:
				diff = flt(item.physically_verified_quantity) -  flt(item.received_qty)
				short_qty = diff if diff < 0 else 0
				item.short_quantity =  abs(short_qty)
				diff_for_excess_qty = diff if diff >= 0 else 0
				item.excess_quantity = diff_for_excess_qty
				accepted_qty = item.received_qty - abs(item.short_quantity) + item.excess_quantity - item.rejected_qty
				# accepted_qty = item.received_qty -  item.rejected_qty
				item.qty = accepted_qty
			



