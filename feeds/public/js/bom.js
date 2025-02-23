frappe.ui.form.on("BOM", {


    
})

frappe.ui.form.on("BOM Item", "qty", function(frm, cdt, cdn) {
	// calculate total qty
	calculate_total()

	var d = locals[cdt][cdn];
	d.stock_qty = d.qty * d.conversion_factor;
	refresh_field("stock_qty", d.name, d.parentfield);
});

frappe.ui.form.on("BOM Item", "item_code", function(frm, cdt, cdn) {
	// calculate total qty
	calculate_total()

	var d = locals[cdt][cdn];
	frappe.db.get_value('Item', {name: d.item_code}, 'allow_alternative_item', (r) => {
		d.allow_alternative_item = r.allow_alternative_item
	})
	refresh_field("allow_alternative_item", d.name, d.parentfield);
});

const calculate_total = () => {
	let items = cur_frm.doc.items

	let total_qty = 0
	cur_frm.doc.items.forEach((x) => {
		if(x.qty){
			total_qty += parseFloat(x.qty)
		}else{
			total_qty += 1
		}
	})

	cur_frm.set_value("total_qty",total_qty)
	refresh_field("total_qty");
}