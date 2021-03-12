import frappe

@frappe.whitelist()
def get_pending_so():
	so_data = [{'name': 'SAL-ORD-2021-00007',
		'customer': 'LIFE LINE DISTRIBUTOR',
		'status': 'Draft',
		'transaction_date': "2021-02-04",
		'item_code': 'S0H2-1',
		'qty': 120.0,
		'rate': 800.0,
		'amount': 96000.0},
		{'name': 'SAL-ORD-2021-00008',
		'customer': 'LIFE LINE DISTRIBUTOR',
		'status': 'Completed',
		'transaction_date': "2021-02-05",
		'item_code': 'P00541',
		'qty': 12.0,
		'rate': 1000.0,
		'amount': 12000.0},
		{'name': 'SAL-ORD-2021-00009',
		'customer': 'LIFE LINE DISTRIBUTOR',
		'status': 'To Deliver and Bill',
		'transaction_date': "2021-02-05",
		'item_code': 'P00541',
		'qty': 5.0,
		'rate': 800.0,
		'amount': 4000.0}
	]
	data = {}
	data["items"] = so_data
	data["customer"] = "Ruturaj Patil"
	data["pending_amt"] = 200
	return data