frappe.ui.form.on("Production Plan", {
	create_pick_list: function(frm, purpose='Material Transfer for Manufacture') {
		this.show_prompt_for_qty_input(frm, purpose)
			.then(data => {
				return frappe.xcall('medtech_bpa.medtech_bpa.work_order.work_order.create_pick_list', {
					'source_name': frm.doc.name,
					'for_qty': data.qty
				});
			}).then(pick_list => {
				frappe.model.sync(production_pick_list);
				frappe.set_route('Form', production_pick_list.doctype, production_pick_list.name);
			});
	}
})