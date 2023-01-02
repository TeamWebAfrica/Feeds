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
def print_allowed(name,user):
	invoice_doc = frappe.get_doc("Sales Invoice",name)
	if invoice_doc.printed:
		# check if user has permissions
		print_users = frappe.db.get_list("Print Users",
			filters={
				'user': user,
			},
			fields=['*'],
			ignore_permissions=True
		)

		if user == "Administrator" or len(print_users):
			return {'status': True}
		else:
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

@frappe.whitelist()
def get_default_user_warehouse(user):
	'''
	Function that gets the default warehouse for the currently logged in
	'''
	user_warehouses = frappe.db.get_list("Default User Warehouse",
		filters={
			'user': user,
		},
		fields=['*'],
		ignore_permissions=True
	)

	if len(user_warehouses):
		return {
			'status': True,
			'warehouse':user_warehouses[0].get('warehouse')
		}		
	else:
		return {
			'status': False,
			'message': "You are only allowed to print this invoice once."
		}
	