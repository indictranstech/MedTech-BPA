frappe.pages['stock-allocation'].on_page_load = function(wrapper) {
	new frappe.stock_allocation({
		$wrapper: $(wrapper)
	});
	//frappe.breadcrumbs.add("MedTech-BPA");
}

frappe.stock_allocation = Class.extend({
	init: function(opts) {
		this.$wrapper = opts.$wrapper
		this.make();
	},

	make: function() {
		this.$wrapper.empty();
		this.$wrapper.append(frappe.render_template("layout"));
		this.clear_localstorage();
		this.fetch_pending_so();
		this.refresh_doc();
		this.change_customer();
		this.save_doc();
		this.submit_doc();
	},

	clear_localstorage: function() {
		//clear localStorage
		keys = ["items", "remaining_amt"]
		$.each(keys, function(i, key) {
			localStorage.removeItem(key);
		})
	},

	fetch_pending_so: function(data) {
		var me = this;
		var data = data ? data: frappe.route_options
		//data["fetch_existing"] = 1
		frappe.call({
			method: "medtech_bpa.medtech_bpa.page.stock_allocation.stock_allocation.get_pending_so",
			args: data,
			callback: function(r) {
				if(!r.exc) {
					$('.item-tbl').html(frappe.render_template("so_item_list", {
						"data": r.message
					}))

					me.update_localstorage_data("customer", r.message.customer)
					me.update_localstorage_data("remaining_amt", r.message.pending_bal)
					me.update_localstorage_data("closing_bal", r.message.closing_bal)
					me.update_localstorage_data("pending_bal", r.message.pending_bal)
					me.update_localstorage_data("total_amt", r.message.sa_total_amt)

					console.log("items", r.message.sa_items)
					// set localstorage with existing data
					if(r.message.sa_items) {
						localStorage.setItem('items', JSON.stringify(r.message.sa_items));
					}

					me.update_qty();
					me.approval_check();
					me.update_remark();
				}
				else {
					if (data && cur_dialog) {
						cur_dialog.hide();
					}
					frappe.msgprint("Unable to fetch the data.")
				}
			}
		})
	},

	update_qty: function() {
		var me = this;
		var is_update_needed = true
		$('.pa-qty').on("change", function() {
			var pa_qty = this.value
			var soi_qty = $(this).closest('tr').find('.soi-qty').attr('data-soi-qty').trim();

			if(!pa_qty || pa_qty < 0) {
				this.value = 0
				$(this).closest('tr').find('.pa-amt').text(0)
				$(this).closest('tr').find('.is_approved').prop("checked", false);
			}

			// validate original qty
			if((cint(pa_qty) > cint(soi_qty))) {
				this.value = 0
				$(this).closest('tr').find('.pa-amt').text(0.00)
				frappe.msgprint(__("Qty is exceeding original Qty"))
			}

			var item_code = $(this).closest('tr').find('.soi-code').attr('data-soi-code').trim();
			var qty = $(this).closest('tr').find('.pa-qty').val();
			var rate = $(this).closest('tr').find('.rate').attr('data-soi-rate').trim();

			var sales_order = $(this).closest('tr').find('.so-name').attr('data-so').trim();
			var is_approved = $(this).closest('tr').find('.is_approved').prop("checked");
			var remark = $(this).closest('tr').find('.pa-remark').val().trim();

			var amount = flt(rate) * cint(qty)

			$(this).closest('tr').find('.pa-amt').text(amount)

			// update stock_qty
			var stock_qty = $(this).closest('tr').find('.stock_qty').attr('data-stock-qty').trim()
			var update_stock_qty = cint(stock_qty) - cint(qty)
			$(this).closest('tr').find('.stock_qty').text(update_stock_qty)
			$(this).closest('tr').find('.pa-amt').text(amount)


			var total_amt = me.calculate_total()
			var pending_bal = me.get_localstorage_data("pending_bal")["pending_bal"]
			var remaining_amt = flt(pending_bal) - flt(total_amt)

			console.log(pending_bal, total_amt, "########")

			// validate amount limit
			if(remaining_amt < 0) {
				frappe.msgprint(__("Exceeding Amount Limit"))
			}

			$('.pending_bal').html("<b>Pending Balance:  </b>"+remaining_amt)
			
			//update localstorage
			me.update_localstorage_data("remaining_amt", remaining_amt)
			me.update_localstorage_data("total_amt", total_amt)
			me.update_localstorage_data("items", {
				"item_code": item_code,
				"qty": cint(qty),
				"rate": rate,
				"amount": flt(amount),
				"sales_order": sales_order,
				"remark": remark,
				"is_approved": is_approved ? 1:0
			})
		})
	},

	approval_check: function() {
		var me = this;
		$('.is_approved').on("click", function() {
			var is_checked = $(this).prop("checked");
			var is_update_needed = false
			
			var qty = $(this).closest('tr').find('.pa-qty').val();
			var rate = $(this).closest('tr').find('.rate').attr('data-soi-rate').trim();
			var item_code = $(this).closest('tr').find('.soi-code').attr('data-soi-code').trim();
			var amount = flt($(this).closest('tr').find('.pa-amt').text() || 0);
			
			if(is_checked) {
				if (cint(qty) <= 0) {
					$(this).prop("checked", false);
					frappe.msgprint("Please allocate the qty first. Qty must be greater than 0")
				}
				else {
					var is_update_needed = true
				}

			}
			if(!is_checked || is_update_needed) {
				var is_approved = is_checked ? 1 : 0
				var item_code = $(this).closest('tr').find('.soi-code').attr('data-soi-code').trim();
				var sales_order = $(this).closest('tr').find('.so-name').attr('data-so').trim();
				var remark = $(this).closest('tr').find('.pa-remark').val().trim();
				me.update_localstorage_data("items", {
					"item_code": item_code,
					"qty": cint(qty),
					"rate": rate,
					"amount": flt(amount),
					"sales_order": sales_order,
					"is_approved": is_approved,
					"remark": remark
				})
			}
		})
	},

	update_remark: function() {
		var me = this;
		$('.pa-remark').on("change", function() {
			var item_code = $(this).closest('tr').find('.soi-code').attr('data-soi-code').trim();
			var sales_order = $(this).closest('tr').find('.so-name').attr('data-so').trim();
			var remark = $(this).closest('tr').find('.pa-remark').val().trim();
			var rate = $(this).closest('tr').find('.rate').attr('data-soi-rate').trim();
			var amount = flt($(this).closest('tr').find('.pa-amt').text() || 0);
			var qty = $(this).closest('tr').find('.pa-qty').val();
			var is_approved = $(this).closest('tr').find('.is_approved').prop("checked");
			me.update_localstorage_data("items", {
				"item_code": item_code,
				"qty": cint(qty),
				"rate": flt(rate),
				"amount": flt(amount),
				"sales_order": sales_order,
				"is_approved": is_approved,
				"remark": remark
			})
		})
	},

	calculate_total: function() {
		var total_amt = 0
		var amt_inputs = $(".pa-amt")
		$.each(amt_inputs, function(i, row) {
			total_amt += flt($(amt_inputs[i]).text().trim() || 0)
		})
		return total_amt
	},

	change_customer: function() {
		var me = this;

		function _change_customer(me) {
			var d = new frappe.ui.Dialog({
				title: __('Select Customer and Posting Date to getting entries.'),
				fields: [
					{
						"label" : "Customer",
						"fieldname": "customer",
						"fieldtype": "Link",
						"options": "Customer",
						"reqd": 1
					},
					{
						"label": __("Fetch With Existing"),
						"fieldname": "fetch_existing",
						"fieldtype": "Check",
						"default": 0
					},
					{
						"fieldtype": 'Column Break',
						"fieldname": 'col_break_1'
					},
					{
						"label": "Posting Date",
						"fieldname": "posting_date",
						"fieldtype": "Date",
						"reqd": 1
					}
				],
				primary_action: function() {
					var data = d.get_values();

					// set route options to avoid refresh trigger conflicts
					frappe.route_options = {
						"stock_allocation_party": data.customer,
						"posting_date": data.posting_date,
					};
					me.clear_localstorage()
					me.fetch_pending_so(data)
					d.hide();
				},
				primary_action_label: __('Fetch Data')
			});
			d.show();
		}

		$('.change_customer').on("click", function() {
			existing_data = me.get_localstorage_data("items")["items"]
			if(Object.keys(existing_data).length) {
				frappe.confirm(__("Please save the changes, if there is any.\
					This action will fetch the data again. \
					Are you certain ?"), function() {
					_change_customer(me);
				});
			}
			else {
				_change_customer(me);
			}
		})
	},

	save_doc: function() {
		var me = this;
		$('.save_doc').on("click", function() {
			var approved_items = $('.is_approved').filter(':checked').length
			if(approved_items == 0) {
				frappe.msgprint(__("No approved allocation found"))
			}
			else {
				var data =  me.get_localstorage_data()
				frappe.call({
					method: "medtech_bpa.medtech_bpa.page.stock_allocation.stock_allocation.save_stock_allocation",
					args: {"data": data},
					async: false,
					callback: function(r) {
						if(!r.exc) {
							frappe.msgprint(__("Stock Allocation {0} Saved Successfully.",
								['<a class="bold" href="#Form/Stock Allocation/'+ r.message + '">' + r.message + '</a>']))
						}
					}
				})
			}
		})
	},

	submit_doc: function() {
		var me = this;
		$('.submit_doc').on("click", function() {
			var approved_items = $('.is_approved').filter(':checked').length
			if(approved_items == 0) {
				frappe.msgprint(__("No approved allocation found"))
			}
			else {
				var data =  me.get_localstorage_data()
				frappe.call({
					method: "medtech_bpa.medtech_bpa.page.stock_allocation.stock_allocation.submit_stock_allocation",
					args: {"data": data},
					async: false,
					callback: function(r) {
						if(!r.exc) {
							me.clear_localstorage();
							me.make();
							frappe.msgprint(__("Stock Allocation {0} Submitted Successfully.\
								Delivery Note: {1}",
								['<a class="bold" href="#Form/Stock Allocation/'+ r.message.stock_allocation + '">' + r.message.stock_allocation + '</a>',
								'<a class="bold" href="#Form/Delivery Note/'+ r.message.delivery_note + '">' + r.message.delivery_note + '</a>']))
						}
					}
				})
			}
		})
	},

	refresh_doc: function() {
		var me = this;
		$('.refresh_doc').on("click", function() {
			existing_data = me.get_localstorage_data("items")["items"]
			if(Object.keys(existing_data).length) {
				frappe.confirm(__("This action will fetch the data again. \
					Please save the changes if there is any. \
					Are you certain ?"), function() {
					me.make();
				});
			}
			else {
				me.make();
			}
		});
	},

	get_localstorage_data: function(key=false) {
		data = {}
		let keys = key ? [key]:["customer", "remaining_amt", "items", "pending_bal"]
		for (let key of keys) {
			if(has_common(["items"],[key])) {
				data[key] = JSON.parse(localStorage.getItem(key)) || {}
			}
			else {
				data[key] = localStorage.getItem(key) || ""
			}
		}
		return data
	},

	update_localstorage_data(key, val) {
		var data = this.get_localstorage_data()
		if( key == "items") {
			var items = data["items"]
			if (val.qty == 0) {
				delete items[val.item_code]
			}
			else {
				items[val.item_code] = [val.qty, val.rate, val.amount, val.sales_order, val.is_approved, val.remark]
			}
			localStorage.setItem('items', JSON.stringify(items));
		}
		else {
			localStorage.setItem(key, val);
		}
	}
})