
frappe.ui.form.on("Payment Entry", {
	refresh: function(frm){
		if(frm.doc.party_type == "Customer"
			&& (!frm.doc.payment_allocation_status ||
			in_list(["Pending", "Partially Allocated"], frm.doc.payment_allocation_status))
			&& frm.doc.docstatus === 1) {
			frm.add_custom_button(__('Stock Allocation'), function () {
				frm.trigger("redirect_to_stock_allocation");
			}).addClass("btn-primary");;
		}
	},

	redirect_to_stock_allocation: function(frm) {
		frappe.route_options = {
			"stock_allocation_party": frm.doc.party,
			"unallocated_amt": frm.doc.unallocated_amount,
			"posting_date": frm.doc.posting_date,
			"payment_entry": frm.doc.name
		};
		frappe.set_route("so_stock_allocation");
	}	
});

