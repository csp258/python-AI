import math

try:
    
    a = float(input("请输入三角形第一条边："))
    b = float(input("请输入三角形第二条边："))
    c = float(input("请输入三角形第三条边："))

   
    if a <= 0 or b <= 0 or c <= 0:
        raise Exception("边长小于等于0")

    
    assert (a + b > c) and (a + c > b) and (b + c > a), "不满足两边之和大于第三边的条件"

    
    s = (a + b + c) / 2  # 半周长（也可直接代入公式）
    area = math.sqrt(s * (s - a) * (s - b) * (s - c))  # 海伦公式（与题目公式等价）
    print(f"三角形的面积是：{area}")

except ValueError as e:
    
    print(f"数据类型错误：{e}")
except AssertionError as e:
   
    print(f"断言错误：{e}")
except Exception as e:
    
    print(f"其他异常：{e}")
finally:
    
    print("程序结束！")