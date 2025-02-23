frappe.ui.form.on("Payment Entry", {

    refresh: (frm) => {
        // add filters for modes of payment
		frm.set_query("mode_of_payment", function(doc) {
			return {
				query: 'feeds.custom_methods.payment_entry.filter_payment_modes',
				filters: {
					user: frappe.session.user
				}
			}
		});

		// add button to print sales invoice
		frm.add_custom_button(__('Sales Invoice'), () => {back_to_sales_invoice(frm)})
    },
})

const back_to_sales_invoice = (frm) => {
	let refs = frm.doc.references
	console.log(refs)
	if(refs.length > 0){
		let first_ref = refs[0]
		if(first_ref.reference_doctype == "Sales Invoice"){
			frappe.route_options = {"data_reload": "1"};
			frappe.set_route("Form","Sales Invoice",first_ref.reference_name)
		}else{
			frappe.throw("The defined payment reference is not a Sales Invoice")
		}
	}else{
		frappe.throw("There are no defined payment references")
	}
}