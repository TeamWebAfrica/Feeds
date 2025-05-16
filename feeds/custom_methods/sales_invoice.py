import frappe,math
from frappe import _
from frappe.utils import flt

def validate(doc,event):
	validate_selling_price(doc)

def before_save(doc,event):
	'''
	Function that runs before saving the sales invoice
	'''
	# Remove unwated fields when user duplicates a an existing invoice
	if not frappe.db.exists("Sales Invoice",doc.name):
		doc.printed = 0

	# calculate correct due amount
	total_due = math.ceil(doc.base_grand_total)
	if doc.total_due != total_due:
		doc.total_due = total_due

	# calculate correct outstanding balance
	updated_outstanding_bal = get_customer_outstanding(doc.customer,doc.company,True)
	if doc.outstanding_amount_custom != updated_outstanding_bal:
		doc.outstanding_amount_custom = updated_outstanding_bal

	# check if user wants to apply advanced payments
	if doc.apply_advanced:
		if len(doc.advances):
			pass
		else:
			doc.apply_advanced = 0
			frappe.throw('Saving stopped <b>Successfully</b> <hr> \
			Go to <b>Payments Section</b> and enter amounts to allocate from Advance payments')

	# check if invoice is updating stock
	if not doc.update_stock:
		doc.update_stock = 1

def on_submit(doc,event):
	'''
	Function that runs when the sales invoice is submitted
	'''
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
def mark_invoice_as_printed_args(*args,**kwargs):
	'''
	Function that marks the gives sales invoice as printed
	'''
	invoice_name = kwargs.get('name')
	return  mark_invoice_as_printed(invoice_name)
	
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
		invoice_doc.db_set("printed", 1)


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


@frappe.whitelist()
def get_user_defaults(user):
	"""
	Fetches both the default warehouse and income account for the given user.
	"""
	default_warehouse = frappe.db.get_value("Default User Warehouse", {"user": user}, "warehouse")
	default_income_account = frappe.db.get_value("Default User Account", {"user": user}, "income_account")

	if not default_warehouse or not default_income_account:
		return {
			"status": False,
			"message": _("You are only allowed to print this invoice once.")
		}

	return {
		"status": True,
		"default_warehouse": default_warehouse,
		"default_income_account": default_income_account
	}

@frappe.whitelist()
def get_default_user_account(user):
	"""
	Fetches only the default income account for the user.
	"""
	income_account = frappe.db.get_value("Default User Account", {"user": user}, "income_account")
	if income_account:
		return {
			"status": True,
			"income_account": income_account
		}
	else:
		return {
			"status": False,
			"message": _("You are only allowed to print this invoice once.")
		}
	
# @frappe.whitelist()
# def get_user_defaults(user):
# 	'''
# 	Function that fetches user defaults based on settings
# 	'''
# 	# get default warehouse
# 	default_warehouse = get_default_user_warehouse(user)
# 	default_income_account = get_default_user_account(user)
# 	# return the defaults
# 	return {
# 		'default_warehouse':default_warehouse,
# 		'default_income_account': default_income_account
# 	}

@frappe.whitelist(allow_guest=True)
def filter_user_income_account(doctype, txt, searchfield, start, page_len, filters):
	"""
	Used in link field query filters to return the default income account for the user.
	"""
	user = filters.get('user')
	result = get_default_user_account(user)

	if result.get('status'):
		return [[result.get('income_account')]]
	return []



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
	invoice = frappe.get_doc("Sales Invoice", sale_invoice_name)
	new_balance = get_customer_outstanding(invoice.customer, invoice.company, True)
	invoice.outstanding_amount_custom = new_balance
	invoice.save()


@frappe.whitelist()
def get_customer_balance(customer,company):
	customer_balance = get_customer_outstanding(customer,company,True)
	return customer_balance

def check_customer_balance(customer):
	pass

def get_item_buying_price(item_code):
	item_price = frappe.db.get_value(
		"Item Price",{
			"price_list": "Standard Buying", 
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

def validate_selling_price(doc):
	'''
	Custom method that validates that the selling price of an item in the sales invoice is 
	greater than the items current buying price
	'''
	if doc.is_return: 
		return
		
	for item in doc.items:	
		# get item buying price
		current_item_details = get_item_buying_price(item.item_code)
		if not current_item_details['status']:
			frappe.throw("Buying price for item {} is not defined".format(item.item_code))

		# define current item price from item details
		current_item_price = current_item_details['amount']
		
		# check if current_item price is less than or equal to selling price
		if current_item_price > item.rate:
			frappe.throw("Selling rate for {} should be atleast {} i.e item's buying price".
			format(item.item_code,current_item_price))