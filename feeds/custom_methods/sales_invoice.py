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


@frappe.whitelist(allow_guest=True)
def filter_user_income_account(doctype, txt, searchfield, start, page_len, filters):
    '''
    Function that filters the different modes of payments for the curent user
    '''
    print("*"*80)
	# get default income account
    user = filters.get('user')
    default_income_account = get_default_user_account(user)
    if(default_income_account.get('status')):
        print(default_income_account)

    return []


    # custom_filters = {}
    # if filters.get('user') != 'Administrator':
    #     custom_filters["user"] = filters.get('user')

    # list_of_payments = frappe.get_list("Allowed Payment Roles", 
    #     filters = custom_filters,
    #     fields = ['name','parent'],
    #     ignore_permissions=True
    # )

    # all_payment_modes = [[mode] for mode in set(map(lambda x: x.get('parent'),list_of_payments))]
    # return all_payment_modes