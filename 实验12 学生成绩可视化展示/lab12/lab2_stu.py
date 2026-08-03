import xlrd
import matplotlib.pyplot as plt

# 解决matplotlib中文乱码问题
plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

# 1. 读取Excel Sheet2数据
# 方式1：如果脚本和data.xls同文件夹，直接写文件名
wb = xlrd.open_workbook(r"D:\下载\visual studio code\text\实验12 学生成绩可视化展示\lab12\data.xls")

sheet = wb.sheet_by_name("Sheet2")
# 第一行是表头，从第二行开始读取品牌和销量
brands = []
sales = []
for row in range(1, sheet.nrows):
    brand = sheet.cell_value(row, 0)
    sale = sheet.cell_value(row, 1)
    brands.append(brand)
    sales.append(sale)

# 2. 绘制饼图
plt.figure(figsize=(6, 6))  # 设置画布为正方形，饼图不会变形
plt.pie(
    sales,
    labels=brands,
    autopct="%.1f%%",  # 百分比保留1位小数
    startangle=90      # 起始角度优化排版
)
plt.title("不同汽车品牌月销量占比")
plt.axis("equal")  # 保证饼图是正圆形
plt.show()