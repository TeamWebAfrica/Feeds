# Copyright (c) 2022, 254 ERP and contributors
# For license information, please see license.txt

import frappe,json
from frappe.model.document import Document

class Production(Document):

	def before_save(self):
		'''
		Function that runs before the document is saved
		'''
		# add the UoM and Qty
		if self.uom != self.stock_uom or self.qty != self.planned_qty:
			self.stock_uom = self.uom
			self.planned_qty = self.qty

		if self.planned_qty - self.produced_qty == self.production_variance:
			self.production_variance = self.planned_qty - self.produced_qty

		# move the stock from one warehouse to the other
		if self.status == "Completed":
			self.complete_packed_products_transfer()

	@frappe.whitelist()
	def get_formula_doc(self):
		return frappe.get_doc("BOM",self.select_bom)
			

	@frappe.whitelist()
	def get_required_raw_materials(self):
		"""
		Gets required raw materials based on BOM and Qty
		"""
		# get required items based on BOM and Qty
		raw_materials = get_items_list_given_bom_n_qty(self)
		if not raw_materials.get('status'):
			return raw_materials
	
		# clear the table before re-appending
		self.required_materials_table = []
		# now add the items to the table
		for item in raw_materials.get('value'):
			# determine the amount available in the warehouse
			stock_result = get_bin_details_twb(self.source_warehouse,item.get('bom_item'))
			if len(stock_result):
				available_stock = stock_result[0].get('actual_qty')
				# now append the correct items and quatities
				self.append(
					"required_materials_table",
					{
						"item": item.get('bom_item'),
						"stock_qty": available_stock,
						"required_qty": item.get('qty'),
						"qty_shortage": available_stock - item.get('qty') * -1 if (available_stock - item.get('qty')) < 0 else 0
					}
				)
			else:
				self.append(
					"required_materials_table",
					{
						"item": item.get('bom_item'),
						"stock_qty": 0,
						"required_qty": item.get('qty'),
						"qty_shortage": item.get('qty') * -1
					}
				)
		
		# return true to end execuation
		return {'status':True}

	def complete_packed_products_transfer(self):
		"""
		Function that moves the materials from stock to finished goods warehouse
		"""
		#creat new stock entry
		repack_doc = frappe.new_doc("Stock Entry")
		repack_doc.stock_entry_type = "Repack"

		# build transfer items
		for item in self.required_materials_table:			
			repack_doc.append("items",{
				"s_warehouse": self.source_warehouse,
				"t_warehouse": "",
				"item_code": item.item,
				"qty": item.required_qty
			})

		# get item linked to BOM
		bom_doc = frappe.get_doc("BOM",self.select_bom)

		# add the target finished product
		repack_doc.append("items",{
				"s_warehouse": "",
				"t_warehouse": self.target_warehouse,
				"item_code": bom_doc.item,
				"qty": self.produced_qty
			})

		# insert the data in the database and submit		
		repack_doc.insert(ignore_permissions=True)
		repack_doc.submit()		
		frappe.db.commit()	


def get_items_list_given_bom_n_qty(self):
	'''
	Function that returns items list given bom_name and 
	qty
	input:
		str - bom_name
		qty - int
	output:
		list - dough_list (with items and qty)
	'''
	# get BOM document
	bom_doc = frappe.get_doc("BOM",self.select_bom)

	# get all the dough items required for this BOM
	bom_items_list = bom_doc.items
	if not len(bom_items_list):
		return {
			'status': False,
			'message':"Materials not defined for BOM:'{}'".format(self.select_bom)
		}

	# initialize conversion factore as 1
	conversion_factor_value = 1 

	if self.formula_uom != self.formula_uom:
		# find conversion factor from given qty to stock qty
		bom_uom_conversion = frappe.get_list("UOM Conversion Factor",
				filters={
					'from_uom':self.formula_uom,
					'to_uom': self.uom
				},
				fields=['name', 'value']
			)


		if not len(bom_uom_conversion):
			return {
				'status': False,
				'message':"A conversion factor from '{}' to '{}' is not defined".format(self.formula_uom,self.uom)
			}
	
		# conversion factor from the UOM indicated in production to BOM UoM
		conversion_factor_value = bom_uom_conversion[0].get('value')	

	# determine share ratio assumign we are using Kgs only
	total_bom_qty = self.formula_qty * conversion_factor_value
	share_ratio = self.qty / total_bom_qty

	items_list = [] #initialize as empty
	for bom_item in bom_items_list: 
		items_list.append({ 
			'bom_item':bom_item.item_code,
			'qty': bom_item.qty * share_ratio
		})

	# return the full dough list
	return {
		'status': True,
		'value': items_list
	}
	

@frappe.whitelist()
def get_bin_details_twb(warehouse, item_code):
    '''
    Function that determines the stock balance of an item in the warehouses
    '''
    # format the sql query here
    sql_string = """ select ifnull(sum(projected_qty),0) as projected_qty,
        ifnull(sum(actual_qty),0) as actual_qty, ifnull(sum(ordered_qty),0) as ordered_qty,
        ifnull(sum(reserved_qty_for_production),0) as reserved_qty_for_production, warehouse,
        ifnull(sum(planned_qty),0) as planned_qty
        from `tabBin` where item_code = '{}' and warehouse = '{}' group by item_code, warehouse
    """.format(item_code, warehouse)
    # return the result of the query as a dictionary
    return frappe.db.sql(sql_string, as_dict=1)


       
