import frappe

@frappe.whitelist()
def get_item_price(item_code):
	item_price = frappe.db.get_value(
		"Item Price",{
			"price_list": "Standard Selling", 
			"item_code": item_code
		},
		["price_list_rate", "currency"]
	)
	if item_price:
		return {
			'status': True,
			'amount':item_price[0],
			'currency':item_price[1]
		}
	else:
		return {
			'status': False
		}

@frappe.whitelist()
def print_allowed(name):
	invoice_doc = frappe.get_doc("Sales Invoice",name)
	if invoice_doc.printed:
		# check if user has permissions
		return {
			'status': False,
			'message': "You are only allowed to print this invoice once."
		}
	else:
		# mark the invoice as printed
		invoice_doc.printed = 1
		invoice_doc.save()
		frappe.db.commit()

		return {
			'status': True,
		}

	