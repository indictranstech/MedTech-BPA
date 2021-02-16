frappe.pages['supplier_wise_rm_wis'].on_page_load = function(wrapper) {
	frappe.supplier_wise_rm_wis_data = new frappe.supplier_wise_rm_wis(wrapper);
}

frappe.supplier_wise_rm_wis = Class.extend({
	init : function(wrapper){
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: 'Supplier wise RM wise Pending PO against Shortage Report',
			single_column: true
		});
    	this.wrapper = wrapper
    	this.make()
		this.get_imp_data()
		this.add_filters()
	},

	make: function() {
		var me = this;
		$(`<div class="frappe-list list-container"></div>`).appendTo(me.page.main);
	},
	get_imp_data:function(){
	    var me = this
	    $('.frappe-list').html("")
	    var filters = {"planning_master":me.planning_master}
	    if (me.planning_master){
	    	frappe.call({
	        	"method": "medtech_bpa.medtech_bpa.page.supplier_wise_rm_wis.supplier_wise_rm_wis.get_planing_master_details",
		        args: {
		        	filters:filters
		        },
		        callback: function (r) {
		        	if (r.message){
		          		var html = r.message.html
						$('.frappe-list').html(html)
		        	}

		        }//calback end
		    })
	    }
	},

	add_filters:function(){
		var me = this;
		me.page.add_field({
			fieldtype: 'Link',
			label: __('Planning Master'),
			fieldname: 'planning_master',
			options: "Planning Master",
			reqd: 1,
			onchange: function() {
				me.planning_master = this.value?this.value:null
				me.get_imp_data()
			}

		})
  	},
})