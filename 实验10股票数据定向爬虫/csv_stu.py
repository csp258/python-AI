import csv
users = [
    {'name': 'Alice', 'age': 28, 'city': 'Beijing'},
    {'name': 'Bob', 'city': 'Shanghai', 'age': 32}
]
# 将users数据写入users.csv文件
headers = ['name', 'age', 'city']
with open("users.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=headers)
    writer.writeheader()
    writer.writerows(users)

print("users.csv 写入完成")