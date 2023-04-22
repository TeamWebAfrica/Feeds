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
	step_2:[
		{field_name:'target_warehouse',field_title:'Target Store/Warehouse'},
	],
	step_3:[
		{field_name:'planned_qty',field_title:'Planned Qty'},
		{field_name:'stock_uom',field_title:'Stock UoM'},
		{field_name:'produced_qty',field_title:'Produced Qty'},
	]
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

	select_bom: (frm) => {
		if(frm.doc.select_bom){

			// call the backend function to consolidate BOMs
			frappe.call({
				method: "get_formula_doc",
				doc: frm.doc,
				callback: function(res) {
					console.log(res.message)

					let bom_doc = res.message
					// set BOM UOM and Qty
					cur_frm.set_value("formula_uom",bom_doc.uom)
					cur_frm.set_value("formula_qty",bom_doc.quantity)

					// clear the formual items table
					cur_frm.set_value("formula_materials",[]);

					bom_doc.items.forEach((item) => {
						const row = frm.add_child("formula_materials");
						row.item = item.item_code
						row.required_qty = item.stock_qty
						row.stock_uom = item.stock_uom
						row.rate = item.rate
						row.amount = item.amount
					})

					frm.refresh_field("formula_materials");

				}
			})

		}else{
			// clear all the linked fields
			cur_frm.set_value("formula_materials",[])
			cur_frm.set_value("formula_uom","")
			cur_frm.set_value("formula_qty","")
		}
	},

	// function triggered when confirmed is clicked
	apply_formula: (frm) => {
		// check that all the required fields are given
		let current_step_validation = validate_fields(frm,requiredFieldsObject.step_1)

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
					if(materials_with_shortage[0].item != "MIXING CHARGE"){
						frappe.throw(`There is insufficient '${materials_with_shortage[0].item}' in the '${frm.doc.source_warehouse}' Store/Warehouse`)
					}
				}				

				// confirm the step as complete
				confirm_section_as_complete(frm,"status",'Confirmed')
			}
		});

	},

	// call function that starts production when button is clicked
	initiate_production: (frm) => {
		// check that all the required fields are given
		let current_step_validation = validate_fields(frm,requiredFieldsObject.step_2)

		if(frm.doc.status != 'Confirmed'){
			frappe.throw("This process is only for productions whose status is 'Confirmed'")
		}

		// confirm the step as complete
		confirm_section_as_complete(frm,"status",'WIP')
	},

	// call function that complete production when button is clicked
	complete_production: (frm) => {
		// check that all the required fields are given
		let current_step_validation = validate_fields(frm,requiredFieldsObject.step_3)

		if(frm.doc.status != 'Confirmed'){
			frappe.throw("This process is only for productions whose status is 'Confirmed'")
		}

		// confirm the step as complete
		confirm_section_as_complete(frm,"status",'Completed')
	},

	// function called when a change is made on the uom field
	uom: (frm) => { 
		if(frm.doc.uom != frm.doc.stock_uom ){
			frm.set_value("stock_uom",frm.doc.uom)
		}
	},

	// function called when a change is made on the qty field
	qty: (frm) => { 
		if(frm.doc.qty != frm.doc.planned_qty ){
			frm.set_value("planned_qty",frm.doc.qty)
		}
	},

	// function called when a change is made on the produced Qty field
	planned_qty: (frm) => { 
		if(frm.doc.planned_qty - frm.doc.produced_qty != frm.doc.production_variance ){
			frm.set_value("production_variance",frm.doc.planned_qty - frm.doc.produced_qty)
		}
	},

	// function called when a change is made on the produced Qty field
	produced_qty: (frm) => { 
		if(frm.doc.planned_qty - frm.doc.produced_qty != frm.doc.production_variance ){
			frm.set_value("production_variance",frm.doc.planned_qty - frm.doc.produced_qty)
		}
	}

});
