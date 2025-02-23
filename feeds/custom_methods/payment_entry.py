import frappe

@frappe.whitelist(allow_guest=True)
def filter_payment_modes(doctype, txt, searchfield, start, page_len, filters):
    '''
    Function that filters the different modes of payments for the curent user
    '''
    custom_filters = {}
    if filters.get('user') != 'Administrator':
        custom_filters["user"] = filters.get('user')

    list_of_payments = frappe.get_list("Allowed Payment Roles", 
        filters = custom_filters,
        fields = ['name','parent'],
        ignore_permissions=True
    )

    all_payment_modes = [[mode] for mode in set(map(lambda x: x.get('parent'),list_of_payments))]
    return all_payment_modes

def update_outstanding_amount(doc,event):
    update_outstanding_amount_func(doc.references)

def update_outstanding_amount_func(references):
	for reference in references:
		if reference.reference_doctype == 'Sales Invoice':
			reference_doc = frappe.get_doc("Sales Invoice",reference.reference_name)
			customer_bal = get_customer_outstanding(reference_doc.customer,reference_doc.company,True)
			reference_doc.db_set("outstanding_amount_custom", customer_bal)