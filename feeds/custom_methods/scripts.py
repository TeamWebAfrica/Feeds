import frappe

def add_customer_to_product_bundle():
    '''
    Function that loops through all the product bundles and updates them using 
    customer in the linked item
    '''
    print("Linking customer to invoices")
    list_of_items = frappe.get_list("Item")
    print(list_of_items)

