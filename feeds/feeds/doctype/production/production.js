// Copyright (c) 2022, 254 ERP and contributors
// For license information, please see license.txt

// global variables
let requiredFieldsObject = {
	step_1:[
		{field_name:'select_bom',field_title:'Select Formula (BOM)'},
		{field_name:'uom',field_title:'UoM'},
		{field_name:'qty',field_title:'Qty'},
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
	if(final_status){
		return {status:final_status}
	}else{
		return {status:final_status,message:message}
	}
}

// function that confirms a section as complete
const confirm_section_as_complete = (frm,fields_valid_step,field_to_mark,mark_value) => {
	if(fields_valid_step.status){
		field_to_mark ? frm.set_value(field_to_mark,mark_value) : 'pass';
		// add a save functionality below
		frm.save()
		// return status as true
		return {status:true}
	}else{
		// if any of them is missing throw an error message
		frappe.throw(fields_valid_step.message)
	}
}


frappe.ui.form.on('Production', {
	refresh: function(frm) {

	},

	// function triggered when confirmed is clicked
	confirm: (frm) => {
		// check that all the required fields are given
		let current_step_validation = validate_fields(frm,requiredFieldsObject.step_1)
		// validate fields and confirm as complete
		let fields_confirmed = confirm_section_as_complete(frm,current_step_validation,"status",'Confirmed')
		// now pull the required items
		// if(fields_confirmed.status){

		// }
		
	},
});
