frappe.ui.form.on("Production Plan", {
	refresh: function(frm){
		// Ignore Projected qty is always be ticked
		if(frm.doc.__islocal){
			frm.set_value("ignore_existing_ordered_qty",1)
		}
		// Allow Parent or group warehouse in material request warehouse list
		frm.set_query('for_warehouse', function(doc) {
			return {
				filters: {
					company: doc.company
				}
			}
		});
	
	},
	get_items_for_mr: function(frm) {
		if (!frm.doc.for_warehouse) {
			frappe.throw(__("Select warehouse for material requests"));
		}
		if (frm.doc.ignore_existing_ordered_qty) {
			// frm.events.get_items_for_material_requests(frm);
			const title = __("Transfer Materials For Warehouse {0}", [frm.doc.for_warehouse]);
			var dialog = new frappe.ui.Dialog({
				title: title,
				fields: [
					{
						"fieldtype": "Table MultiSelect", "label": __("Source Warehouses (Optional)"),
						"fieldname": "warehouses", "options": "Production Plan Material Request Warehouse",
						"description": __("System will pickup the materials from the selected warehouses. If not specified, system will create material request for purchase."),
						get_query: function () {
							return {
								filters: {
									company: frm.doc.company
								}
							};
						},
					},
				]
			});

			dialog.show();

			dialog.set_primary_action(__("Get Items"), () => {
				let warehouses = dialog.get_values().warehouses;
				frm.events.get_items_for_material_requests(frm, warehouses);
				dialog.hide();
			});
		}
	},
	get_items_for_material_request_wip_warehouse:function(frm) {
		if (!frm.doc.wip_warehouse) {
			frappe.throw(__("Select WIP warehouse for material requests"));
		}
		if (frm.doc.ignore_existing_ordered_qty) {
			const title = __("Transfer Materials For Warehouse {0}", [frm.doc.for_warehouse]);
			var dialog = new frappe.ui.Dialog({
				title: title,
				fields: [
					{
						"fieldtype": "Table MultiSelect", "label": __("Source Warehouses (Optional)"),
						"fieldname": "warehouses", "options": "Production Plan Material Request Warehouse",
						"description": __("System will pickup the materials from the selected warehouses. If not specified, system will create material request for purchase."),
						get_query: function () {
							return {
								filters: {
									company: frm.doc.company
								}
							};
						},
					},
				]
			});

			dialog.show();

			dialog.set_primary_action(__("Get Items"), () => {
				let warehouses = dialog.get_values().warehouses;
				frm.events.get_items_for_material_requests(frm, warehouses);
				dialog.hide();
			});
		}
	},
	get_items_for_material_requests: function(frm, warehouses) {
		const set_fields = ['actual_qty', 'item_code','item_name', 'description', 'uom', 'from_warehouse',
			'min_order_qty', 'quantity', 'sales_order', 'warehouse', 'projected_qty', 'material_request_type'];

		frappe.call({
			method: "erpnext.manufacturing.doctype.production_plan.production_plan.get_items_for_material_requests",
			freeze: true,
			args: {
				doc: frm.doc,
				warehouses: warehouses || []
			},
			callback: function(r) {
				if(r.message) {
					frm.set_value('mr_items', []);
					$.each(r.message, function(i, d) {
						var item = frm.add_child('mr_items');
						for (let key in d) {
							if (d[key] && in_list(set_fields, key)) {
								item[key] = d[key];
							}
						}
					});
				}
				refresh_field('mr_items');
			}
		});
	}
});
frappe.ui.form.on("Production Plan Item", {
	// fetch FG Warehouse and WIP Warehouse from Manufacturing Settings
	item_code :function(frm,cdt,cdn){
		frappe.call({
					method: "frappe.client.get_value",
					args: {
						doctype: "Manufacturing Settings",
						fieldname: ['default_fg_warehouse', 'default_wip_warehouse']
					},
					callback: function(r) {
						if(r.message) {
							frappe.model.set_value(cdt, cdn, 'warehouse', r.message.default_fg_warehouse);
							frappe.model.set_value(cdt, cdn, 'for_wip_warehouse', r.message.default_wip_warehouse);
						}
					}
				});
	}
})