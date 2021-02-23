
frappe.pages['plan_availability'].on_page_load = function(wrapper) {
	frappe.plan_availability_data = new frappe.plan_availability(wrapper);
}

frappe.plan_availability = Class.extend({
	init : function(wrapper){
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: 'Planning Vs Availability Report',
			single_column: true
		});
    	this.wrapper = wrapper
    	this.make()
		this.add_filters()
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
					// me.mass_production(me)	          
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
			
						$("[data-fieldname=from_date]").val(r.message[0].from_date)
						$("[data-fieldname=to_date]").val(r.message[0].to_date)
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
  	},
})
