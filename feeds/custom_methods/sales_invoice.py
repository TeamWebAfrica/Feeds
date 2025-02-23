import frappe,math
from frappe.utils import flt
from erpnext.accounts.utils import get_balance_on

def before_save(doc,event):
	'''
	Function that runs before saving the sales invoice
	'''
	# calculate correct due amount
	total_due = math.ceil(doc.base_grand_total)
	if doc.total_due != total_due:
		doc.total_due = total_due

	# calculate correct outstanding balance
	updated_outstanding_bal = get_customer_outstanding(doc.customer,doc.company,True)
	if doc.outstanding_amount_custom != updated_outstanding_bal:
		doc.outstanding_amount_custom = updated_outstanding_bal

def on_submit(doc,event):
	# updating outstanding amount
	update_outstanding_bal(doc.name)

	# force reload the document
	frappe.reload_doc("Accounts", "Sales Invoice", doc.name)

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
	# counter check customer balance
	correct_balance = counter_balance(invoice_doc)
	if not correct_balance.get('status'):
		return {
			'status': correct_balance.get('status'),
			'message': correct_balance.get('message')
		}

	if invoice_doc.printed:
		# check if user has permissions
		print_users = frappe.db.get_list("Print Users",
			filters={
				'user': user,
			},
			fields=['*'],
			ignore_permissions=True
		)

		if len(print_users) or frappe.session.user == 'Administrator':
			return {'status': True}
		else:
			return {
				'status': False,
				'message': "You are not allowed to print invoice more than once."
			}
	else:
		return {
			'status': True,
		}

@frappe.whitelist()
def mark_invoice_as_printed(sales_invoice):
	'''
	Function that marks the gives sales invoice as printed
	'''
	invoice_doc = frappe.get_doc("Sales Invoice",sales_invoice)
	# counter check customer balance
	correct_balance = counter_balance(invoice_doc)

	allow_printing = True
	message = ""

	if not correct_balance.get('status'):
		allow_printing = correct_balance.get('status'),
		message =  correct_balance.get('message')

		return {'status':False,'message':message}
	

	if invoice_doc.printed:
		# check if user has permissions
		print_users = frappe.db.get_list("Print Users",
			filters={
				'user': frappe.session.user
			},
			fields=['*'],
			ignore_permissions=True
		)

		if len(print_users) or frappe.session.user == 'Administrator':
			return {'status': True}
		else:
			allow_printing = False
			message =  "You are not allowed to print invoice more than once"

			return {'status':allow_printing,'message':message}
	else:
		# mark invoice as printed
		invoice_doc.printed = 1
		invoice_doc.save()
		frappe.db.commit()

	# return status and message
	return {'status':allow_printing,'message':message}


def counter_balance(doc):
	'''
	Function that checks that the current balance o sales invoice matches the customers
	outstanding balance for the customer is the correct
	balance 
	'''
	customer_balance = get_customer_outstanding(doc.customer,"Glen Feeds",True)
	if doc.outstanding_amount_custom == customer_balance:
		return {'status':True}
	else:
		return {
			'status':False,
			'message': 'Oustanding balance on sales invoice does not match current customer balance.'
		}


	frappe.throw("Pause")

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

def get_customer_outstanding(
	customer, company, ignore_outstanding_sales_order=False, cost_center=None
):
	# Outstanding based on GL Entries

	cond = ""
	if cost_center:
		lft, rgt = frappe.get_cached_value("Cost Center", cost_center, ["lft", "rgt"])

		cond = """ and cost_center in (select name from `tabCost Center` where
			lft >= {0} and rgt <= {1})""".format(
			lft, rgt
		)

	outstanding_based_on_gle = frappe.db.sql(
		"""
		select sum(debit) - sum(credit)
		from `tabGL Entry` where party_type = 'Customer'
		and party = %s and company=%s {0}""".format(
			cond
		),
		(customer, company),
	)

	outstanding_based_on_gle = flt(outstanding_based_on_gle[0][0]) if outstanding_based_on_gle else 0

	# Outstanding based on Sales Order
	outstanding_based_on_so = 0

	# if credit limit check is bypassed at sales order level,
	# we should not consider outstanding Sales Orders, when customer credit balance report is run
	if not ignore_outstanding_sales_order:
		outstanding_based_on_so = frappe.db.sql(
			"""
			select sum(base_grand_total*(100 - per_billed)/100)
			from `tabSales Order`
			where customer=%s and docstatus = 1 and company=%s
			and per_billed < 100 and status != 'Closed'""",
			(customer, company),
		)

		outstanding_based_on_so = flt(outstanding_based_on_so[0][0]) if outstanding_based_on_so else 0

	# Outstanding based on Delivery Note, which are not created against Sales Order
	outstanding_based_on_dn = 0

	unmarked_delivery_note_items = frappe.db.sql(
		"""select
			dn_item.name, dn_item.amount, dn.base_net_total, dn.base_grand_total
		from `tabDelivery Note` dn, `tabDelivery Note Item` dn_item
		where
			dn.name = dn_item.parent
			and dn.customer=%s and dn.company=%s
			and dn.docstatus = 1 and dn.status not in ('Closed', 'Stopped')
			and ifnull(dn_item.against_sales_order, '') = ''
			and ifnull(dn_item.against_sales_invoice, '') = ''
		""",
		(customer, company),
		as_dict=True,
	)

	if not unmarked_delivery_note_items:
		return outstanding_based_on_gle + outstanding_based_on_so

	si_amounts = frappe.db.sql(
		"""
		SELECT
			dn_detail, sum(amount) from `tabSales Invoice Item`
		WHERE
			docstatus = 1
			and dn_detail in ({})
		GROUP BY dn_detail""".format(
			", ".join(frappe.db.escape(dn_item.name) for dn_item in unmarked_delivery_note_items)
		)
	)

	si_amounts = {si_item[0]: si_item[1] for si_item in si_amounts}

	for dn_item in unmarked_delivery_note_items:
		dn_amount = flt(dn_item.amount)
		si_amount = flt(si_amounts.get(dn_item.name))

		if dn_amount > si_amount and dn_item.base_net_total:
			outstanding_based_on_dn += (
				(dn_amount - si_amount) / dn_item.base_net_total
			) * dn_item.base_grand_total

	return outstanding_based_on_gle + outstanding_based_on_so + outstanding_based_on_dn

@frappe.whitelist()
def update_outstanding_bal(sale_invoice_name):
	'''
	Function that automatically updates the correct customer outstanding balance in sales invoice
	'''
	invoice_doc = frappe.get_doc("Sales Invoice",sale_invoice_name)
	# now get correct customer outstanding balance
	customer_balance = get_customer_outstanding(invoice_doc.customer,invoice_doc.company,True)

	if customer_balance != invoice_doc.outstanding_amount_custom:
		invoice_doc.db_set("outstanding_amount_custom", customer_balance)

	return {
		'status':True
	}

@frappe.whitelist()
def get_customer_balance(customer,company):
	customer_balance = get_customer_outstanding(customer,company,True)
	return customer_balance

def check_customer_balance(customer):
	pass