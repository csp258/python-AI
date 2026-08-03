
peach = 1  # 第10天剩余1个桃子
for day in range(9, 0, -1):  # 从第9天倒推到第1天
    peach = (peach + 1) * 2
print("猴子们一共摘了", peach, "个桃子")