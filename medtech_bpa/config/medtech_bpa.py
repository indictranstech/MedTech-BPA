from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("MedTech-BPA "),
			"icon": "fa fa-star",
			"items": [
				{
					"type": "doctype",
					"name": "QC Disable",
					"description": _("QC Disable"),
					"onboard": 1
				}
			]
		}
		
	]
