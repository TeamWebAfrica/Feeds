
def before_save_func(doc,method):
    '''
    Method that runs before the document is saved
    '''
    print('*'*80)
    print("Before Saving")
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