# 输入自己球队的实力值
my_team = int(input("请输出自己球队的实力:"))
# 输入其他三支球队的实力值
team2 = int(input("请输出球队2的实力:"))
team3 = int(input("请输出球队3的实力:"))
team4 = int(input("请输出球队4的实力:"))

# 初始化总积分
total_score = 0

# 与球队2比赛
if my_team > team2:
    total_score += 3
elif my_team == team2:
    total_score += 1

# 与球队3比赛
if my_team > team3:
    total_score += 3
elif my_team == team3:
    total_score += 1

# 与球队4比赛
if my_team > team4:
    total_score += 3
elif my_team == team4:
    total_score += 1

# 输出我方球队总成绩
print("我方球队总成绩:" + str(total_score))