
def before_save(self):
    total_qty = 0
    # caculate the total
    for item in self.items:
        total_qty += item.qty
    # set total amount
    if self.total_qty != total_qty:
        self.total_qty = total_qty