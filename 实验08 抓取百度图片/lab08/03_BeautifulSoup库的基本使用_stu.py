import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def spider_images_from_static_site(url, save_dir, max_num=5):
    # 1. 请求头伪装
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    # 2. 发送请求
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'
        html = response.text
    except Exception as e:
        print(f"❌ 网页请求失败：{e}")
        return

    # 3. 用BeautifulSoup解析所有img标签
    soup = BeautifulSoup(html, 'html.parser')
    img_tags = soup.find_all('img')

    if not img_tags:
        print("❌ 页面中未找到任何img标签")
        return

    # 4. 过滤并处理图片链接
    all_img_urls = set()
    for img in img_tags:
        # 兼容多种懒加载属性
        img_src = img.get('src') or img.get('data-src') or img.get('data-original')
        if not img_src:
            continue
        # 拼接完整URL
        full_url = urljoin(url, img_src)
        # 过滤无效链接
        if (not full_url.startswith('data:') 
            and not full_url.endswith('.svg') 
            and len(full_url) > 10):
            all_img_urls.add(full_url)

    if not all_img_urls:
        print("❌ 未找到任何有效图片链接")
        return

    # 5. 创建保存目录
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        print(f"📁 创建保存目录：{save_dir}")

    # 6. 下载图片
    count = 0
    for img_url in all_img_urls:
        if count >= max_num:
            break
        try:
            img_response = requests.get(img_url, headers=headers, timeout=10)
            if img_response.status_code == 200:
                filename = os.path.join(save_dir, f"{count+1}.jpg")
                with open(filename, 'wb') as f:
                    f.write(img_response.content)
                print(f"✅ 已下载：{filename}")
                count += 1
        except Exception as e:
            print(f"❌ 下载失败 {img_url[:50]}... 错误：{e}")

    print(f"\n🎉 下载完成！共成功下载 {count} 张图片，保存到：{os.path.abspath(save_dir)}")

if __name__ == '__main__':
    # 这里用一个静态图片网站作为测试
    target_url = "https://www.baidu.com"  # 百度首页，有很多静态图片
    save_directory = "soup_images"
    max_images = 5

    spider_images_from_static_site(target_url, save_directory, max_images)