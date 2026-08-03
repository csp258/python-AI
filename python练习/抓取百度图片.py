import requests
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def download_images_with_bs4(url, save_dir="./网页图片", max_num=5):
    # 1. 创建保存目录
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        print(f"已创建保存目录：{os.path.abspath(save_dir)}")

    # 2. 构造请求头，模拟浏览器
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    }

    # 3. 请求网页
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        response.encoding = "utf-8"
    except Exception as e:
        print(f"请求网页失败：{e}")
        return

    # 4. 用 BeautifulSoup 解析 HTML
    soup = BeautifulSoup(response.text, "html.parser")
    img_tags = soup.find_all("img")  # 提取所有 img 标签

    # 5. 提取图片链接（处理相对路径）
    img_urls = []
    for img in img_tags:
        src = img.get("src") or img.get("data-src")
        if src:
            # 把相对路径转成绝对路径
            absolute_url = urljoin(url, src)
            img_urls.append(absolute_url)

    if not img_urls:
        print("未在网页中找到任何图片")
        return

    print(f"成功解析到 {len(img_urls)} 个图片链接")

    # 6. 下载图片
    count = 0
    for img_url in img_urls:
        if count >= max_num:
            break
        try:
            print(f"正在下载第 {count+1} 张图片：{img_url[:50]}...")
            img_response = requests.get(img_url, headers=headers, timeout=10)
            img_response.raise_for_status()

            # 保存图片，按 1.jpg、2.jpg... 命名
            save_path = os.path.join(save_dir, f"{count+1}.jpg")
            with open(save_path, "wb") as f:
                f.write(img_response.content)

            print(f"✅ 已保存：{save_path}")
            count += 1
        except Exception as e:
            print(f"❌ 下载失败：{e}")

    print(f"\n爬取完成！共下载 {count} 张图片，保存在：{os.path.abspath(save_dir)}")

if __name__ == "__main__":
    
    target_url = "https://image.baidu.com/search/detail?adpicid=0&b_applid=11167296123682198492&bdtype=0&commodity=&copyright=&cs=1309679938%2C1370356780&di=7630500745602662401&fr=click-pic&fromurl=http%253A%252F%252Fwww.douyin.com%252Fnote%252F7283280174496435490&gsm=1e&hd=&height=0&hot=&ic=&ie=utf-8&imgformat=&imgratio=&imgspn=0&is=2958699928%2C3231943009&isImgSet=&latest=&lid=a6492bfb015e736e&lm=&objurl=https%253A%252F%252Fp3-pc-sign.douyinpic.com%252Ftos-cn-i-0813c001%252FoIeCRfAnA7ktAPinMyWiAiCTyAEAIASmzbavhg~tplv-dy-aweme-images%253Aq75.webp%253Fbiz_tag%253Daweme_images%2526from%253D327834062%2526lk3s%253D138a59ce%2526s%253DPackSourceEnum_SEO%2526sc%253Dimage%2526se%253Dfalse%2526x-expires%253D1763330400%2526x-signature%253DASO2Icbvv7YFpYlii23YtOoeXp0%25253D&os=2958699928%2C3231943009&pd=image_content&pi=0&pn=0&rn=1&simid=1309679938%2C1370356780&tn=baiduimagedetail&width=0&word=%E5%90%91%E6%97%A5%E8%91%B5&z="
    download_images_with_bs4(target_url, save_dir="./向日葵图片", max_num=5)