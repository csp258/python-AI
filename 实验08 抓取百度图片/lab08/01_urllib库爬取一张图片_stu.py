from urllib import request
url='https://pics4.baidu.com/feed/9825bc315c6034a8a82df6093988705b0b237692.jpeg@f_auto?token=0afd1fcf354d7ed7f32fc5a509a3cdd4'
# 1.使用urlretrieve函数
request.urlretrieve(url, 'baidu_pic1.jpg')
print("方式一：图片下载完成！")



# 2.通过write()写入文件
from urllib import request

url = 'https://pics4.baidu.com/feed/9825bc315c6034a8a82df6093988705b0b237692.jpeg@f_auto?token=0afd1fcf354d7ed7f32fc5a509a3cdd4'

# 2. 通过 write() 写入文件
# 发送请求，获取响应对象
response = request.urlopen(url)
# 读取二进制内容
img_data = response.read()
# 写入本地文件
with open('baidu_pic2.jpg', 'wb') as f:
    f.write(img_data)
print("方式二：图片下载完成！")