
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
			frappe.model.set_value(cdt, cdn, 'excess_quantity', 0);
			frm.refresh_field("short_quantity");
			frm.refresh_field("excess_quantity");
		}
		else if(diff >= 0){
			frappe.model.set_value(cdt, cdn, 'excess_quantity', Math.abs(diff));
			frappe.model.set_value(cdt, cdn, 'short_quantity', 0);
			frm.refresh_field("short_quantity");
			frm.refresh_field("excess_quantity");
		}
		var accepted_qty = row.received_qty - short_quantity + excess_quantity - row.rejected_qty
		// frappe.model.set_value(cdt, cdn, 'qty', accepted_qty);
		// frm.refresh_field("qty");
	},
	
	received_qty :function(frm,cdt,cdn){
		var row = locals[cdt][cdn]
		var short_quantity = 0.0
		var excess_quantity = 0.0
		var diff = flt(row.physically_verified_quantity - row.received_qty)
		if (diff < 0){
			frappe.model.set_value(cdt, cdn, 'short_quantity', Math.abs(diff));
			frappe.model.set_value(cdt, cdn, 'excess_quantity', 0);
			frm.refresh_field("short_quantity");
			frm.refresh_field("excess_quantity");
		}
		else if(diff >= 0){
			frappe.model.set_value(cdt, cdn, 'excess_quantity', Math.abs(diff));
			frappe.model.set_value(cdt, cdn, 'short_quantity', 0);
			frm.refresh_field("short_quantity");
			frm.refresh_field("excess_quantity");
		}
		var accepted_qty = row.received_qty - short_quantity + excess_quantity - row.rejected_qty
		// frappe.model.set_value(cdt, cdn, 'qty', accepted_qty);
		// frm.refresh_field("qty");
	},

	quality_inspection:function(frm,cdt,cdn) {
		var row = locals[cdt][cdn]
		if (row.quality_inspection){

			frappe.call({
				method:"frappe.client.get_list",
					args:{
						doctype:"Quality Inspection",
						filters: [	["name","=",row.quality_inspection ] ],
						fields: ["rejected_warehouse","rejected_quantity"]
					},
				callback: function(r) {
					if (r.message) {
						console.log(r.message[0]['rejected_warehouse'],r.message[0]['rejected_quantity'])
						frappe.model.set_value(cdt, cdn, 'rejected_warehouse', r.message[0]['rejected_warehouse']);
						frappe.model.set_value(cdt, cdn, 'rejected_qty',r.message[0]['rejected_quantity']);
						frm.refresh_field("rejected_warehouse");
						frm.refresh_field("rejected_quantity");
					}
				}
			});		

		}
	}
});

