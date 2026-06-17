# class Car:
#     pass


# c1 = Car()
# c1.color = "read"
# c1.brand = "BMW"
# c1.name = "X5"
# c1.price = 50000

# print(c1.brand)
# print(c1.__dict__)


class Car:

    #类属性(所有实例对象所共有)
    wheel = 4  #轮胎
    tax_rate = 0.1 #购置税

    #__int__ 方法是初始化的方法,会在对象创建时自动调用,可以在该方法中为对象设置对应的属性
    #self: 是第一个参数,表示当前创建出来的实例对象
    def __init__(self, c_color, c_brand, c_name, c_price):
        self.color = c_color
        self.brand = c_brand
        self.name = c_name
        self.price = c_price

    def running(self):
        print(f"{self.brand} {self.name} 正在高速行驶.....")  

    def total_cost(self, discount, rate):
        total_cost = self.price * discount + self.price * rate
        return total_cost
    
    #魔法方法
    def __str__(self):
        return f"{self.color} {self.brand} {self.name} {self.price}"
    def __eq__(self, other):
        return self.color == other.color and self.brand == other.brand and self.price == other.price
    def __lt__(self, other):
        return self.price < other.price

    def __gt__(self, other):
        return self.price > other.price

c1 = Car("红色", "BWX", "X7", 800000)
c2 = Car("红色", "奔驰", "E300", 450000)

c1.running()

total = c1.total_cost(0.9, 0.1)
print(f"提车的总费用为:{total}")

print(c1)
print(c1 == c2)
print(c1 > c2)
print(c1.__dict__)
print(c1.color)
print(c1.wheel)  #通过实例对象查找属性时,会先查找实例属性,实例属性不存在,再查找类属性

        