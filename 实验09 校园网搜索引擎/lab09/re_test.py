import re
# 1.如何验证手机号？（ 要求：1开头，第二位3-9，共11位数字）
def is_valid_phone(phone):


    return re.match(pattern, phone) is not None
print(is_valid_phone("13800138000"))  # True
print(is_valid_phone("23800138000"))  # False

# 2. 如何验证日期格式？（暂不考虑日期真实性）
def is_valid_date(date):

    return re.match(pattern, date) is not None

print(is_valid_date("2023-05-15"))  # True
print(is_valid_date("2023/05/15"))  # False（分隔符错误）

# 3.判断以下三个URL格式是否符合要求？
def is_valid_url(url):
    pattern = r'^https?://[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+(/.*)?$'
    return re.match(pattern, url) is not None

print(is_valid_url("https://example.com"))
print(is_valid_url("http://localhost:8080"))
print(is_valid_url("ftp://example.com"))




