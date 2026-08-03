import matplotlib.pyplot as plt
import numpy as np
# 生成随机数据
x = np.random.randint(100, 200, 10)  # 10个100~200的随机整数
y = np.random.randint(100, 130, 10)  # 10个100~130的随机整数
# 绘制散点图
plt.scatter(
    x, y,
    s=100,          # 点的大小
    c="r",          # 颜色（红色）
    marker="v",     # 形状（向下三角形）
    alpha=0.5       # 透明度
)
plt.show()





