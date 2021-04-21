import json
import frappe
from frappe.utils import getdate, flt
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
					sp_email = frappe.db.get_value("Sales Person", row.sales_person,
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
		so_details = frappe.db.sql("""SELECT name, grand_total, discount_amount from `tabSales Order` where transaction_date>='{0}' and transaction_date<='{1}' and customer='{2}'""".format(pricing_rule[0].get('valid_from'), pricing_rule[0].get('valid_upto'), doc.customer), as_dict=1)
		discount_calculation(doc, so_details, pricing_rule)


def discount_calculation(doc, so_details, pricing_rule):
	total_amt=0.0
	total_amt+=doc.grand_total
	disc_amt = 0.0
	so_name = []
	for row in so_details:
		if row.get("discount_amount")>0:
			so_name.append(row.name)

	if getdate(doc.transaction_date) >= getdate(pricing_rule[0].get('valid_from')) and getdate(doc.transaction_date) <= getdate(pricing_rule[0].get('valid_upto')):
		if so_name:
			disc_amt = doc.grand_total*pricing_rule[0].get("discount_percentage")/100 
			doc.discount_amount = disc_amt
			doc.grand_total = doc.grand_total-disc_amt
			doc.rounded_total = round(doc.grand_total)
			in_words = frappe.utils.money_in_words(round(doc.grand_total))
			doc.in_words = in_words
		else:
			for row in so_details:
				total_amt+=row.grand_total
				if total_amt >= pricing_rule[0].get("max_amt") and not doc.discount_amount:
					disc_amt = total_amt*pricing_rule[0].get("discount_percentage")/100 
					doc.discount_amount = disc_amt
					doc.grand_total = doc.grand_total-disc_amt
					doc.rounded_total = round(doc.grand_total)
					in_words = frappe.utils.money_in_words(round(doc.grand_total))
					doc.in_words = in_words

def update_rate_with_taxes(doc, method):
	item_taxes = frappe._dict()
	# get item_wise_taxes
	if doc.taxes_and_charges or len(doc.get("taxes")):
		for tax in doc.get("taxes"):
			if tax.item_wise_tax_detail:
				tax_detail = json.loads(tax.item_wise_tax_detail)
				for k, v in tax_detail.items():
					if not k in item_taxes:
						item_taxes[k] = flt(v[1])
					else:
						item_taxes[k] = item_taxes.get(k, 0) + flt(v[1])

	#update item table with tax rate
	for item in doc.get("items"):
		if item.rate:
			tax_amt = item_taxes.get(item.item_code) or item_taxes.get(item.item_name)
			if tax_amt and tax_amt > 0:
				item.rate_with_tax = item.rate + flt(tax_amt/item.qty)
			else:
				item.rate_with_tax = item.rate
	doc.flags.ignore_permissions = True
	#doc.save()


@frappe.whitelist()
def reason_of_rejection(reason, name):
	doc = frappe.new_doc("Comment")
	doc.comment_type = "Comment"
	doc.reference_doctype = "Sales Order"
	doc.reference_name = name
	doc.comment_email = frappe.session.user
	doc.comment_by = frappe.db.get_value("User", {'name':frappe.session.user}, 'full_name')
	doc.content = reason
	doc.save()

	return True