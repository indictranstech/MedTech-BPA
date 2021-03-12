
frappe.ui.form.on("Payment Entry", {
	refresh: function(frm){
		if(frm.doc.party_type == "Customer"
			&& (!frm.doc.payment_allocation_status ||
			in_list(["Pending", "Partially Allocated"], frm.doc.payment_allocation_status))
			&& frm.doc.docstatus === 1) {
			frm.add_custom_button(__('Allocate Payment'), function () {
				frm.trigger("allocate_payment");
			});
		}
	},

	allocate_payment: function(frm) {
		frappe.route_options = {
			"payment_allocation_party": frm.doc.party,
			"unallocated_amt": frm.doc.unallocated_amount,
			"posting_date": frm.doc.posting_date
		};
		frappe.set_route("payment-allocation");
	}	
});

