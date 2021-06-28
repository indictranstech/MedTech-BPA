from __future__ import unicode_literals
import frappe
from frappe.utils.background_jobs import enqueue


def validate(doc, method):
	# so_name = [row.sales_order for row in doc.items if row.sales_order]
	so_name = frappe.db.get_value("Sales Invoice Item",{'parent':doc.name},'sales_order')
	if so_name:
		so_doc =frappe.get_doc("Sales Order", so_name)
		so_doc.workflow_state = "Pending for Bill"
		so_doc.db_update()
		frappe.db.commit()


def on_submit(doc, method):
	# so_name = [row.sales_order for row in doc.items]
	so_name = frappe.db.get_value("Sales Invoice Item",{'parent':doc.name},'sales_order')

	if so_name:
		so_doc =frappe.get_doc("Sales Order", so_name)
		so_doc.workflow_state = "Completed"
		so_doc.db_update()
		frappe.db.commit()
	try:
		# if doc.workflow_state == 'Payment Pending':
		#get email ids
		recipients = [frappe.db.get_value("Customer", doc.customer, "email_id")]
		cc = []
		for row in doc.sales_team:
			if row.sales_person:
				sp_email = frappe.db.get_value("Sales Person", row.sales_person,
					"contact_company_email")
				if sp_email:
					cc.append(sp_email)
		
		if not recipients and not cc:
			frappe.msgprint("Please add email Ids for Customer and Sales Persons")
		else:
			subject = "Sales Invoice {} Notification".format(doc.name)
			message = "Hi,\t This is system generated message. Do not reply.\n\
			In case of query, check with your System Administrative"

			email_args = {
				"recipients": recipients, 
				"cc" : cc,
				"sender": None,
				"subject": subject,
				"message": message,
				"now": True,
				"attachments": [frappe.attach_print("Sales Invoice", doc.name)]
			}
			enqueue(method=frappe.sendmail, queue='short', timeout=300, is_async=True, **email_args)
		return doc.name
	except Exception as e:
		print("#####################\n {}".format(str(e)))