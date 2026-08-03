class Ticket:
    def __init__(self, weekend, child):
       
        self.weekend = weekend
        self.child = child
       
        self.unit_price = 100  
        if self.weekend:
            self.unit_price *= 1.2  
        if self.child:
            self.unit_price /= 2  
    
    def calcPrice(self, num):
        
        return self.unit_price * num


adult_ticket = Ticket(weekend=True, child=False)
adult_total = adult_ticket.calcPrice(2)


child_ticket = Ticket(weekend=True, child=True)
child_total = child_ticket.calcPrice(3)


total_price = adult_total + child_total
print(f"2个大人和3个儿童周末的总票价为：{total_price}元")