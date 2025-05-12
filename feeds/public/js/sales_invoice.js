frappe.ui.form.on("Sales Invoice", {
    refresh: function (frm) {
        // Set query for customer formulas
        frm.set_query("customer_formulas", () => {
            if (!frm.doc.customer) {
                frappe.throw(__('Please select a customer'));
            }
            return {
                filters: {
                    'linked_customer': frm.doc.customer
                }
            };
        });

        // Get user defaults
        frappe.call({
            method: "feeds.custom_methods.sales_invoice.get_user_defaults",
            args: {
                user: frappe.session.user
            },
            callback(res) {
                if (res.message.default_warehouse.status) {
                    frm.set_value("set_warehouse", res.message.default_warehouse.warehouse);
                }
                if (res.message.default_income_account.status) {
                    frm.set_value("income_account", res.message.default_income_account.income_account);
                }
            }
        });

        // Button to update outstanding balance
        frm.add_custom_button(__('Update Balance'), () => {
            frappe.call({
                method: "feeds.custom_methods.sales_invoice.update_outstanding_bal",
                args: {
                    sale_invoice_name: frm.doc.name
                },
                callback: function () {
                    frm.refresh_fields();
                }
            });
        });
    },

    customer: function (frm) {
        if (!frm.doc.customer || !frm.doc.posting_date) return;

        frappe.call({
            method: "erpnext.accounts.utils.get_balance_on",
            args: {
                date: frm.doc.posting_date,
                party_type: 'Customer',
                party: frm.doc.customer
            },
            callback: function (r) {
                frm.set_value("outstanding_balance", parseFloat(r.message));
                frm.refresh_field("outstanding_balance");
            }
        });
    },

    customer_formulas: function (frm) {
        if (!frm.doc.customer_formulas) {
            frm.set_value("formula_details", []);
            return;
        }

        frappe.call({
            method: "feeds.custom_methods.product_bundle.get_formula_items",
            args: {
                item_code: frm.doc.customer_formulas
            },
            callback: function (res) {
                if (!res || !res.message) return;

                let sortedItems = (res.message.bundle_items || []).sort((a, b) => a.idx - b.idx);
                let total_qty = 0;
                let total_amt = 0;

                frm.clear_table("formula_details");

                sortedItems.forEach(item => {
                    let row = frm.add_child("formula_details");
                    row.material = item.item_code;
                    row.qty = item.qty;
                    row.rate = item.rate;
                    row.amount = item.qty * item.rate;
                    row.description = item.description;
                    row.uom = item.uom;

                    if (item.item_code !== "MIXING CHARGE") {
                        total_qty += item.qty;
                    }
                    total_amt += row.amount;
                });

                frm.set_value("total_amount_formula", total_amt);
                frm.set_value("total_qty_formula", total_qty);
                frm.refresh_fields();
            }
        });
    },

    apply_formula: async function (frm) {
        if (!frm.doc.income_account || !frm.doc.set_warehouse) {
            frappe.throw("Please select Source Warehouse and Income Account in order to continue.");
        }

        let formulaValues = await add_formula_details(frm);
        if (!formulaValues.qty) return;

        frm.clear_table("items");
        let formula_items_qty = (frm.doc.formula_details.map((x) => x.item_code != "MIXING CHARGE" ? x.qty : 0)).reduce((x,y) => x+y,0)
        let total_amount = 0;

        frm.doc.formula_details.forEach(item => {
            let row = frm.add_child("items");
            row.item_code = item.material;
            row.item_name = item.material;
            row.description = item.material;

            if (item.material === "MIXING CHARGE") {
                row.qty = 1;
                row.uom = "Service Charge";
            } else {
                row.qty = (formulaValues.qty / formula_items_qty) * item.qty;
                row.uom = "Kg";
            }

            row.rate = item.rate;
            row.amount = row.qty * row.rate;
            row.income_account = frm.doc.income_account;
            row.expense_account = "Cost of Goods Sold - GF";
            row.warehouse = frm.doc.set_warehouse;

            total_amount += row.amount;
        });

        frm.set_value("total_quantity_custom", formulaValues.qty);
        frm.set_value("base_total", total_amount);
        frm.set_value("base_net_total", total_amount);
        frm.set_value("total", total_amount);
        frm.set_value("net_total", total_amount);
        frm.set_value("custom_rounded_total", total_amount);
        frm.refresh_fields();
    },

    save_formula: async function (frm) {
        if ((frm.doc.formula_details || []).length === 0) {
            frappe.throw('You have not added any materials on the formula table.');
        }

        const confirmed_values = await confirm_formula_save(frm);

        let result = await frappe.call({
            method: 'feeds.custom_methods.product_bundle.create_bundle_from_formula',
            args: {
                formula_details: {
                    customer_name: confirmed_values.customer,
                    formula_name: confirmed_values.formula_name,
                    default_uom: confirmed_values.default_uom,
                    items: frm.doc.formula_details
                }
            }
        });

        const res = result.message;
        if (res.status) {
            frm.set_value('customer_formulas', res.formula);
            frappe.msgprint("Successfully saved formula");
        } else {
            frappe.throw(res.message);
        }
    },

    items_add(frm, cdt, cdn) {
        if (!frm.doc.income_account) {
            frm.set_value("items", []);
            frappe.throw("Please select Income Account in order to continue");
        }

        let row = frappe.get_doc(cdt, cdn);
        frm.script_manager.copy_from_first_row("items", row, ["income_account", "discount_account", "cost_center"]);
        row.income_account = frm.doc.income_account;
        row.expense_account = "Cost of Goods Sold - GF";
    }
});

