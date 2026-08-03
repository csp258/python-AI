# 定义敏感词列表
sensitive_words = ["笨蛋", "水货", "痴线"]
# 提示用户输入一段文本
text = input("请输入一段话：")
# 遍历敏感词列表
for word in sensitive_words:
    # 检查文本中是否包含当前敏感词
    if word in text:
        print("文本中存在敏感词!")
        # 若存在，跳出循环
        break
else:
    # 若循环正常结束（即没有触发break），说明文本中没有敏感词
    print("文本中未发现敏感词!")