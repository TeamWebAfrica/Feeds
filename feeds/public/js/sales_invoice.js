
frappe.ui.form.on("Sales Invoice", {

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

		// custom code 
		frm.add_custom_button(__('New Invoice'), () => {new_sales_invoice()})

        
    },

    customer_formulas: function(frm) {
            if(frm.doc.customer_formulas){	
                let total_qty = 0
                let total_amt = 0	
                frappe.call({
                    method: "feeds.custom_methods.product_bundle.get_formula_items",
                    args: {
                        "item_code": frm.doc.customer_formulas
                    },
                    callback: function(res) {
                        if (res) {
                            // clear the previous table items
                            cur_frm.set_value("formula_details",[])
    
                            // sort formula in correct order
                            let productBundleItems = res.message.bundle_items
                            let sortedItems = productBundleItems?.sort((a, b) => (a.idx > b.idx ? 1 : -1))
    
                            sortedItems.forEach((item) => {
                                var row = frappe.model.add_child(frm.doc, "Formula Details", "formula_details");
                                row.material = item.item_code;
                                row.qty = item.qty;
                                row.rate = item.rate
                                row.amount = item.qty * item.rate
                                row.description = item.description;
                                row.uom = item.uom;
    
                                if(item.item_code != "MIXING CHARGE"){
                                    total_qty += row.qty
                                }
    
                                total_amt += row.amount
                            })
    
                            frm.set_value("total_amount_formula",total_amt)
                            frm.set_value("total_qty_formula",total_qty)
                            refresh_field('total_amount_formula');
                            refresh_field('total_qty_formula');
                        }
                        refresh_field('formula_details');
                    }
                });
    
            }else{
                // clear the table
                frm.set_value('formula_details',[])
            }
    },

    apply_formula: async (frm) => {
		
		if(!cur_frm.doc.income_account || !cur_frm.doc.set_warehouse){
			frappe.throw("Please select Source Warehouse and Income Account in order to continue.")
		}

		let formulaValues = await  add_formula_details(frm)

		if(formulaValues.qty){

			frm.set_value('items',[])
			let formula_items_qty = (frm.doc.formula_details.map((x) => x.item_code != "MIXING CHARGE" ? x.qty : 0)).reduce((x,y) => x+y,0)
			let total_amount = 0

			// get item from formula tables
			frm.doc.formula_details.forEach((item) => {

				var row = frappe.model.add_child(frm.doc, "Sales Invoice Item", "items");
				row.item_code = item.material;
				row.item_name = item.material;
				row.description = item.material;
				row.description = item.material;

				if(item.material == "MIXING CHARGE"){
					row.qty =  1
					row.uom = "Service Charge";

				}else{
					row.qty =  formulaValues.qty / cur_frm.doc.total_qty_formula * item.qty
				}
				
				row.rate = item.rate;
				row.amount = row.qty * row.rate
				// items below should be modified accordingly hardcode for now
				row.uom = "Kg";
				row.income_account = cur_frm.doc.income_account;
				row.expense_account = "Cost of Goods Sold - GF";
				row.warehouse = cur_frm.doc.set_warehouse;

				// update total
				total_amount += row.amount
				
			}) 

			// set totals
			frm.set_value("total_quantity_custom",formulaValues.qty)
			frm.set_value("base_total",total_amount)
			frm.set_value("base_net_total",total_amount)
			frm.set_value("total",total_amount)
			frm.set_value("net_total",total_amount)

		}
		frm.refresh_fields();
	},

    save_formula: async function(frm) {
		// custom formula to save a new formula 
		if(frm.doc.formula_details.length == 0){
			frappe.throw('You have not added any materials on the formula table.')
		}

		let confirmed_values = await confirm_formula_save(frm)

		// await for formula to save
		let product_bundle_saved = await frappe.call({
			method: 'feeds.custom_methods.product_bundle.create_bundle_from_formula',
			args: {
				formula_details :{
					customer_name: confirmed_values.customer,
					formula_name: confirmed_values.formula_name,
					default_uom: confirmed_values.default_uom,
					items:cur_frm.doc.formula_details
				}
			},
			callback: (res) => {
				return res
			}
		});

		if(product_bundle_saved.message.status){
			frm.set_value('customer_formulas',product_bundle_saved.message.formula)
			frappe.msgprint("Successfully saved formula")
		}else{
			frappe.throw(product_bundle_saved.message.message)
		}

	},


})

