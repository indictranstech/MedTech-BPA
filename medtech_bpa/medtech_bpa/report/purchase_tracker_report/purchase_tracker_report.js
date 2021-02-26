// Copyright (c) 2016, Indictrans and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Purchase Tracker Report"] = {
	"filters": [
		{
			"label": __("From Date"),
			"fieldname":"from_date",
			"fieldtype": "Date"
		},
		{
			"label": __("To Date"),
			"fieldname":"to_date",
			"fieldtype": "Date"
		}
	]
};
