frappe.ui.form.on("Purchase Order", {
	po_rate_type: function(frm){
		// Set Fixed and Variable Rate according to PO Rate Type Field
		if(frm.doc.po_rate_type == 'Fixed Rate'){
			frm.set_value("maintain_fix_rate",1)
		}
		else
		{
			frm.set_value("maintain_fix_rate",0)
		}
	}
})