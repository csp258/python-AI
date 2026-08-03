
class Pet:
    def __init__(self, name, health):
        self.name = name  
        self.health = health  

    def cure(self):
       
        pass



class Dog(Pet):
    def __init__(self, name, health):
       
        super().__init__(name, health)

    def cure(self):
       
        return "打针、吃药"



class Cat(Pet):
    def __init__(self, name, health):
        
        super().__init__(name, health)

    def cure(self):
       
        return "吃药、疗养"


 
def to_hospital(pet):
    
    if pet.health < 60:
        
        treatment = pet.cure()
        
        print(f"{pet.name}的健康值为{pet.health}，需要{treatment}")



dog = Dog("肠肠", 57)
cat = Cat("胖迪", 50)


to_hospital(dog)
to_hospital(cat)