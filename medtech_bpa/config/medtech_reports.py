from __future__ import unicode_literals
from frappe import _
import frappe

def get_data():
	return [

		{
			"label": _("MRP Reports"),
			"items": [
				{
				"type": "page",
				"name": "supplier_wise_rm_wis",
				"description": _("MRP Supplier Wise Report"),
				"onboard":1,
				"label":_("MRP Supplier Wise Report")
				},
				{
				"type": "page",
				"name": "rm-wise-report",
				"description": _("MRP RM Wise Report"),
				"onboard":1,
				"label":_("MRP RM Wise Report")
				},
				{
				"type": "page",
				"name": "plan_availability",
				"description": _("MRP FG Wise Report"),
				"onboard":1,
				"label":_("MRP FG Wise Report")
				} 
			]
		}
	]