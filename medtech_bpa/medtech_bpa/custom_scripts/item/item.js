
frappe.ui.form.on("Item", {
	
	refresh: function(frm){
		
		cur_frm.fields_dict['item_group'].get_query = function(doc,cdt,cdn) {
			return{
				filters:{
					'is_group': 0
				}
			};
		};
	}	
	
});

