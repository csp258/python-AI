import pandas as pd

data = {
    '学号': ['05', '03', '02', '04', '06', '01'],
    '姓名': ['张伟', '王芳', '李强', '陈静', '刘洋', '赵敏'],
    '年龄': ['18', '19', '19', '20', '18', '21'],
    '语文': ['88', '92', '75', '81', None, '95'],    # 含缺失值
    '数学': ['92', '85', '100', '78', '88', '90'],
    '英语': ['85', '90', '88', None, '92', '80']     # 含缺失值
}


df = pd.DataFrame(data)
print(df)

# 1. 获取列名
print(df.columns)  # 返回的是 Index 对象，类似列表
print("所有列名:", df.columns.tolist())  # 转换为列表
print("第三列名称:", df.columns[2])    # 根据索引返回对应位置的列名

# 2. 数据排序
df_sorted = df.sort_values(by="学号")  # 默认升序
print("\n按学号排序后的数据:")
print(df_sorted)

# 3. 数据选择（iloc的语法：df.iloc[行索引, 列索引]）
print("\n第一行所有数据:")
print(df.iloc[0])  # 选择张伟的完整记录

print("\n所有人的语文成绩列:")
print(df.iloc[:, 3])

print("\n最后一个人的年龄:", df.iloc[-1, 2])

# 4. 数据删除
df_drop = df.drop(['年龄'], axis=1)   # axis=1按列操作，默认是行操作
print("\n删除年龄列后的数据:")
print(df_drop)

# 5. 数据处理
# 缺失值统计
print("\n缺失值统计:")
df_missing = df.isnull().sum()
print(df_missing)

# 类型转换
df_numeric = df.iloc[:, 3:].apply(pd.to_numeric, errors='coerce')
print("\n类型转换后:")
print(df_numeric)

# 填充缺失值
df_filled = df_numeric.fillna(df_numeric.mean())
print("\n用均值填充后的数据:")
print(df_filled)