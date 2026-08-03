# 1.导入模块
import sqlite3
# 2.建立数据库连接(创建SQLite数据库sales.db)
conn = sqlite3.connect('sales.db')
# 3.创建游标对象
cursor = conn.cursor()
# 4.使用cursor对象的execute执行SQL命令
# 创建表book：包含三个列，id（主键）、price和name
cursor.execute('''
CREATE TABLE IF NOT EXISTS book (
    id TEXT PRIMARY KEY,
    price INTEGER,
    name TEXT
)
''')
# 插入一行数据('001',33,'大学计算机多媒体')
# 外层用双引号，内层用单引号，注意逗号分隔每个值
cursor.execute("INSERT INTO book VALUES ('001', 33, '大学计算机多媒体')")# 插入多行数据
books=[("021",25,"大学计算机"),("022",30, "大学英语"),("023",18, "艺术欣赏 ") ,( "024",35, "高级语言程序设计")]
cursor.executemany("INSERT INTO book VALUES (?, ?, ?)", books)
# 修改一行数据(将"大学英语"的价格修改为25)
cursor.execute("UPDATE book SET price = 25 WHERE name = '大学英语'")
# 删除一行数据(删除价格为25的数据)
cursor.execute("DELETE FROM book WHERE price = 25")
# 5.处理返回结果：获取游标的查询结果集
cursor.execute("SELECT * FROM book")
results = cursor.fetchall()
print("当前表中的数据：")
for row in results:
    print(row)
# 6.提交事务
conn.commit()
# 7.关闭游标和连接
cursor.close()
conn.close()
