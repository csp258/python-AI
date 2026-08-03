import math
radius = float(input("请输入半径值："))
area = math.pi * math.pow(radius, 2)
volume = (4 / 3) * math.pi * math.pow(radius, 3)
print(f"以该半径构成的圆的面积为：{area:.2f}")
print(f"以该半径构成的球的体积为：{volume:.2f}")