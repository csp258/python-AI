from pandas import Series, DataFrame
# Series示例（可基于字典、列表、标量值创建）
sr = Series([2, 7, -3, 9.6], index=['A', 'B', 'C', 'D'])
print(sr)

sr = Series([2, 7, -3, 9.6])
print(sr)

# DataFrame示例（可基于字典、列表、多个Series组合、NumPy数组、CSV/Excel文件读取创建）
data = {
    'a': [1, 2, 3],
    'b': ['we', 'you', 'they'],
    'c': ['我们', '你们', '他们'],
    'd': [True, False, None]
}
df = DataFrame(data, index=[1,2,3])
print(df)