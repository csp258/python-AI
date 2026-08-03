# 获取用户输入
city = input("请输入城市名称：")
weather = input("请输入天气状况（晴天、阴天、雨天）：")
temperature = input("请输入温度（摄氏度）：")

# 根据天气状况确定趣味注释
if weather == "晴天":
    comment = "晒晒太阳，补补钙吧！"
elif weather == "阴天":
    comment = "虽然天空不晴朗，但心情可以自己调节哦！"
elif weather == "雨天":
    comment = "记得带伞哦，别淋成落汤鸡！"
else:
    comment = "无"

# 格式化输出个性化天气预报
forecast = f"""【{city}天气预报】
天气状况：{weather}
温度：{temperature}°C
趣味注释：{comment}"""

print(forecast)