// pop up function to allow users to add formula details
const add_formula_details = (frm) => {
	return new Promise(function(resolve, reject) {
		const d = new frappe.ui.Dialog({
			title: 'You selected a Formula.Please Select the required Amount & Quantity Below!',
			fields: [
				{
					label: 'Unit of Measurement(UoM)',
					fieldname: 'uom',
					fieldtype: 'Select',
					default: 'Kg',
					options: ['Kg'],
				},
				{
					label: 'Mixing Charge',
					fieldname: 'mixing_charge',
					fieldtype: 'Select',
					default: 'Yes',
					options: ['Yes','No'],
				},
				{
					label: 'Quantity',
					fieldname: 'qty',
					fieldtype: 'Float',
					default: frm.doc.total_qty_formula
				}
			],
			primary_action_label: 'Submit',
			primary_action(values) {
				d.hide();
				resolve(values);
			}
		});
		// show the dialog box
		d.show()
	})
}

// Functions called on change of formula
frappe.ui.form.on("Formula Details", {
	material: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		frappe.call({
			method: "feeds.custom_methods.sales_invoice.get_item_price",
			args: {
				"item_code": row.material
			},
			callback: function(res) {
				if (res) {
					let price_details = res.message
					if(price_details.status){
						row.qty = 1
						row.rate = price_details.amount
						row.amount = row.qty * row.rate

						// calculate total qty
						let total_qty = 0
						let total_amt = 0
						frm.doc.formula_details.forEach((row) => {
							// exclude amount for mixing charge
							if(row.material != "MIXING CHARGE"){
								total_qty += row.qty
							}
							total_amt += row.amount
						})
						frm.set_value("total_qty_formula",total_qty)
						frm.set_value("total_amount_formula",total_amt)
						frm.refresh_fields();
					}else{
						frappe.throw(`Item price is not defined for ${row.item_code}`)
					}
				}
			}
		});
	}
});

frappe.ui.form.on("Formula Details", {
	qty: function(frm, cdt, cdn) {
		let total_qty = 0
		let total_amt = 0
		frm.doc.formula_details.forEach((row) => {
			row.amount = row.qty * row.rate
			total_qty += row.qty
			total_amt += row.amount
		})
		frm.set_value("total_qty_formula",total_qty)
		frm.set_value("total_amount_formula",total_amt)
		frm.refresh_fields();
	}
});

frappe.ui.form.on("Formula Details", {
	rate: function(frm, cdt, cdn) {
		let total_qty = 0
		let total_amt = 0
		frm.doc.formula_details.forEach((row) => {
			row.amount = row.qty * row.rate
			total_qty += row.qty
			total_amt += row.amount
		})
		frm.set_value("total_qty_formula",total_qty)
		frm.set_value("total_amount_formula",total_amt)
		frm.refresh_fields();
	}
});

// pop up function to allow users to add formula details
const confirm_formula_save = (frm) => {
	return new Promise(function(resolve, reject) {
		const d = new frappe.ui.Dialog({
			title: 'Save the formula.',
			fields: [
				{
					label: 'Customer',
					fieldname: 'customer',
					fieldtype: 'Link',
					options: 'Customer',
					default: frm.doc.customer
				},
				{
					label: 'Formula Name',
					fieldname: 'formula_name',
					fieldtype: 'Data',
					madatory: 1
				},
				{
					label: 'Stock UoM',
					fieldname: 'stock_uom',
					fieldtype: 'Select',
					defualt:'Kg',
					options:['Kg']
				}
			],
			primary_action_label: 'Confirm',
			primary_action(values) {
				if(values.formula_name && values.customer ){
					d.hide();
					resolve(values);
				}else{
					frappe.throw("Customer and Formula name are required to save a new formula.")
				}
			}
		});
		// show the dialog box
		d.show()
	})
}

const new_sales_invoice = () => {
	frappe.set_route("Form", "Sales Invoice","new-sales-invoice-1")
}