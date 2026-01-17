import csv
import os
import time
import random
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# --- 配置区 ---
IMAGE_DIR = 'images'  # 图片保存文件夹
CSV_FILE = 'data.csv'  # 数据源文件
BROWSER_HEADLESS = False  # 设置为 False 可以看到浏览器自动运行的过程，设置为 True 则后台静默运行


def setup_driver():
    """初始化浏览器驱动"""
    chrome_options = Options()
    if BROWSER_HEADLESS:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # 伪装 User-Agent
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

    # 自动下载并安装适配的 ChromeDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def download_image(url, save_path):
    """下载图片并保存"""
    try:
        # 设置超时时间，防止卡死
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            print(f"    └─ 成功保存: {os.path.basename(save_path)}")
            return True
    except Exception as e:
        print(f"    └─ 下载失败: {e}")
    return False


def main():
    # 1. 创建文件夹
    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)

    # 2. 检查CSV文件
    if not os.path.exists(CSV_FILE):
        print(f"❌ 错误：找不到 {CSV_FILE}，请确认文件位置。")
        return

    print("🤖 正在启动浏览器机器人...")
    driver = setup_driver()
    driver.maximize_window()  # 最大化窗口

    try:
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                site_id = row['id']
                site_name = row['name']
                file_name = f"{site_id}.jpg"
                save_path = os.path.join(IMAGE_DIR, file_name)

                # 如果图片已存在，跳过
                if os.path.exists(save_path):
                    print(f"⏩ [{site_name}] 图片已存在，跳过。")
                    continue

                keyword = f"{site_name} 风景"
                print(f"\n🔍 正在搜索: {keyword}")

                # --- 核心采集逻辑 (使用 Bing 图片搜索，比百度更适合脚本) ---
                search_url = f"https://www.bing.com/images/search?q={keyword}"
                driver.get(search_url)

                # 随机等待 2-4 秒，模仿人类查看网页
                time.sleep(random.uniform(2, 4))

                try:
                    # 寻找第一张图片元素。Bing 的图片缩略图通常有 class 'mimg'
                    # 我们尝试获取页面上第一个有效的图片标签
                    img_elements = driver.find_elements(By.CSS_SELECTOR, "img.mimg")

                    found_url = None
                    if img_elements:
                        # 获取第一张图的 src
                        found_url = img_elements[0].get_attribute("src")

                        # 如果 src 是空的，尝试 data-src (有些网站懒加载)
                        if not found_url:
                            found_url = img_elements[0].get_attribute("data-src")

                    if found_url:
                        # 过滤掉 base64 格式的小图标（太模糊），尽量找 http 开头的链接
                        if found_url.startswith("http"):
                            print(f"    ├─ 找到图片链接...")
                            download_image(found_url, save_path)
                        else:
                            print(f"    ├─ ⚠️ 警告: 找到的图片格式不支持下载 (Base64)，尝试下一张...")
                            # 这里可以写更复杂的逻辑去处理 Base64，但对于初学者，跳过即可
                    else:
                        print(f"    ├─ ❌ 未找到相关图片元素")

                except Exception as e:
                    print(f"    ├─ ❌ 页面解析出错: {e}")

                # 采集完一个，休息一下，做个有礼貌的爬虫
                time.sleep(random.uniform(1, 2))

    finally:
        print("\n🏁 任务结束，正在关闭浏览器...")
        driver.quit()


if __name__ == '__main__':
    main()