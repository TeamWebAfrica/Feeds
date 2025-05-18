

def before_save(doc,event):
    '''
    Function that runs before the BOM is saved
    '''
    total_qty = 0
    # caculate the total
    for item in doc.items:
        total_qty += item.qty

    # set total amount
    if doc.total_qty != total_qty:
        doc.total_qty = total_qty