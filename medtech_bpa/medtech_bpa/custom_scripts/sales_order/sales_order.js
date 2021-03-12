frappe.ui.form.on("Sales Order", {
	refresh: function(frm){
		console.log("Refresh ...")
		if(frm.doc.docstatus===0 && !in_list(["Lost", "Stopped", "Closed"], frm.doc.status)) {
			frm.page.add_menu_item(__('Send Email'), function() {
				frm.trigger('send_email');
			});
		}
	},

	send_email: function(frm) {
		frappe.call({
			method: "medtech_bpa.medtech_bpa.custom_scripts.sales_order.sales_order.send_so_notification",
			args: {
				"sales_order": frm.doc.name
			},
			callback: function(r) {
				console.log(r.message)
				if(!r.exc) {
					frappe.msgprint(__("Sending Email ... {}", [r.message]))
				}
			}
		});
	}
})