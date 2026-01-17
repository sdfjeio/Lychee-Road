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
SAVE_FILE = 'literature_scholar.csv'  # 保存到这个新文件
# 关键词：更加偏向学术、考古、地理
KEYWORDS = [
  "荔枝道",
  "蜀道交通",
  "唐代驿传制度",
  "古代驿道",
  "贡荔运输",
  "唐代交通制度",
  "驿站制度研究",
  "邮驿制度",
  "唐代物流史",
  "古代交通史",
  "唐诗中的交通意象",
  "唐代行旅诗",
  "驿道文化",
  "蜀道文化研究",
  "交通与文学"
]

MAX_PAGES = 2  # 每个词抓2页


def setup_driver():
    print("🎓 启动学术采集助手...")
    chrome_options = Options()
    # 百度学术反爬比较严，必须用可视模式
    # chrome_options.add_argument("--headless")

    # 伪装成真人浏览器
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def init_csv():
    if not os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # 表头要和之前的保持一致，方便网站读取
            writer.writerow(['id', 'title', 'author', 'era', 'content', 'type', 'source'])


def main():
    driver = setup_driver()
    init_csv()

    # 计算当前ID (防止和诗歌的ID冲突，我们从 2000 开始编号)
    current_id = 2000
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if len(lines) > 1:
                current_id = 2000 + len(lines)

    print(f"📚 目标关键词: {KEYWORDS}")

    for keyword in KEYWORDS:
        print(f"\n🔍 正在检索学术资料: 【{keyword}】")

        for page in range(0, MAX_PAGES):
            # 百度学术的分页逻辑：第1页是0，第2页是10，第3页是20
            pn = page * 10
            url = f"https://xueshu.baidu.com/s?wd={keyword}&pn={pn}&filter=sc_type%3D%7B1%7D"  # sc_type=1 代表只看期刊/论文

            driver.get(url)
            time.sleep(random.uniform(3, 5))  # 多休息一会，学术网站比较敏感

            try:
                # 找到所有的论文卡片
                items = driver.find_elements(By.CSS_SELECTOR, ".result")

                if len(items) == 0:
                    print("      ⚠️ 本页无内容或遇到验证码，跳过...")
                    break

                for item in items:
                    try:
                        # 1. 抓取标题
                        title_elem = item.find_element(By.CSS_SELECTOR, "h3 a")
                        title = title_elem.text
                        link = title_elem.get_attribute("href")

                        # 2. 抓取摘要 (Content)
                        try:
                            abstract_elem = item.find_element(By.CSS_SELECTOR, ".c_abstract")
                            content = abstract_elem.text.replace("\n", "").replace("摘要：", "")
                        except:
                            content = "暂无摘要预览..."

                        # 3. 抓取作者和年份 (Era)
                        # 百度学术的作者信息比较杂，我们直接抓取下方的一行小字
                        try:
                            info_elem = item.find_element(By.CSS_SELECTOR, ".sc_info")
                            info_text = info_elem.text
                            # 简单的年份提取逻辑：找 19xx 或 20xx
                            import re
                            year_match = re.search(r'(19|20)\d{2}', info_text)
                            era = year_match.group(0) + "年" if year_match else "现代"

                            # 提取作者 (取第一个名字)
                            author = info_text.split("-")[0].strip()
                        except:
                            era = "现代"
                            author = "学术研究组"

                        # 4. 写入 CSV
                        with open(SAVE_FILE, 'a', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            # type 固定为 '学术研究'，方便前端显示不同颜色
                            writer.writerow([current_id, title, author, era, content, '学术研究', link])

                        print(f"      ✅ [{current_id}] {title[:20]}...")
                        current_id += 1

                    except Exception as e:
                        continue

            except Exception as e:
                print(f"      ❌ 页面出错: {e}")

    print(f"\n🎉 学术采集完成！数据已保存到 {SAVE_FILE}")
    print("💡 提示：百度学术如果弹出验证码，请手动点击一下，脚本会自动继续。")
    # driver.quit()


if __name__ == '__main__':
    main()