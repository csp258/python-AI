# 示例一（利用requests访问搜狗网：https://www.sogou.com）：
# 1.导入模块
import requests
# 2.发送请求，获取响应
response = requests.get('https://www.sogou.com/')
# 3.获取响应数据
print("=== 示例一输出 ===")
print("response.text（字符串类型的网页源码）：")
# str类型：自动根据编码解析成字符串
print(response.text[:200])  # 只打印前200字符，避免输出过长

print("\nresponse.encoding（当前自动识别的编码）：")
# 当前文本解码编码
print(response.encoding)  

# 手动设置编码为utf-8，解决乱码问题
response.encoding = 'utf-8'

print("\nresponse.content（字节类型的原始数据）：")
# byte类型：原始二进制数据
print(response.content[:100])  

print("\nresponse.content.decode()（字节解码为字符串）：")
# 将字节内容解码为字符串（默认utf-8）
print(response.content.decode()[:200])  


print(response.content.decode())  # 将字节内容解码为字符串
# print(response.json())  # 报错：响应数据非JSON类型




# 示例二（利用requests访问目标网址，获取所有风向数据）：
url = 'http://t.weather.itboy.net/api/weather/city/101280101'
response = requests.get(url)

# 设置编码，避免中文乱码
response.encoding = 'utf-8'

print("\n=== 示例二输出 ===")
# 1. 直接获取JSON数据（API返回的是JSON格式）
weather_data = response.json()

# 2. 打印返回的完整JSON（格式化输出）
import json
print(json.dumps(weather_data, ensure_ascii=False, indent=4))

# 3. 提取风向相关数据（根据API结构）
if weather_data.get('status') == 200:
    city_info = weather_data.get('cityInfo', {})
    data = weather_data.get('data', {})
    forecast = data.get('forecast', [])
    
    print("\n城市：", city_info.get('city'))
    print("当前温度：", data.get('wendu'), "℃")
    print("当前湿度：", data.get('shidu'))
    print("当前风向：", data.get('fengxiang'), " ", data.get('fengli'))
    
    print("\n未来几天风向预报：")
    for day in forecast:
        print(f"{day['date']} {day['week']}：风向 {day['fengxiang']}，风力 {day['fengli']}")
else:
    print("请求失败，状态码：", weather_data.get('status'))