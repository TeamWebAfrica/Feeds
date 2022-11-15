# Copyright (c) 2022, 254 ERP and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

class FeedsSettings(Document):

	def before_save(self):
		'''
		Method that runs before a document is saved
		'''
		self.calculate_milling_charge_per_uom()


	def calculate_milling_charge_per_uom(self):
		'''
		Function that calulates the milling charge per UOM based
		on the given Milling Charge per Qty
		'''
		try:
			self.milling_charge_per_uom =  self.milling_charge_per_milling_qty / self.milling_quantity * 1
		except:
			self.milling_charge_per_uom = 0
