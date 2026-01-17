import csv
import os
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# --- 🛠️ 配置区 ---
SAVE_FILE = 'literature_poems.csv'
# 这里的关键词可以根据项目书需求增加
KEYWORDS = ["荔枝", "蜀道", "子午谷", "妃子笑", "一骑红尘", "杨贵妃", "长安", "驿站"]
MAX_PAGES = 3  # 每个词抓3页，差不多能有100多条数据


def setup_driver():
    print("🚗 启动浏览器...")
    chrome_options = Options()
    # 必须显示界面，否则你怎么扫码登录？
    # chrome_options.add_argument("--headless")

    # 防屏蔽参数
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def init_csv():
    # 如果文件不存在，先写表头
    if not os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'title', 'author', 'era', 'content', 'type', 'source'])


def main():
    driver = setup_driver()
    init_csv()

    # 1.先打开首页
    driver.get("https://so.gushiwen.cn/")

    # --- 🛑 关键步骤：给你 40秒 时间手动登录 ---
    print("\n" + "=" * 50)
    print("🚨 【请注意】浏览器已打开！")
    print("👉 请在 40秒 内，在浏览器里点击右上角“登录”，用微信扫码登录。")
    print("👉 登录成功后，不要关浏览器，脚本会自动开始工作！")
    print("=" * 50 + "\n")

    # 倒计时显示
    for i in range(40, 0, -1):
        print(f"\r⏳ 剩余登录时间: {i} 秒...", end="")
        time.sleep(1)
    print("\n\n🚀 时间到！开始自动执行抓取任务...\n")

    # 计算当前ID
    current_id = 1
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, 'r', encoding='utf-8') as f:
            current_id = len(f.readlines())

    for keyword in KEYWORDS:
        print(f"\n🔍 正在搜索关键词: 【{keyword}】")

        for page in range(1, MAX_PAGES + 1):
            print(f"   📄 第 {page} 页...")
            url = f"https://so.gushiwen.cn/search.aspx?value={keyword}&page={page}"
            driver.get(url)
            time.sleep(random.uniform(2, 4))  # 随机休息，模拟真人阅读

            try:
                poems = driver.find_elements(By.CSS_SELECTOR, ".sons .cont")

                if len(poems) == 0:
                    print("      ⚠️ 本页无内容或又弹出验证码了...")
                    break

                for poem in poems:
                    try:
                        title_text = poem.find_element(By.CSS_SELECTOR, "b").text
                        content_text = poem.find_element(By.CSS_SELECTOR, ".contson").text.replace("\n", " ")

                        # 简单去重：如果内容里没有关键词，可能是不相关的
                        if keyword not in (title_text + content_text):
                            continue

                        source_text = "未知"
                        try:
                            source_text = poem.find_element(By.CSS_SELECTOR, ".source").text
                            parts = source_text.split('：')
                            era = parts[0] if len(parts) > 0 else "未知"
                            author = parts[1] if len(parts) > 1 else "佚名"
                        except:
                            era, author = "未知", "佚名"

                        with open(SAVE_FILE, 'a', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow(
                                [current_id, title_text, author, era, content_text, '诗歌', driver.current_url])

                        print(f"      ✅ [{current_id}] {title_text}")
                        current_id += 1

                    except:
                        continue

            except Exception as e:
                print(f"      ❌ 页面出错: {e}")

    print(f"\n🎉 大功告成！数据已保存在 {SAVE_FILE}")
    print("你可以关闭浏览器了。")
    # driver.quit()


if __name__ == '__main__':
    main()