from __future__ import unicode_literals
import frappe


def validate(doc, method):
	so_name = [row.sales_order for row in doc.items]
	if so_name:
		so_doc =frappe.get_doc("Sales Order", so_name[0])
		so_doc.workflow_state = "Pending for Bill"
		so_doc.db_update()
		frappe.db.commit()


def on_submit(doc, method):
	so_name = [row.sales_order for row in doc.items]
	if so_name:
		so_doc =frappe.get_doc("Sales Order", so_name[0])
		so_doc.workflow_state = "Completed"
		so_doc.db_update()
		frappe.db.commit()