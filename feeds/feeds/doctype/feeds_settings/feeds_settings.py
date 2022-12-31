# Copyright (c) 2022, 254 ERP and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import datetime

class FeedsSettings(Document):

	def before_save(self):
		'''
		Method that runs before a document is saved
		'''
		# self.calculate_mixing_charge_per_uom()
		# self.create_or_update_mixing_charge_item()
		pass
	
	def calculate_mixing_charge_per_uom(self):
		'''
		Function that calulates the mixing charge per UOM based
		on the given Mixing Charge per Qty
		'''
		try:
			self.mixing_charge_per_uom =  self.mixing_charge_per_mixing_qty / self.mixing_quantity * 1
		except:
			self.mixing_charge_per_uom = 0

	def create_or_update_mixing_charge_item(self):
		'''
		Methods that create or updates and item that contains the mixing
		charge per UOM
		'''
		if not frappe.db.exists("Item","Mixing Charge Item Per UoM"):
			mixing_charge_doc = frappe.new_doc("Item")
			mixing_charge_doc.item_code = "Mixing Charge Item Per UoM"
			mixing_charge_doc.item_group= "Services"
			mixing_charge_doc.stock_uom = self.mixing_uom
			mixing_charge_doc.is_stock_item = 0
			mixing_charge_doc.standard_rate = self.mixing_charge_per_uom
			mixing_charge_doc.save()
			frappe.db.commit()
		else:
			mixing_charge_doc = frappe.get_doc("Item","mixing Charge Item Per UoM")
			if mixing_charge_doc.stock_uom != self.mixing_uom:
				mixing_charge_doc.stock_uom = self.mixing_uom
			mixing_charge_doc.save()
			frappe.db.commit()

			similiar_item_prices = frappe.get_list("Item Price", filters = [
				["item_code","=","Mixing Charge Item Per UoM"],
				["price_list","=","Standard Selling"],
				["price_list_rate","=",self.mixing_charge_per_uom],
				["valid_upto","<", '1970-01-01']
			])

			# update item with the same price
			if len(similiar_item_prices):
				name_of_similar_price = similiar_item_prices[0].get('name')
				item_price_doc = frappe.get_doc('Item Price',name_of_similar_price)
				item_price_doc.valid_upto = datetime.datetime.today().date()
				item_price_doc.save()
				frappe.db.commit()

			# create a new item price		
			item_price_doc = frappe.new_doc("Item Price")
			item_price_doc.item_code = "Mixing Charge Item Per UoM"
			item_price_doc.price_list = "Standard Selling"
			item_price_doc.price_list_rate = self.mixing_charge_per_uom
			item_price_doc.save()
			frappe.db.commit()
		
