# 定义基类Animal
class Animal:
    def __init__(self, age, health_status):
        # 私有属性：年龄、健康状态
        self._age = age
        self._health_status = health_status

    def eat(self, food):
        # 基类进食方法（子类可重写）
        print("The animal eats specific food for this type of animal.")

    def make_sound(self):
        # 基类发声方法（子类需重写）
        pass

    # 年龄的访问器方法
    def get_age(self):
        return self._age

    def set_age(self, new_age):
        self._age = new_age


# 定义子类Lion（继承Animal）
class Lion(Animal):
    def __init__(self, age, health_status):
        super().__init__(age, health_status)

    def make_sound(self):
        # 重写发声方法：狮子的吼声
        print("Roar!")

    def eat(self, food):
        # 重写进食方法：狮子的进食行为
        print("The lion devours the meat.")


# 定义子类Elephant（继承Animal）
class Elephant(Animal):
    def __init__(self, age, health_status):
        super().__init__(age, health_status)

    def make_sound(self):
        # 重写发声方法：大象的鸣叫声
        print("Trumpet!")


# 定义子类Dolphin（继承Animal）
class Dolphin(Animal):
    def __init__(self, age, health_status):
        super().__init__(age, health_status)

    def make_sound(self):
        # 重写发声方法：海豚的声音
        print("Click and whistle!")


# 测试函数：模拟动物园管理
def test_zoo():
    # 创建不同类型的动物实例
    animals = [
        Lion(age=5, health_status="good"),
        Elephant(age=10, health_status="fair"),
        Dolphin(age=3, health_status="excellent")
    ]

    # 遍历动物列表，调用行为方法（体现多态性）
    for animal in animals:
        # 输出动物类型
        print(f"Animal is {type(animal).__name__}")
        # 调用发声方法
        animal.make_sound()
        # 调用进食方法
        animal.eat(food="")
        # 分隔不同动物的输出
        print()


# 执行测试
test_zoo()