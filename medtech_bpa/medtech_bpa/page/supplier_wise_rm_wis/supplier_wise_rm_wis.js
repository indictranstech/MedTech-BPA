frappe.pages['supplier_wise_rm_wis'].on_page_load = function(wrapper) {
	frappe.supplier_wise_rm_wis_data = new frappe.supplier_wise_rm_wis(wrapper);
}

frappe.supplier_wise_rm_wis = Class.extend({
	init : function(wrapper){
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: 'RM & Supplier wise Report',
			single_column: true
		});
    	this.wrapper = wrapper
    	this.make()
		this.get_imp_data()
		this.add_filters()
		this.add_menus(wrapper);
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

  	add_menus:function(wrapper){
		var me = this
		wrapper.page.add_menu_item("Print",function(){
			me.print_pdf()
		})
		wrapper.page.add_menu_item("Export",function(){
			var filters = {"planning_master":me.planning_master}
			if (me.planning_master){
		    	frappe.call({
		        	"method": "medtech_bpa.medtech_bpa.page.supplier_wise_rm_wis.supplier_wise_rm_wis.get_planing_master_details",
			        args: {
			        	filters:filters
			        },
			        callback: function (r) {
			        	if (r.message){
			          		var data = r.message.data
							me.download_xlsx(data)
						}
					}
				})
			}
		})
	},

	print_pdf: function() {
		var me = this;
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
						var formData = new FormData();
						formData.append("html", html);
						var blob = new Blob([], { type: "text/xml"});
						//formData.append("webmasterfile", blob);
						formData.append("blob", blob);

						var xhr = new XMLHttpRequest();
						/*xhr.open("POST", '/api/method/frappe.utils.print_format.report_to_pdf');*/
						xhr.open("POST", '/api/method/medtech_bpa.medtech_bpa.page.supplier_wise_rm_wis.supplier_wise_rm_wis.custome_report_to_pdf');

						xhr.setRequestHeader("X-Frappe-CSRF-Token", frappe.csrf_token);
						xhr.responseType = "arraybuffer";
						xhr.onload = function(success) {
							if (this.status === 200) {
								var blob = new Blob([success.currentTarget.response], {type: "application/pdf"});
								var objectUrl = URL.createObjectURL(blob);

								//Open report in a new window
								window.open(objectUrl);
							}
						};
						xhr.send(formData);
		        	}

		        }//calback end
		    })
	    }
	},

	download_xlsx: function(data) {
		var me = this;
		return frappe.call({
			module:"medtech_bpa.medtech_bpa",
			page:"supplier_wise_rm_wis",
			method: "make_xlsx_file",
			args: {renderd_data:data},
			callback: function(r) {
				var w = window.open(
				frappe.urllib.get_full_url(
				"/api/method/medtech_bpa.medtech_bpa.page.supplier_wise_rm_wis.supplier_wise_rm_wis.download_xlsx?"));

				if(!w)
					frappe.msgprint(__("Please enable pop-ups")); return;
			}
		})
	},
})