import random
import time
from urllib import request
from bs4 import BeautifulSoup
import sqlite3
import jieba
import math
# 1.数据准备
conn = sqlite3.connect("gzus_new.db")
cur = conn.cursor()
# 计算文档总数
cur.execute('select count(*) from doc')
N = cur.fetchall()[0][0]
# 2.自行编写：用户输入与分词（分词结果存入seggen）


# 3.计算词条相关文档的得分（TF-IDF计算）
# 自行编写：构建字典tf_idf（文档ID:文档得分）

for word in seggen:
    # 自行编写：构建字典tf（文档ID:词在文档中出现的次数）

    # 3.1 查询词条对应的文档ID列表
    print('得到查询词：', word)
    cur.execute('select list from word where term=?', (word,))
    # 自行编写：获取查询结果,存入result

    if len(result) > 0:
        doc_list = result[0][0]  # 获取list字段中的内容
        # 3.2 自行编写：计算IDF（提示：python中math.log默认是自然对数）


        # 3.3 自行编写：计算TF（统计词频）


        # 3.4 自行编写：计算TF_IDF


    else:
        print("抱歉，无搜索结果！")

# 4.结果排序与展示
sortedlist = sorted(tf_idf.items(), key=lambda d: d[1], reverse=True)  # 排序
# print(sortedlist)
for num, doc_score in sortedlist:
    # 4.1 自行编写：获取num对应的url，并打印url和相应的得分
    cur.execute('select link from doc where id=?', (num,))


    time.sleep(random.uniform(3, 8))  # 降低请求频率
    # 4.2 自行编写：爬取网页内容


    # 4.3 自行编写：解析网页内容（提取标题，并打印）



conn.commit()
cur.close()
conn.close()

