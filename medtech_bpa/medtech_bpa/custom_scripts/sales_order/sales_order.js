frappe.ui.form.on("Sales Order", {
	refresh: function(frm){
		if(frm.doc.docstatus===0 && !in_list(["Lost", "Stopped", "Closed"], frm.doc.status)) {
			frm.page.add_menu_item(__('Send Email'), function() {
				frm.trigger('send_email');
			});
		}
		
		if (frm.doc.workflow_state=="Rejected"){
			frappe.db.get_value('Comment', {'reference_name': frm.doc.name, 'comment_type':"Comment"}, 'name', (r) => {
				if (!r.name){
					frm.trigger('reason_of_rejection')
				}
			});
			frm.add_custom_button(__('Reason of Rejection'), function () {
				frm.trigger('reason_of_rejection')
			})
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
	},

	reason_of_rejection: function(frm) {
		const dialog = new frappe.ui.Dialog({
			title: __("Reason of Rejection"),
			fields: [
				{
	              	label: __(''),
	              	fieldname: "rejection_reason",
	              	fieldtype: "Small Text",
	              	read_only: 0,
	              	reqd: 1, 
	            }
	        ],
			primary_action: function() {
				var data = dialog.get_values();
				frappe.call({
					method: "medtech_bpa.medtech_bpa.custom_scripts.sales_order.sales_order.reason_of_rejection",
					args: {
						reason: data.rejection_reason,
						name: frm.doc.name					
					},
					callback: function(r) {
						frm.reload_doc();
					}
				});
				dialog.hide();
			},
			primary_action_label: __('Update')
		});
		dialog.show();
	}
})