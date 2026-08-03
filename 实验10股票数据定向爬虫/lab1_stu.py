import requests
import csv
import time


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://xueqiu.com/",
    "Cookie": ""  # 如果还是被拦截，可以加上你浏览器里雪球网的Cookie
}

# 雪球网API接口（返回JSON格式数据）
url = "https://xueqiu.com/service/v5/stock/screener/quote/list"
params = {
    "type": "sha",
    "order": "desc",
    "order_by": "percent",
    "market": "CN",
    "size": 30,  # 每页条数
    "page": 1
}


try:
    response = requests.get(url, headers=headers, params=params, timeout=10)
    response.raise_for_status()  # 检查请求是否成功
    data = response.json()
except Exception as e:
    print(f"请求失败：{e}")
    exit()


stock_data = []
stocks = data.get("data", {}).get("list", [])

for stock in stocks:
    stock_info = {
        "股票代码": stock.get("symbol", ""),
        "股票名称": stock.get("name", ""),
        "当前价": stock.get("current", ""),
        "涨跌额": stock.get("chg", ""),
        "涨跌幅": stock.get("percent", ""),
        "年初至今": stock.get("current_year_percent", ""),
        "成交量": stock.get("volume", ""),
        "成交额": stock.get("amount", ""),
        "换手率": stock.get("turnover_rate", ""),
        "市盈率(TTM)": stock.get("pe_ttm", ""),
        "股息率": stock.get("dividend_yield", ""),
        "市值": stock.get("market_capital", "")
    }
    stock_data.append(stock_info)


csv_headers = ['股票代码', '股票名称', '当前价', '涨跌额', '涨跌幅', '年初至今', '成交量',
               '成交额', '换手率', '市盈率(TTM)', '股息率', '市值']

with open("xueqiu_stocks.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=csv_headers)
    writer.writeheader()
    writer.writerows(stock_data)

print(f"✅ 成功爬取 {len(stock_data)} 条数据，已保存到 xueqiu_stocks.csv")