# 接收用户输入的诗
poem = input("请输入一首诗：")
# 去除诗中的空格和标点（这里简单处理，假设只有逗号分隔）
poem = poem.replace("，", "").replace("。", "").replace(" ", "")
# 将诗按字符反转
reversed_poem = poem[::-1]
# 判断正读和反读是否一致
if poem == reversed_poem:
    print("这是一首回文诗")
else:
    print("这不是一首回文诗")