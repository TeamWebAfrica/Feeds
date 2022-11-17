# Copyright (c) 2022, 254 ERP and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class FeedsSettings(Document):

	def before_save(self):
		'''
		Method that runs before a document is saved
		'''
		self.calculate_milling_charge_per_uom()
		self.create_or_update_milling_charge_item()


	def calculate_milling_charge_per_uom(self):
		'''
		Function that calulates the milling charge per UOM based
		on the given Milling Charge per Qty
		'''
		try:
			self.milling_charge_per_uom =  self.milling_charge_per_milling_qty / self.milling_quantity * 1
		except:
			self.milling_charge_per_uom = 0

	def create_or_update_milling_charge_item(self):
		'''
		Methods that create or updates and item that contains the milling
		charge per UOM
		'''
		if not frappe.db.exists("Item","Milling Charge Item Per UoM"):
			milling_charge_doc = frappe.new_doc("Item")
			milling_charge_doc.item_code = "Milling Charge Item Per UoM"
			milling_charge_doc.item_group= "Services"
			milling_charge_doc.stock_uom = self.milling_uom
			milling_charge_doc.standard_rate = self.milling_charge_per_uom
			milling_charge_doc.save()
			frappe.db.commit()
		else:
			milling_charge_doc = frappe.get_doc("Item","Milling Charge Item Per UoM")
			if milling_charge_doc.stock_uom != self.milling_uom:
				milling_charge_doc.stock_uom = self.milling_uom
			milling_charge_doc.save()
			frappe.db.commit()

			similiar_item_prices = frappe.get_list("Item Price", filters = [

				["item_code","=","Milling Charge Item Per UoM"],
				["price_list","=","Standard Selling"],
				["price_list_rate","=",self.milling_charge_per_uom],
				["valid_upto","=", None]
					
				])
			
			print(similiar_item_prices)
			
					 
			
			item_price_doc = frappe.new_doc("Item Price")
			item_price_doc.item_code = "Milling Charge Item Per UoM"
			item_price_doc.price_list = "Standard Selling"
			item_price_doc.rate = self.milling_charge_per_uom
			item_price_doc.save()
			frappe.db.commit()
		
