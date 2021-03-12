import frappe
from frappe.utils.background_jobs import enqueue

@frappe.whitelist()
def send_so_notification(sales_order):
	try:
		so = frappe.get_doc("Sales Order", sales_order)
		#get email ids
		recipients = [frappe.db.get_value("Customer", so.customer, "email_id")]
		cc = []
		for row in so.sales_team:
			if row.sales_person:
				sp_email = frappe.db.get_value("Sales Person", row.sales_person,\
					"contact_company_email")
				if sp_email:
					cc.append(sp_email)

		if not recipients and not cc:
			frappe.msgprint("Please add email Ids for Customer and Sales Persons")
		else:
			subject = "Sales Order {} Notification".format(so.name)
			message = "Hi,\t This is system generated message. Do not reply.\n\
			In case of query, check with your System Administrative"

			email_args = {
				"recipients": ['sangram.p@indictranstech.com'], #recipients,
				"sender": None,
				"subject": subject,
				"message": message,
				"now": True,
				"attachments": [frappe.attach_print("Sales Order", so.name)]
			}
			enqueue(method=frappe.sendmail, queue='short', timeout=300, is_async=True, **email_args)
		return so.name
	except Exception as e:
		print("#####################\n {}".format(str(e)))
		#frappe.msgprint("Error: {}".format(str(e)))