# 原始信件内容
letter = "ma*g*i*c *i*s *a*ma*z*i*ng* t*h*e* *m*ag*i*c *sc*ho*o*l* *i*s *fu*l*l *o*f *se*c*re*t*s"
# 清除所有“*”
cleaned_letter = letter.replace("*", "")
# 以空格为分隔符分割成单词列表
words = cleaned_letter.split()
# 统计“magic”出现的次数
magic_count = words.count("magic")
# 根据“magic”出现次数打印对应内容
if magic_count >= 2:
    print("这是一封充满魔力的信件！")
else:
    print("这封信件的魔力稍显不足")
# 将单词列表以短线“-”为分隔符重新连接并打印
new_content = "-".join(words)
print(new_content)