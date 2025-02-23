
def before_save(doc,event):
    '''
    Method that runs before the document is saved
    '''
    if doc.item_group == "Materials" or doc.item_group == "Additives":
        if not doc.is_stock_item:
            doc.is_stock_item = 1
    elif self.item_group == "Formula":
        if self.is_stock_item:
            self.is_stock_item = 0