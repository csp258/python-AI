import time
import random
from collections import deque
from urllib import request
import re
from bs4 import BeautifulSoup
import sqlite3
import jieba
# 1.初始化
# 1.1 设置入口 URL
url = 'https://news.gzus.edu.cn/gryw.htm'  # 目标数据：广软要闻
# 1.2 创建待爬取队列unvisited和已访问集合visited
unvisited = deque()  # 待爬链接队列（广度优先）
unvisited.append(url)
visited = set()  # 已访问的链接集合
# 1.3 创建数据库表
conn = sqlite3.connect('gzus_new.db')
cur = conn.cursor()
cur.execute('create table doc (id int primary key,link text)')  # 创建文档表（存储文档 ID 和 URL）
cur.execute('create table word (term varchar(25) primary key,list text)')   # 创建倒排索引表（词条→文档 ID 列表）
conn.commit()
cur.close()
conn.close()

cnt = 0
while unvisited:
    # 2.新闻数据爬取与解析
    url = unvisited.popleft()  # 取一个待爬 URL
    visited.add(url)  # 将URL标记为已访问
    cnt += 1
    print('开始抓取第', cnt, '个链接：', url)
    if cnt > 20:  # 限制次数
        break
    time.sleep(random.uniform(3, 8))  # 降低请求频率
    # 2.1 自行编写：爬取网页内容（注意使用异常处理）



    # 2.2 自行编写：利用BeautifulSoup解析网页内容（提取新闻链接+下页链接，存入unvisited）,解析工具为'lxml'

    # 自行编写：利用find_all()获取本页面所有的新闻链接<a>，存入列表all_a中

    for a_tag in all_a:
        x = a_tag['href']  # 网址
        if re.match(r'info/.+', x):  # "info/1011/90211.htm"
            x = 'https://news.gzus.edu.cn/' + x
        elif re.match(r'\.\./info/.+', x):  # "../info/1011/89661.htm"
            x = 'https://news.gzus.edu.cn/' + x[3:]
        if (x not in visited) and (x not in unvisited):
            unvisited.append(x)
    # 自行编写：利用find获取本页面的下页链接<span>，整合网址后，存入列表unvisited中




    # 2.3 解析网页内容（提取内容）
    # 自行编写：提取文章标题所对应的tag，命名为title_tag

    if title_tag:
        title = title_tag.text.strip()
        print(f'文章标题：{title}')
        # 自行编写：提取文章内容对应的tag，命名为content_div

        paragraphs = [p.text.strip() for p in content_div.find_all('p') if p.text.strip()]  # 提取所有段落文本
        article = ''.join(paragraphs).replace('\n', '').replace('\r', '')  # 合并内容并清理

        # 自行编写：对标题（title）和文章内容（article）进行中文分词，并存入列表seglist中



        # 3.数据存储
        conn = sqlite3.connect("gzus_new.db")
        cur = conn.cursor()
        # 3.1 将文档 ID 和 URL 存入doc表
        cur.execute('insert into doc values(?,?)', (cnt, url))
        # 3.2 将词条和文档 ID 存入word表
        for word in seglist:
            # 检验看看这个词语是否已存在于数据库
            cur.execute('select list from word where term=?', (word,))
            result = cur.fetchall()
            # 如果不存在，则插入
            if len(result) == 0:
                doc_list = str(cnt)  # 字符串类型
                cur.execute('insert into word values(?,?)', (word, doc_list))
            # 如果已存在，则追加文档 ID
            else:
                doc_list = result[0][0]
                doc_list += ' ' + str(cnt)
                cur.execute('update word set list=? where term=?', (doc_list, word))

        conn.commit()
        cur.close()
        conn.close()
print('词表建立完毕')
