// Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Production Pick List', {
	setup: (frm) => {
		frm.set_indicator_formatter('item_code',
			function(doc) { return (doc.stock_qty === 0) ? "red" : "green"; });
		frm.set_query('parent_warehouse', () => {
			return {
				filters: {
					'is_group': 1,
					'company': frm.doc.company
				}
			};
		});
		frm.set_query('production_plan', () => {
			return {
				filters: {
					'status' :'In Process' 
					// 'company': frm.doc.company
				}
			};
		});

		frm.set_query('work_order', () => {
			return {
				query: 'erpnext.stock.doctype.pick_list.pick_list.get_pending_work_orders',
				filters: {
					'company': frm.doc.company
				}
			};
		});
		frm.set_query('item_code', 'locations', () => {
			return erpnext.queries.item({ "is_stock_item": 1 });
		});
	},
	item:function(frm){
		if(frm.doc.production_plan){
			frappe.call({
				"method":"medtech_bpa.medtech_bpa.doctype.production_pick_list.production_pick_list.get_work_orders",
				"args":{
					'production_plan':frm.doc.production_plan,
					'item':frm.doc.item
				},
				callback:function(r){
					if(r.message){
						frm.set_value('work_order',r.message)
						frm.set_df_property("work_order","read_only",1)
					}else{
						frappe.throw(__("Error: No Work Order Created For Item {0} and Production Plan {1} ",
					[frm.doc.item,frm.doc.production_plan]
				));
					}
				}
			})
		}else{
			frappe.throw("Please Select Production Plan First")
		}

	},
	set_item_locations:(frm, save) => {
		if (!(frm.doc.locations && frm.doc.locations.length)) {
			frappe.msgprint(__('Add items in the Item Locations table'));
		} else {
			frm.call('set_item_locations', {save: save});
		}
	},
	get_item_locations: (frm) => {
		// Button on the form
		frm.events.set_item_locations(frm, false);
	},
	work_order: (frm) => {
		frappe.db.get_value('Work Order',
			frm.doc.work_order,
			['qty', 'material_transferred_for_manufacturing']
		).then(data => {
			let qty_data = data.message;
			let max = qty_data.qty - qty_data.material_transferred_for_manufacturing;
			frappe.prompt({
				fieldtype: 'Float',
				label: __('Qty of Finished Goods Item'),
				fieldname: 'qty',
				description: __('Max: {0}', [max]),
				default: max
			}, (data) => {
				frm.set_value('for_qty', data.qty);
				if (data.qty > max) {
					frappe.msgprint(__('Quantity must not be more than {0}', [max]));
					return;
				}
				frm.clear_table('locations');
				erpnext.utils.map_current_doc({
					method: 'medtech_bpa.medtech_bpa.custom_scripts.work_order.work_order.create_pick_list',
					target: frm,
					source_name: frm.doc.work_order
				});
			}, __('Select Quantity'), __('Get Items'));
		});
	},
	purpose: (frm) => {
		frm.clear_table('locations');
		frm.trigger('add_get_items_button');
	}
});

frappe.ui.form.on('Production Pick List Item', {
	item_code: (frm, cdt, cdn) => {
		let row = frappe.get_doc(cdt, cdn);
		if (row.item_code) {
			get_item_details(row.item_code).then(data => {
				frappe.model.set_value(cdt, cdn, 'uom', data.stock_uom);
				frappe.model.set_value(cdt, cdn, 'stock_uom', data.stock_uom);
				frappe.model.set_value(cdt, cdn, 'conversion_factor', 1);
			});
		}
	},
	uom: (frm, cdt, cdn) => {
		let row = frappe.get_doc(cdt, cdn);
		if (row.uom) {
			get_item_details(row.item_code, row.uom).then(data => {
				frappe.model.set_value(cdt, cdn, 'conversion_factor', data.conversion_factor);
			});
		}
	},
	qty: (frm, cdt, cdn) => {
		let row = frappe.get_doc(cdt, cdn);
		frappe.model.set_value(cdt, cdn, 'stock_qty', row.qty * row.conversion_factor);
	},
	conversion_factor: (frm, cdt, cdn) => {
		let row = frappe.get_doc(cdt, cdn);
		frappe.model.set_value(cdt, cdn, 'stock_qty', row.qty * row.conversion_factor);
	}
});

function get_item_details(item_code, uom=null) {
	if (item_code) {
		return frappe.xcall('medtech_bpa.medtech_bpa.doctype.production_pick_list.production_pick_list.get_item_details', {
			item_code,
			uom
		});
	}
}