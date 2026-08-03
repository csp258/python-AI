class Car:
   
    total_cars = 0

    def __init__(self, brand, model):
       
        self.brand = brand
        self.model = model
        
        Car.total_cars += 1

    def __del__(self):
        
        print(f"{self.brand}{self.model}实例被销毁。")
        
        Car.total_cars -= 1
        
        if Car.total_cars > 0:
            print(f"当前剩余{Car.total_cars}辆Car实例。")



car1 = Car("小米", "SU7")
car2 = Car("理想", "L7")
car3 = Car("仰望", "U8")


car3.model = "U9"


del car1
del car2
del car3