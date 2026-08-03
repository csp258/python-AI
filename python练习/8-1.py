tourist_sources = [
    "北京", "上海", "广州", "深圳", "北京",
    "成都", "杭州", "广州", "武汉", "上海",
    "重庆", "北京", "西安", "深圳"
]

sources = set(tourist_sources)
source_count = len(sources)


gx = "广西" in sources

print(f"不同来源地的数量：{source_count}")
print(f"是否有游客来自广西：{gx}")