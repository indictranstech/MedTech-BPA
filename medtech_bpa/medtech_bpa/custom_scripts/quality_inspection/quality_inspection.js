
frappe.ui.form.on("Quality Inspection", {
	refresh :function(frm,cdt,cdn){
		if(frm.doc.reference_type == 'Purchase Receipt'){
			frm.set_df_property('rejected_warehouse', 'reqd', 1)
		}
		set_rejected_warehouse(frm)
	},
	reference_type :function(frm,cdt,cdn){
		if(frm.doc.reference_type == 'Purchase Receipt'){
			frm.set_df_property('rejected_warehouse', 'reqd', 1)
		}
	}
})

function set_rejected_warehouse(frm){
	frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "MedTech Settings",
				fieldname: ['rejected_warehouse']
			},
		async :false,
		callback: function(r) {
			if(r.message) {
				console.log(r.message['rejected_warehouse'])
				frm.set_value('rejected_warehouse', r.message['rejected_warehouse'])
				refresh_field('rejected_warehouse')
			}
		}
	});
}