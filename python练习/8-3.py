products = [
    {"name": "电脑", "price": 7000},
    {"name": "鼠标", "price": 30},
    {"name": "usb电动小风扇", "price": 20},
    {"name": "遮阳伞", "price": 50},
]

# 计算所有商品的总价
total_price = 0
for product in products:
    total_price += product["price"]

# 判断是否能购买
if total_price <= 8000:
    print("可以购买")
else:
    print("无能力购买")