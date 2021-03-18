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

def on_update_after_submit(doc,method):
	try:
		if doc.workflow_state == 'Payment Pending':	
			#get email ids
			recipients = [frappe.db.get_value("Customer", doc.customer, "email_id")]
			cc = []
			for row in doc.sales_team:
				if row.sales_person:
					sp_email = frappe.db.get_value("Sales Person", row.sales_person,\
						"contact_company_email")
					if sp_email:
						cc.append(sp_email)

			if not recipients and not cc:
				frappe.msgprint("Please add email Ids for Customer and Sales Persons")
			else:
				subject = "Sales Order {} Notification".format(doc.name)
				message = "Hi,\t This is system generated message. Do not reply.\n\
				In case of query, check with your System Administrative"

				email_args = {
					"recipients": recipients, 
					"cc" : cc,
					"sender": None,
					"subject": subject,
					"message": message,
					"now": True,
					"attachments": [frappe.attach_print("Sales Order", doc.name)]
				}
				enqueue(method=frappe.sendmail, queue='short', timeout=300, is_async=True, **email_args)
			return doc.name
	except Exception as e:
		print("#####################\n {}".format(str(e)))
		#frappe.msgprint("Error: {}".format(str(e)))


def validate(doc, method):
	pricing_rule = frappe.db.get_values("Pricing Rule", {"customer":doc.customer, "is_cummulative_customer":1}, ["max_amt", "valid_from", "valid_upto", "discount_percentage"],as_dict=1)

	if pricing_rule:
		lst_disc_so = frappe.db.sql("""SELECT MAX(transaction_date) AS max_date  FROM `tabSales Order` where discount_amount>0 and transaction_date>='{0}' and transaction_date<='{1}'""".format(pricing_rule[0].get('valid_from'), pricing_rule[0].get('valid_upto')), as_dict=1)

		if lst_disc_so[0].get('max_date'):
			so_details = frappe.db.sql("""SELECT name, grand_total, discount_amount from `tabSales Order` where transaction_date>'{0}' and transaction_date>='{1}' and transaction_date<='{2}'""".format(lst_disc_so[0].get('max_date'),pricing_rule[0].get('valid_from'), pricing_rule[0].get('valid_upto')), as_dict=1)
			discount_calculation(doc,so_details, pricing_rule)
		else:
			so_details = frappe.db.sql("""SELECT name, grand_total, discount_amount from `tabSales Order` where transaction_date>='{1}' and transaction_date<='{2}'""".format(lst_disc_so[0].get('max_date'),pricing_rule[0].get('valid_from'), pricing_rule[0].get('valid_upto')), as_dict=1, debug=1)
			discount_calculation(doc,so_details, pricing_rule)


def discount_calculation(doc, so_details, pricing_rule):
	total_amt=0.0
	total_amt+=doc.grand_total
	disc_amt = 0.0
	
	for row in so_details:
		total_amt+=row.grand_total
		if total_amt >= pricing_rule[0].get("max_amt") and not doc.discount_amount:
			disc_amt = total_amt*pricing_rule[0].get("discount_percentage")/100 
			doc.discount_amount = disc_amt
			doc.grand_total = doc.grand_total-disc_amt
			doc.rounded_total = round(doc.grand_total)
			in_words = frappe.utils.money_in_words(round(doc.grand_total))
			doc.in_words = in_words