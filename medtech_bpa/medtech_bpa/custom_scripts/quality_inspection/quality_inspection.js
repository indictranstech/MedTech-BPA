
frappe.ui.form.on("Quality Inspection", {
	refresh :function(frm,cdt,cdn){
		if(frm.doc.reference_type == 'Purchase Receipt'){
			frm.set_df_property('rejected_warehouse', 'reqd', 1)
		}
	},
	reference_type :function(frm,cdt,cdn){
		if(frm.doc.reference_type == 'Purchase Receipt'){
			frm.set_df_property('rejected_warehouse', 'reqd', 1)
		}
	}
})