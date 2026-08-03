def get_age(n):
    if n == 1:
        return 10
    else:
        return get_age(n - 1) + 2

# 输出所有人的年龄
for i in range(1, 6):
    print(f"第{i}个人的年龄是：{get_age(i)}岁")