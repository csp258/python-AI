import os
import requests
import re

def baidu_image_spider(keyword, save_dir, max_num=10):
    # 1. 准备请求参数和请求头（伪装成浏览器）
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    # 百度图片搜索URL
    base_url = 'https://image.baidu.com/search/flip?tn=baiduimage&word='
    url = base_url + keyword
    
    # 2. 发送请求，获取页面源码
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    html = response.text
    
    # 3. 用正则提取图片链接
    # 匹配objURL字段，里面是真实图片地址
    pattern = re.compile(r'"objURL":"(.*?)"')
    img_urls = pattern.findall(html)
    
    # 4. 创建保存目录
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        print(f"创建保存目录：{save_dir}")
    
    # 5. 下载图片
    count = 0
    for img_url in img_urls:
        if count >= max_num:
            break
        
        try:
            # 发送图片请求
            img_response = requests.get(img_url, headers=headers, timeout=10)
            if img_response.status_code == 200:
                # 生成文件名
                filename = os.path.join(save_dir, f"{count+1}.jpg")
                # 写入图片
                with open(filename, 'wb') as f:
                    f.write(img_response.content)
                print(f"✅ 已下载：{filename}")
                count += 1
        except Exception as e:
            print(f"❌ 下载失败 {img_url}，错误：{e}")
    
    print(f"\n下载完成！共成功下载 {count} 张图片，保存到：{os.path.abspath(save_dir)}")

if __name__ == '__main__':
    # 配置参数
    keyword = "向日葵"       # 搜索主题
    save_dir = "baidu_images" # 保存目录
    max_num = 5             # 最多下载张数（和示例效果一致，可修改）
    
    # 启动爬虫
    baidu_image_spider(keyword, save_dir, max_num)