// --- Utility Dialog Functions ---

const add_formula_details = (frm) => {
    return new Promise((resolve) => {
        const d = new frappe.ui.Dialog({
            title: 'You selected a Formula. Please Select the required Amount & Quantity Below!',
            fields: [
                {
                    label: 'Unit of Measurement(UoM)',
                    fieldname: 'uom',
                    fieldtype: 'Select',
                    default: 'Kg',
                    options: ['Kg']
                },
                {
                    label: 'Mixing Charge',
                    fieldname: 'mixing_charge',
                    fieldtype: 'Select',
                    default: 'Yes',
                    options: ['Yes', 'No']
                },
                {
                    label: 'Quantity',
                    fieldname: 'qty',
                    fieldtype: 'Float',
                    default: frm.doc.total_qty_formula
                },
                {
                    label: 'Amount',
                    fieldname: 'amount',
                    fieldtype: 'Currency',
                    default: frm.doc.total_amount_formula
                }
            ],
            primary_action_label: 'Submit',
            primary_action(values) {
                d.hide();
                resolve(values);
            }
        });
        d.show();
    });
};

const confirm_formula_save = (frm) => {
    return new Promise((resolve) => {
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
                    reqd: 1
                },
                {
                    label: 'Default UoM',
                    fieldname: 'default_uom',
                    fieldtype: 'Select',
                    options: ['Kg'],
                    default: 'Kg'
                }
            ],
            primary_action_label: 'Save',
            primary_action(values) {
                d.hide();
                resolve(values);
            }
        });
        d.show();
    });
};

// --- Formula Details Child Table Events ---

frappe.ui.form.on("Formula Details", {
    material(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        frappe.call({
            method: "feeds.custom_methods.sales_invoice.get_item_price",
            args: { item_code: row.material },
            callback(res) {
                if (res && res.message && res.message.status) {
                    row.qty = 1;
                    row.rate = res.message.amount;
                    row.amount = row.qty * row.rate;
                    recalculate_formula_totals(frm);
                } else {
                    frappe.throw(`Item price is not defined for ${row.material}`);
                }
            }
        });
    },
    qty(frm) {
        recalculate_formula_totals(frm);
    },
    rate(frm) {
        recalculate_formula_totals(frm);
    }
});

const recalculate_formula_totals = (frm) => {
    let total_qty = 0;
    let total_amt = 0;

    (frm.doc.formula_details || []).forEach(row => {
        row.amount = row.qty * row.rate;
        if (row.material !== "MIXING CHARGE") {
            total_qty += row.qty;
        }
        total_amt += row.amount;
    });

    frm.set_value("total_qty_formula", total_qty);
    frm.set_value("total_amount_formula", total_amt);
    frm.refresh_field("formula_details");
};

frappe.ui.form.on("Sales Invoice", {
	refresh(frm) {
		calculate_total_amount(frm);
	}
});

frappe.ui.form.on("Sales Invoice Item", {
	rate: trigger_total,
	qty: trigger_total,
	item_code: trigger_total,
	items_on_form_rendered: trigger_total,
	items_remove: trigger_total
});

function trigger_total(frm, cdt, cdn) {
	calculate_total_amount(frm);
}

function calculate_total_amount(frm) {
	const total = (frm.doc.items || []).reduce((sum, row) => sum + flt(row.amount), 0);
	const rounded_total = Math.round(total);
	frm.set_value("custom_rounded_total", rounded_total);
}
