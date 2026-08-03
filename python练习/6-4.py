# 初始化“过”出现的次数为0
count = 0
# 循环遍历1到100的数字
for num in range(1, 101):
    # 判断数字是否是7的倍数或者尾数是7
    if num % 7 == 0 or num % 10 == 7:
        print("过")
        # 次数加1
        count += 1
        # 跳过本次循环，继续下一个数字
        continue
    # 不是则打印该数字
    print(num)
# 循环结束后，打印“过”出现的次数
print("\"过\"出现的次数为{}次".format(count))