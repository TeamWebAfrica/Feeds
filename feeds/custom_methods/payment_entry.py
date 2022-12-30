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