from __future__ import unicode_literals
from frappe.model.document import Document
import frappe
from frappe.utils import flt,today, get_link_to_form
from frappe import _


def validate(doc, method):
	# fix variable rate
	set_po_item_rate(doc)


def set_po_item_rate(doc):
	if doc.items:
		for item in doc.items:
			if item.po_detail:
				rate = frappe.db.get_value('Purchase Order Item', item.po_detail, 'rate')
				if item.maintain_fix_rate == 1 and rate != item.rate:
					frappe.throw('Not allowed to change the rate for <b>Row {0}</b> as <b>Maintain Fix Rate</b> is checked on the purchase order {1}'.format(item.idx, get_link_to_form('Purchase Order', item.purchase_order)))
