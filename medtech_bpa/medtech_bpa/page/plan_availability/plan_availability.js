
frappe.pages['plan_availability'].on_page_load = function(wrapper) {
	frappe.plan_availability_data = new frappe.plan_availability(wrapper);
}

frappe.plan_availability = Class.extend({
	init : function(wrapper){
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: 'MRP FG Wise Report',
			single_column: true
		});
    	this.wrapper = wrapper
    	this.make()
		this.add_filters()
		this.add_menus(wrapper);
	},

	make: function() {
		var me = this;
		$(`<div class="frappe-list list-container"></div>`).appendTo(me.page.main);
	},
	get_data:function(){
		var me = this
	    $('.frappe-list').html("")
	    var filters = {"planning_master":me.planning_master}
	    // ,"start_date":me.start_date,"to_date":me.to_date}
	    frappe.call({
	        "method": "medtech_bpa.medtech_bpa.page.plan_availability.plan_availability.get_planning_master_data",
	        args: {filters:filters},
	        callback: function (r) {
	        	if (r.message){
	          		var html = r.message.html
					$('.frappe-list').html(html)
						          
	        	}

	        }//calback end
	    })

	},
	add_filters:function(){
		var me = this;
		me.page.add_field({
			fieldtype: 'Link',
			label: __('Planning Master'),
			fieldname: 'planning_master',
			options: "Planning Master",
			onchange: function() {
				me.planning_master = this.value?this.value:null
				frappe.call({
					method:"medtech_bpa.medtech_bpa.page.plan_availability.plan_availability.get_planning_dates",
					args :{
						planning_master : me.planning_master
					},
					callback:function(r){
		
						$("[data-fieldname=from_date]").val(r.message['from_date'])
						$("[data-fieldname=to_date]").val(r.message['to_date'])
						$("[data-fieldname=description]").val(r.message['description'])
					}
				})
				
				me.get_data()
			}

		})

		const today = frappe.datetime.get_today();
		me.page.add_field({
			fieldtype: 'Date',
			label: __('From Date'),
			fieldname: 'from_date',
			default:"",
			read_only:1,
			onchange: function() {
				me.from_date = this.value?this.value:null
			}
		})
		me.page.add_field({
			fieldtype: 'Date',
			label: __('To Date'),
			fieldname: 'to_date',
			default:"",
			read_only:1,
			onchange: function() {
				me.to_date = this.value?this.value:null
			}
		})
		me.page.add_field({
			fieldtype: 'Data',
			label: __('Description'),
			fieldname: 'description',
			default:"",
			read_only:1,
			onchange: function() {
				me.description = this.value?this.value:null
			}
		})
  	},
  	add_menus:function(wrapper){
		var me = this
		var filters = {"planning_master":me.planning_master}
		wrapper.page.add_menu_item("Export",function(){
			if (me.planning_master){
		    	me.export()
			}
		})
	},
	export:function(){
		var me = this
	    var filters = {"planning_master":me.planning_master}
	    frappe.call({
	        "method": "medtech_bpa.medtech_bpa.page.plan_availability.plan_availability.get_planning_master_data",
	        args: {filters:filters},
	        callback: function (r) {
	        	if (r.message){
	          		data = r.message.data
	          		me.download_xlsx(data)
						          
	        	}

	        }//calback end
	    })

	},
	download_xlsx: function(data) {
		var me = this;
		return frappe.call({
			module:"medtech_bpa.medtech_bpa",
			page:"plan_availability",
			method: "make_xlsx_file",
			args: {renderd_data:data},
			callback: function(r) {
				var w = window.open(
				frappe.urllib.get_full_url(
				"/api/method/medtech_bpa.medtech_bpa.page.plan_availability.plan_availability.download_xlsx?"));

				if(!w)
					frappe.msgprint(__("Please enable pop-ups")); return;
			}
		})
	}
})
