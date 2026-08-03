import requests
from bs4 import BeautifulSoup
import csv
import os

# 1. 配置：文件直接保存在当前脚本所在的文件夹
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "tonghuashun_stocks.csv")

# 表头（和题目字段完全对应）
csv_headers = [
    '序号', '代码', '名称', '现价', '涨跌幅(%)', '涨跌', '涨速(%)',
    '换手(%)', '量比', '振幅(%)', '成交额', '流通股', '流通市值', '市盈率'
]

# 2. 发送请求（同花顺行情中心）
url = "https://q.10jqka.com.cn/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://q.10jqka.com.cn/"
}

try:
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    response.encoding = "gbk"  # 适配同花顺的中文编码
except Exception as e:
    print(f"请求失败：{e}")
    exit()

# 3. 解析数据
soup = BeautifulSoup(response.text, "html.parser")
# 定位表格（根据同花顺网页结构调整）
table = soup.find("table", class_="m-table")

if not table:
    print("未找到数据表格，可能是页面结构更新了")
    exit()

rows = table.find_all("tr")[1:]  # 跳过表头
stock_data = []

for row in rows:
    cols = row.find_all("td")
    if len(cols) < len(csv_headers):
        continue  # 跳过不完整的行
    
    # 按顺序提取数据
    stock_info = {
        '序号': cols[0].text.strip(),
        '代码': cols[1].text.strip(),
        '名称': cols[2].text.strip(),
        '现价': cols[3].text.strip(),
        '涨跌幅(%)': cols[4].text.strip(),
        '涨跌': cols[5].text.strip(),
        '涨速(%)': cols[6].text.strip(),
        '换手(%)': cols[7].text.strip(),
        '量比': cols[8].text.strip(),
        '振幅(%)': cols[9].text.strip(),
        '成交额': cols[10].text.strip(),
        '流通股': cols[11].text.strip(),
        '流通市值': cols[12].text.strip(),
        '市盈率': cols[13].text.strip()
    }
    stock_data.append(stock_info)

# 4. 保存数据到CSV
with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=csv_headers)
    writer.writeheader()
    writer.writerows(stock_data)

print(f" 成功爬取 {len(stock_data)} 条数据")
print(f" 文件已保存到：{file_path}")