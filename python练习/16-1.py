
class Vehicle:
    def __init__(self, brand, color):
        self.brand = brand
        self.color = color

    def showInfo(self):
        print(f"Brand: {self.brand}")
        print(f"Color: {self.color}")



class Car(Vehicle):
    def __init__(self, brand, color, seat):
      
        super().__init__(brand, color)
        self.seat = seat  

    def showInfo(self):
       
        super().showInfo()
       
        print(f"Seat: {self.seat}")



car = Car("Toyota", "Red", 4)
car.showInfo()