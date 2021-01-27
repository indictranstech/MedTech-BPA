frappe.pages['planning-screen'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Planning Screen',
		single_column: true
	});
	controller = new frappe.planning_screen(wrapper);
}

frappe.planning_screen = Class.extend({
	init :function(wrapper){
		var me = this;
		me.wrapper_page = wrapper.page
		// '.layout-main-section-wrapper' class for blank dashboard page
		this.page = $(wrapper).find('.layout-main-section-wrapper');
		$(frappe.render_template('planning_screen_html')).appendTo(this.page);

		$(".create_new").click(function(){
			$('.planning_screen').html($(frappe.render_template('create_new')));
			me.new_from_date()
			me.new_to_date()

			$(".create").click(function(){
				me.get_data()
			});
		});
	},
	get_data:function(){
		var me= this;
		frappe.call({
				method: "medtech_bpa.medtech_bpa.page.planning_screen.planning_screen.get_items_data",
				async: false,
				freeze_message:"Loading ...Please Wait",
				args:{
					from_date : me.new_project_from_date,
					to_date : me.new_project_to_date
				},
				callback: function(r) {
					data=r.message
					$('.create_new_table').html($(frappe.render_template('create_new_table'),{"data":data}));
				}
		});
	},
	new_from_date:function(){
		var me= this;
		var new_from_date = frappe.ui.form.make_control({
		    parent: this.page.find(".new_from_date"),
		    df: {
				label: '<b>From Date</b>',
				fieldtype: "Date",
				options: "",
				fieldname: "",
				placeholder: __("From Date"),
				change:function(){
					$("#new_from_date").val(new_from_date.get_value())
					me.new_project_from_date = new_from_date.get_value()
				}
	     	},
	     	only_input: false,
   		});
		new_from_date.refresh();
	},
	new_to_date:function(){
		var me= this;
		var new_to_date = frappe.ui.form.make_control({
		    parent: this.page.find(".new_to_date"),
		    df: {
				label: '<b>To Date</b>',
				fieldtype: "Date",
				options: "",
				fieldname: "",
				placeholder: __("To Date"),
				change:function(){
					$("#new_to_date").val(new_to_date.get_value())
					me.new_project_to_date = new_to_date.get_value()
				}
	     	},
	     	only_input: false,
   		});
		new_to_date.refresh();
	},
})