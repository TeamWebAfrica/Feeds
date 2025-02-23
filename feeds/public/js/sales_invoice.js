
frappe.ui.form("Sales Invoice", {
    refresh: (frm) => {

        // set quety for customer formulas
        frm.set_query("customer_formulas", function(doc) {
            if(!frm.doc.customer) {
                frappe.throw(_('Please select a customer'));
            }

            return {
                filters: {
                    'linked_customer': frm.doc.customer
                }
            }
        });

        
    }
})