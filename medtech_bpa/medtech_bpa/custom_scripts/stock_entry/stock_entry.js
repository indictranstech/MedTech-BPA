
frappe.ui.form.on("Stock Entry", {
	setup: (frm) => {
		frm.set_query('production_plan', () => {
			return {
				filters: {
					'status' :'In Process' ,
					'company': frm.doc.company
				}
			};
		});
		frm.set_query('work_order', () => {
			return {
				filters: {
					'company': frm.doc.company,
					'production_plan':frm.doc.production_plan,
					'production_item':frm.doc.item
				}
			};
		});
	},
	production_plan:function(frm){
		if(frm.doc.production_plan){
			frappe.call({
				"method":"medtech_bpa.medtech_bpa.custom_scripts.stock_entry.stock_entry.get_items_from_production_plan",
				args:{
					'production_plan':frm.doc.production_plan
				},
				callback:function(r){
					if(r.message){
						cur_frm.fields_dict['item'].get_query = function(doc, cdt, cdn) {
			return {
				filters: [
					['Item','name', 'in', r.message]
				]
			}
		}
						}
					}
							
				
			})
		}
	},
	item:function(frm){
		if(frm.doc.production_plan){
			if(frm.doc.item){
				frappe.call({
				"method":"medtech_bpa.medtech_bpa.custom_scripts.stock_entry.stock_entry.get_work_orders",
				"args":{
					'production_plan':frm.doc.production_plan,
					'item':frm.doc.item
				},
				callback:function(r){
					if(r.message){
						frm.set_value('work_order',r.message)
						// frm.set_df_property("work_order","read_only",1)
					}else{
						frappe.throw(__("Error: No Work Order Created For Item {0} and Production Plan {1} ",
					[frm.doc.item,frm.doc.production_plan]
				));
					}
				}
			})
			}
			
		}else{
			frappe.throw("Please Select Production Plan First")
		}

	},
});


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
					if(r.message.rm_warehouse == row.t_warehouse && !frm.doc.purchase_receipt && frm.doc.purpose == 'Material Transfer'){
						frappe.msgprint("Please Enter Visual Inspection Report No")

						// frm.set_df_property('purchase_receipt' , 'reqd', 1)

					}
				}
			}
		});
	}
});