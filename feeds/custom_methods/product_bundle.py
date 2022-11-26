import frappe,json

def before_save_func(doc,method):
    '''
    Method that runs before the document is saved
    '''
    generate_atomic_items_ratios(doc)

def generate_atomic_items_ratios(doc):
		'''
		Method that gets values from the Items table and create an 
		atomic ratio equivalent for 1kg
		'''
		doc.atomic_items = []
		total_qty = sum([x.qty for x in doc.items])

		for item in doc.items:
			doc.append("atomic_items", {
				'item_code': item.item_code,
				'qty': item.qty/total_qty * 1,
				'description': item.description,
				'rate': item.rate,
				'uom':item.uom
			})

@frappe.whitelist()
def create_bundle_from_formula(formula_details):
	'''
	Function that creates a product bundle using the 
	'''
	formula_details = json.loads(formula_details)
	try:
		# create an product item
		item_doc = frappe.new_doc("Item")
		item_doc.item_code = formula_details.get('formula_name')
		item_doc.item_name = formula_details.get('formula_name')
		item_doc.item_group = 'Materials'
		item_doc.is_stock_item = 0
		item_doc.stock_uom = formula_details.get('stock_uom')
		item_doc.linked_customer = formula_details.get('customer_name')

		# save the item
		item_doc.save()
		frappe.db.commit()
	except:
		return {
			'status':False,
			'message':'Saving item failed'
		}

	try:
		# create a linked product bundle
		product_bundle_doc = frappe.new_doc("Product Bundle")
		product_bundle_doc.new_item_code = formula_details.get('formula_name')
		product_bundle_doc.description = formula_details.get('Fomula product bundle')
		for formula_item in formula_details.get('items'):
			# don not save milling charge as part of the formula
			if formula_item.get('item_code') != 'Milling Charge Item Per UoM':
				product_bundle_doc.append("items",{
					'item_code': formula_item.get('item_code'),
					'qty': formula_item.get('qty'),
					'rate':formula_item.get('rate'),
					'uom': formula_item.get('uom'),
				})


		product_bundle_doc.save()
		frappe.db.commit()
		
		# now save
		return {
				'status':True,
				'message':'Saving Successful'
			}
	except:
		return {
			'status':False,
			'message':'Failed to save formula as product bundle'
		}