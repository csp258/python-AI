import xlrd
import matplotlib.pyplot as plt

# 解决matplotlib中文乱码
plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

# ===================== 1.数据读取 =====================

wb = xlrd.open_workbook(r'D:\下载\visual studio code\text\实验12 学生成绩可视化展示\lab12\data.xls')
print(wb.sheet_names())

# 获取Sheet1对应的表格
sheet = wb.sheet_by_name("Sheet1")
# 获取第一行的值
header = sheet.row_values(0)
# 获取所有课程名、打印出所有课程名
course_list = header
print(course_list)

# ===================== 2.让用户选择要分析的课程，提取对应成绩列 =====================
course = input("请输入需要分析的课程:")
# 获取课程名的列索引
col_idx = course_list.index(course)
# 获取第m列的所有值（含课程名）
col_data = sheet.col_values(col_idx)
# 提取成绩（跳过第1行的课程名）
score_raw = col_data[1:]
# 过滤有效数字成绩
scores = []
for s in score_raw:
    if isinstance(s, (int, float)):
        scores.append(float(s))

# ===================== 3.基础统计分析 =====================
max_score = max(scores)
min_score = min(scores)
avg_score = sum(scores) / len(scores)
print('最高分:', max_score)
print('最低分:', min_score)
print('平均分:', avg_score)

# ===================== 4.统计各分数段人数 =====================
count = [0, 0, 0, 0, 0]
for s in scores:
    if s >= 90:
        count[0] += 1
    elif 80 <= s < 90:
        count[1] += 1
    elif 70 <= s < 80:
        count[2] += 1
    elif 60 <= s < 70:
        count[3] += 1
    else:
        count[4] += 1

# ===================== 5.绘制柱状图（和示例样式一致） =====================
x_label = [">=90", "80~89分", "70~79分", "60~69分", "60分以下"]
bar = plt.bar(x_label, count, color="green")
plt.title(f"{course}成绩分析")
plt.xlabel("分数段")
plt.ylabel("人数")

# 在柱子上方标注数值（和效果图一致带.0）
for b in bar:
    h = b.get_height()
    plt.text(b.get_x() + b.get_width()/2, h, f"{h}.0", ha="center", va="bottom")

plt.tight_layout()
plt.show()