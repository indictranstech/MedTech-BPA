frappe.pages['payment-allocation'].on_page_load = function(wrapper) {
	new frappe.payment_allocation({
		$wrapper: $(wrapper)
	});
	//frappe.breadcrumbs.add("MedTech-BPA");
}

frappe.payment_allocation = Class.extend({
	init: function(opts) {
		this.$wrapper = opts.$wrapper
		this.make();
	},

	make: function() {
		this.$wrapper.empty();
		this.$wrapper.append(frappe.render_template("payment_allocation_layout"));
		this.clear_localstorage();
		this.fetch_pending_so();
		//this.update_localstorage_data("remaining_amt", 1000)
	},

	clear_localstorage: function() {
		//clear localStorage
		keys = ["items", "remaining_amt"]
		$.each(keys, function(i, key) {
			localStorage.removeItem(key);
		})
	},

	fetch_pending_so: function() {
		var me = this;
		frappe.call({
			method: "medtech_bpa.medtech_bpa.page.payment_allocation.payment_allocation.get_pending_so",
			args: frappe.route_options,
			callback: function(r) {
				if(!r.exc) {
					$('.item-tbl').html(frappe.render_template("so_item_list", {
						"data": r.message
					}))

					me.update_localstorage_data("customer", r.message.customer)
					me.update_localstorage_data("remaining_amt", r.message.closing_bal)
					me.update_qty();
					me.approval_check();
					me.update_remark();
					me.save_doc();
					me.refresh_doc();
				}
				else {
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
			var curr_amount = flt($(this).closest('tr').find('.pa-amt').text() || 0);
			var remaining_amt = me.get_localstorage_data("remaining_amt")["remaining_amt"] || 0

			if(!pa_qty || pa_qty < 0) {
				var is_update_needed = false
				this.value = 0
				var pa_qty = 0
				var amount = 0
				var remaining_amt = flt(remaining_amt) + flt(curr_amount)
				$(this).closest('tr').find('.is_approved').prop("checked", false);
			}

			var rate = $(this).closest('tr').find('.rate').attr('data-soi-rate').trim();
			var qty = $(this).closest('tr').find('.soi-qty').attr('data-soi-qty').trim();
			var amount = flt(rate) * cint(pa_qty)

			// validate original qty
			if((cint(pa_qty) > cint(qty))) {
				this.value = 0
				var remaining_amt = flt(remaining_amt) + flt(curr_amount)
				$(this).closest('tr').find('.pa-amt').text(0.00)
				frappe.msgprint(__("Qty is exceeding original Qty"))
			}

			// validate amount limit
			else if(remaining_amt - amount < 0) {
				this.value = 0
				var remaining_amt = flt(remaining_amt) + flt(curr_amount)
				$(this).closest('tr').find('.pa-amt').text(0.00)
				frappe.msgprint(__("Exceeding Amount Limit"))
			}
			else if (!is_update_needed) {
				$(this).closest('tr').find('.pa-amt').text(amount)
				var remaining_amt = flt(remaining_amt) - flt(amount)
			}
			
			var qty = $(this).closest('tr').find('.pa-qty').val();
			var item_code = $(this).closest('tr').find('.soi-code').attr('data-soi-code').trim();
			var amount = flt($(this).closest('tr').find('.pa-amt').text() || 0);
			var sales_order = $(this).closest('tr').find('.so-name').attr('data-so').trim();
			var is_approved = $(this).closest('tr').find('.is_approved').prop("checked");
			var remark = $(this).closest('tr').find('.pa-remark').val().trim();
			$('.pending_amt').html("<b>Pending Balance:  </b>"+remaining_amt)
			
			//update localstorage
			me.update_localstorage_data("remaining_amt", remaining_amt)
			me.update_localstorage_data("items", {
				"item_code": item_code,
				"qty": cint(qty),
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
			var amount = flt($(this).closest('tr').find('.pa-amt').text() || 0);
			var qty = $(this).closest('tr').find('.pa-qty').val();
			var is_approved = $(this).closest('tr').find('.is_approved').prop("checked");
			me.update_localstorage_data("items", {
				"item_code": item_code,
				"qty": cint(qty),
				"amount": flt(amount),
				"sales_order": sales_order,
				"is_approved": is_approved,
				"remark": remark
			})
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
					method: "medtech_bpa.medtech_bpa.page.payment_allocation.payment_allocation.save_payment_allocation",
					args: {"data": data},
					async: false,
					callback: function(r) {
						if(!r.exc) {
							frappe.msgprint(__("Payment Allocation Saved Successfully ..."))
						}
					}
				})
			}
		})
	},

	refresh_doc: function() {
		var me = this;
		$('.refresh_doc').on("click", function() {
			//me.clear_localstorage();
			me.make();
		})
	},

	get_localstorage_data: function(key=false) {
		data = {}
		let keys = key ? [key]:["customer", "remaining_amt", "items"]
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
		console.log("update_localstorage_data", key, val)
		var data = this.get_localstorage_data()
		if( key == "items") {
			var items = data["items"]
			if (val.qty == 0) {
				delete items[val.item_code]
			}
			else {
				items[val.item_code] = [val.qty, val.amount, val.sales_order, val.is_approved, val.remark]
			}
			localStorage.setItem('items', JSON.stringify(items));
		}
		else {
			localStorage.setItem(key, val);
		}
	}
})	