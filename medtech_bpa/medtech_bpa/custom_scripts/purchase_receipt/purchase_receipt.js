
frappe.ui.form.on("Purchase Receipt", {

	refresh: function(frm){
	},	
	
});

frappe.ui.form.on("Purchase Receipt Item", {
	physically_verified_quantity :function(frm,cdt,cdn){
		var row = locals[cdt][cdn]
		var short_quantity = 0.0
		var excess_quantity = 0.0
		var diff = flt(row.physically_verified_quantity - row.received_qty)
		if (diff < 0){
			frappe.model.set_value(cdt, cdn, 'short_quantity', Math.abs(diff));
			frm.refresh_field("short_quantity");
		}
		else if(diff >= 0){
			frappe.model.set_value(cdt, cdn, 'excess_quantity', Math.abs(diff));
			frm.refresh_field("excess_quantity");
		}
		var accepted_qty = row.received_qty - short_quantity + excess_quantity - row.rejected_qty
		frappe.model.set_value(cdt, cdn, 'qty', accepted_qty);
		frm.refresh_field("accepted_qty");
	}
});

