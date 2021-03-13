// Copyright (c) 2021, Indictrans and contributors
// For license information, please see license.txt

frappe.ui.form.on('Stock Allocation', {
	refresh: function(frm) {
		//entry must be created/updated from Stock Allocation
		frm.disable_save();
	},
});
