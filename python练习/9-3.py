def multi(*args):
    product = 1
    for num in args:
        product *= num
    return product

# 调用函数并输出结果
print("传递2个参数的乘积:", multi(2, 3))
print("传递3个参数的乘积:", multi(2, 3, 4))
print("传递4个参数的乘积:", multi(2, 3, 4, 5))
print("传递5个参数的乘积:", multi(2, 3, 4, 5, 6))