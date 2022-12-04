// Copyright (c) 2022, 254 ERP and contributors
// For license information, please see license.txt

// global variables
let requiredFieldsObject = {
	step_1:[
		{field_name:'select_bom',field_title:'Select Formula (BOM)'},
		{field_name:'uom',field_title:'UoM'},
		{field_name:'qty',field_title:'Qty'},
		{field_name:'source_warehouse',field_title:'Source Store/Warehouse'}
	],
}

// create a function that verifies that all the required fields are given
const validate_fields = (frm,listOfFields) => {
	let [final_status,message] = [true,""]
	// loop through the list of custom fields
	listOfFields.forEach((x) => {
		if(x.type == 'table'){
			// check that the table has rows
			if(frm.doc[x.field_name].length == 0){
				final_status = false
				message = `${x.field_title} is a required field.`
			}
		}else{
			// check that the fields are given
			if(!frm.doc[x.field_name]){
				final_status = false
				message = `${x.field_title} is a required field.`
			}
		}		
	})
	// return based on the message
	if(!final_status){
		frappe.throw(message)
	}
}

// function that confirms a section as complete and saves
const confirm_section_as_complete = (frm,field_to_mark,mark_value) => {
	frm.set_value(field_to_mark,mark_value)
	frm.save()
}


frappe.ui.form.on('Production', {
	refresh: function(frm) {

	},

	// function triggered when confirmed is clicked
	confirm: (frm) => {
		// check that all the required fields are given
		let current_step_validation = validate_fields(frm,requiredFieldsObject.step_1)
		// validate fields and confirm as complete

		// call the backend function to consolidate BOMs
		frappe.call({
			method: "get_required_raw_materials",
			doc: frm.doc,
			callback: function(response) {
				let res = response.message
				if(!res.status){
					frappe.throw(res.message)
				}

				// refresh_field("sales_orders");
				refresh_field('required_materials_table');

				// check table is not empty
				let rqd_materials = frm.doc.required_materials_table
				if(!rqd_materials.length){
					frappe.throw("You do not have any items in the required items table.")
				}

				// check for shortage
				let materials_with_shortage = rqd_materials.filter((item) => item.qty_shortage)
				if(materials_with_shortage.length){
					frappe.throw(`There is insufficient '${materials_with_shortage[0].item}' in the '${frm.doc.source_warehouse}' Store/Warehouse`)
				}

				// confirm the step as complete
				confirm_section_as_complete(frm,"status",'Confirmed')
			}
		});


	},
});
