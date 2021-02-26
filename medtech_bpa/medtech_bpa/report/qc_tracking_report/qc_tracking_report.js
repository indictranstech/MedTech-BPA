// Copyright (c) 2016, Indictrans and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["QC Tracking Report"] = {
	"filters": [
		{
			"label": __("Visual Inspection Report"),
			"fieldname":"purchase_receipt",
			"fieldtype": "Link",
			"options": "Purchase Receipt"
		}
		
	]
};
