from __future__ import unicode_literals
from frappe.model.document import Document
import frappe
from frappe.utils import nowdate

def validate(doc, method):
	if doc.qc_status in ['100% Accept','Accepted with Deviation']:
		doc.status ='Accepted'
	else:
		doc.status ='Rejected'
def on_submit(doc,method):
	doc.submission_date = nowdate()

