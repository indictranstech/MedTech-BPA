frappe.pages['rm-wise-report'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'MRP RM Wise Report',
		single_column: true
	});
	controller = new frappe.rm_wise_report(wrapper);
};

frappe.rm_wise_report = Class.extend({
	init :function(wrapper){
		var me = this;
		me.wrapper_page = wrapper.page
		// '.layout-main-section-wrapper' class for blank dashboard page
		this.page = $(wrapper).find('.layout-main-section-wrapper');
		$(frappe.render_template('rm_wise_report_html')).appendTo(this.page);
		me.base_data()		
		me.planning_master()
		me.from_date()
		me.to_date()
		me.description()
		// me.po()
		// me.item()
		// me.po_toc_status()

		$(".export").click(function(){
			me.get_data_for_export()
		});
	},
	get_data_for_export:function(){
		var me = this
		frappe.call({
		        	"method": "medtech_bpa.medtech_bpa.page.rm_wise_report.rm_wise_report.get_rm_report_details",
			        args: {
			        	planning_master : me.planning_master_list
			        },
			        callback: function (r) {
			        	if (r.message){
			          		var data = r.message
							me.download_xlsx(data)
						}
					}
				})
	},
	download_xlsx: function(data) {
		var me = this;
		return frappe.call({
			module:"medtech_bpa.medtech_bpa",
			page:"rm_wise_report",
			method: "make_xlsx_file",
			args: {renderd_data:data},
			callback: function(r) {
				var w = window.open(
				frappe.urllib.get_full_url(
				"/api/method/medtech_bpa.medtech_bpa.page.rm_wise_report.rm_wise_report.download_xlsx?"));

				if(!w)
					frappe.msgprint(__("Please enable pop-ups")); return;
			}
		})
	},
	base_data:function(){
		var me= this;
		frappe.call({
				method: "medtech_bpa.medtech_bpa.page.rm_wise_report.rm_wise_report.get_rm_report_details",
				async: false,
				freeze_message:"Loading ...Please Wait",
				args:{
					planning_master : me.planning_master_list
				},
				callback: function(r) {
						data=r.message
				}
			})
			me.display_table(data)
	},
	display_table:function(data){
		var me= this;
		$('.rm_wise_report').html($(frappe.render_template('rm_wise_report_table',{"data":data})));
	},
	planning_master:function(){
		var me= this;
		var planning_master = frappe.ui.form.make_control({
		    parent: this.page.find(".planning_master"),
		    df: {
				label: '<b>Planning Master</b>',
				fieldtype: "Link",
				options: "Planning Master",
				fieldname: "",
				placeholder: __("Planning Master"),
				reqd : 1,
				change:function(){
					me.planning_master = this.value?this.value:null
					frappe.call({
						method:"medtech_bpa.medtech_bpa.page.rm_wise_report.rm_wise_report.get_planning_dates",
						args :{
							planning_master : me.planning_master
						},
						callback:function(r){
							$("[data-fieldname=from_date]").val(r.message['from_date'])
							$("[data-fieldname=to_date]").val(r.message['to_date'])
							$("[data-fieldname=description]").val(r.message['description'])
						}
					})
					$("#planning_master").val(planning_master.get_value())
					me.planning_master_list = planning_master.get_value()
					me.base_data()
				}
	     	},
	     	only_input: false,
   		});
		planning_master.refresh();
	},
	from_date:function(){
		var me= this;
		var from_date = frappe.ui.form.make_control({
		    parent: this.page.find(".from_date"),
		    df: {
				label: '<b>From Date</b>',
				fieldtype: "Date",
				options: "",
				fieldname: "from_date",
				placeholder: __("From Date"),
				change:function(){
					me.from_date = $("#from_date").val(from_date.get_value())
				}
	     	},
	     	only_input: false,
   		});
		from_date.refresh();
	},
	to_date:function(){
		var me= this;
		var to_date = frappe.ui.form.make_control({
		    parent: this.page.find(".to_date"),
		    df: {
				label: '<b>To Date</b>',
				fieldtype: "Date",
				options: "",
				fieldname: "to_date",
				placeholder: __("To Date"),
				change:function(){
					me.to_date = $("#to_date").val(to_date.get_value())
				}
	     	},
	     	only_input: false,
   		});
		to_date.refresh();
	},
	description:function(){
		
		var me= this;
		var description = frappe.ui.form.make_control({
		    parent: this.page.find(".description"),
		    df: {
				label: '<b>Description</b>',
				fieldtype: "Data",
				fieldname: "description",
				placeholder: __("Description"),
				change:function(){
					me.description = $("#description").val(description.get_value())
				}
	     	},
	     	only_input: false,
   		});
		description.refresh();
	},
	po:function(){
		var me= this;
		var po = frappe.ui.form.make_control({
		    parent: this.page.find(".po"),
		    df: {
				label: '<b>Purchase Order</b>',
				fieldtype: "Link",
				options: "Purchase Order",
				fieldname: "",
				placeholder: __("Purchase Order"),
				get_query: function(){ 
					return {
						'filters': [
							['Purchase Order', 'docstatus','=','1'],
							['Purchase Order', 'is_subcontracted','=','No']
						]
					}
				},
				change:function(){
					$("#po").val(po.get_value())
					me.po_list = po.get_value()
					me.base_data()
				}
	     	},
	     	only_input: false,
   		});
		po.refresh();
	},
	item:function(){
		var me= this;
		var item = frappe.ui.form.make_control({
		    parent: this.page.find(".item"),
		    df: {
				label: '<b>Item</b>',
				fieldtype: "Link",
				options: "Item",
				fieldname: "",
				placeholder: __("Item"),
				get_query: function(){ 
					return {
						'filters': [
							['Item', 'disabled','=','0']
						]
					}
				},
				change:function(){
					$("#item").val(item.get_value())
					me.item_list = item.get_value()
					me.base_data()
				}
	     	},
	     	only_input: false,
   		});
		item.refresh();
	},
	po_toc_status:function(){
		var me= this;
		frappe.call({
				method: "nano_mag.nano_mag_tech.page.po_report.po_report.get_buffer_levels",
				async: false,
				freeze_message:"Loading ...Please Wait",
				args:{
				},
				callback: function(r) {
					data=r.message
				}
			})
		var po_toc_status = frappe.ui.form.make_control({
		    parent: this.page.find(".po_toc_status"),
		    df: {
				label: '<b>PO TOC Status</b>',
				fieldtype: "Select",
				options: data,
				placeholder: __("PO TOC Status"),
				get_query: function(){ return {'filters': [['Buffer Levels', 'buffer_type','=','Timeline']]}},
				change:function(){
					$("#po_toc_status").val(po_toc_status.get_value())
					me.po_toc_status_list = po_toc_status.get_value()
					me.base_data()
				}
			},
			only_input: false,
	     });
		po_toc_status.refresh();
	}
})
