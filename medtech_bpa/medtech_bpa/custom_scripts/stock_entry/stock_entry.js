
// frappe.ui.form.on("Stock Entry", {
// 	refresh: function(frm){
// 		frappe.msgprint("rrrrrrrreeeeeeeeload")
// 	}
// });


frappe.ui.form.on("Stock Entry Detail", {
	t_warehouse :function(frm,cdt,cdn){
		var result= ''
		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "MedTech Settings",
				fieldname: ['rm_warehouse']
			},
			callback: function(r) {
				var row = locals[cdt][cdn]
				if(r.message) {
					if(r.message.rm_warehouse == row.t_warehouse){

						frm.set_df_property('purchase_receipt' , 'reqd', 1)

					}
				}
			}
		});
	}
});