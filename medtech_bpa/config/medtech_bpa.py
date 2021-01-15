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
		},
		{
			"label": _("Report"),
			"icon": "fa fa-star",
			"items": [
				{
					"type": "report",
					"name": "Visual Inspection Report",
					"doctype": "Purchase Receipt",
					"onboard":1,
					"is_query_report": True
				},
					{
					"type": "report",
					"name": "Tracking Report and Export",
					"doctype": "Purchase Receipt",
					"onboard":1,
					"is_query_report": True
				}
			]
		}
		
	]
