import frappe

def add_customer_to_product_bundle():
    '''
    Function that loops through all the product bundles and updates them using 
    customer in the linked item
    '''
    list_of_items = frappe.get_list("Item",fields = ['name','linked_customer'])
    for item in list_of_items:
        try:
            bundle_doc = frappe.get_doc("Product Bundle",item.get('name'))
            bundle_doc.linked_customer = item.get('linked_customer')
            bundle_doc.save()
            frappe.db.commit()
        except:
            pass


                

