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

@frappe.whitelist()
def get_default_user_account(user):
	'''
	Function that gets the default income account for the currently logged in user
	'''
	income_accounts = frappe.db.get_list("Default User Account",
		filters={
			'user': user,
		},
		fields=['*'],
		ignore_permissions=True
	)

	if len(income_accounts):
		return {
			'status': True,
			'income_account':income_accounts[0].get('income_account')
		}		
	else:
		return {
			'status': False,
			'message': "You are only allowed to print this invoice once."
		}
	

@frappe.whitelist()
def get_user_defaults(user):
	'''
	Function that fetches user defaults based on settings
	'''
	# get default warehouse
	default_warehouse = get_default_user_warehouse(user)
	default_income_account = get_default_user_account(user)
	# return the defaults
	return {
		'default_warehouse':default_warehouse,
		'default_income_account': default_income_account
	}
