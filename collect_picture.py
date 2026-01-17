import os
import csv
import time
import random
import requests
import base64
import hashlib
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# --- 🛠️ 暴力采集配置区 ---
SAVE_DIR = 'images_history'
CSV_FILE = 'gallery.csv'
IMAGES_PER_KEYWORD = 3  # 🔥 每个关键词抓几张图？(建议 3-5 张)

# --- 1. 关键词矩阵 (随意扩充，脚本会自动排列组合) ---
# A. 核心主体
SUBJECTS = [
    "荔枝道", "蜀道", "子午谷", "秦岭", "剑门关",  # 地理
    "唐玄宗", "杨贵妃", "杜牧", "驿使", "骑马俑",  # 人物/角色
    "驿站", "栈道", "望楼", "长安城", "古道",  # 建筑
    "荔枝", "马匹", "马鞍", "通关文牒"  # 物品
]

# B. 历史修饰词
ERAS = [
    "唐代", "古代", "宋代", "历史复原", "遗址"
]

# C. 艺术形式 (确保搜出来的是古风/文物)
STYLES = [
    "壁画", "山水画", "线描图", "文物", "陶俑",
    "古地图", "拓片", "敦煌画风", "界画"
]


# --- 2. 浏览器初始化 ---
def setup_driver():
    print("🚀 启动[PRO版]影像采集引擎...")
    chrome_options = Options()
    # chrome_options.add_argument("--headless") # 想要后台静默运行就把这行注释去掉
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)


# --- 3. 生成去重指纹 ---
def get_file_hash(content):
    return hashlib.md5(content).hexdigest()


# --- 4. 核心下载逻辑 ---
def download_images_for_keyword(driver, keyword, start_id, existing_hashes):
    print(f"\n🔍 正在通过矩阵搜索: 【{keyword}】 (目标: {IMAGES_PER_KEYWORD}张)")

    # 必应搜索 (强制显示大图)
    url = f"https://www.bing.com/images/search?q={keyword}&qft=+filterui:imagesize-large"
    driver.get(url)

    # 疯狂向下滚动，加载更多图片
    for _ in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

    downloaded_count = 0
    try:
        # 找到所有图片缩略图
        img_elements = driver.find_elements(By.CSS_SELECTOR, "img.mimg")

        for img in img_elements:
            if downloaded_count >= IMAGES_PER_KEYWORD:
                break

            try:
                # 获取链接
                src = img.get_attribute("src")
                if not src: continue

                # 下载内容
                content = None
                if src.startswith("data:image"):
                    content = base64.decodebytes(src.split(",")[1].encode())
                elif src.startswith("http"):
                    try:
                        res = requests.get(src, timeout=5)
                        if res.status_code == 200:
                            content = res.content
                    except:
                        continue

                if not content: continue

                # 图片查重 (计算哈希值)
                img_hash = get_file_hash(content)
                if img_hash in existing_hashes:
                    # print("      重复图片，跳过...")
                    continue

                # 保存文件
                filename = f"history_{start_id}.jpg"
                filepath = os.path.join(SAVE_DIR, filename)

                with open(filepath, "wb") as f:
                    f.write(content)

                # 写入 CSV
                with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    # 自动生成一段描述
                    desc = f"关于{keyword}的历史影像资料，反映了当时的文化风貌。"
                    writer.writerow([start_id, keyword, desc, f"{SAVE_DIR}/{filename}", '文物影像'])

                # 更新状态
                existing_hashes.add(img_hash)
                print(f"      ✅ [{downloaded_count + 1}/{IMAGES_PER_KEYWORD}] 保存成功: {filename}")

                start_id += 1
                downloaded_count += 1
                time.sleep(0.5)  # 稍微休息防封

            except Exception as e:
                continue

    except Exception as e:
        print(f"      ❌ 搜索页出错: {e}")

    return start_id


# --- 主程序 ---
def main():
    if not os.path.exists(SAVE_DIR): os.makedirs(SAVE_DIR)

    # 初始化 CSV
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'title', 'desc', 'filename', 'type'])

    driver = setup_driver()

    # 读取当前 ID
    current_id = 3000
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            rows = list(csv.reader(f))
            if len(rows) > 1 and rows[-1][0].isdigit():
                current_id = int(rows[-1][0]) + 1

    # 读取已有图片的哈希，防止重复下载
    existing_hashes = set()
    # (这里为了脚本简化，暂不读取本地已有文件的哈希，仅在单次运行中去重)

    # --- 🔥 矩阵生成器 ---
    # 随机打乱顺序，保证每次跑都能下到不一样的东西
    random.shuffle(SUBJECTS)

    count = 0
    total_combinations = len(SUBJECTS) * len(STYLES)  # 大概 20 * 9 = 180 种组合

    print(f"🎰 预计生成搜索组合: {total_combinations} 种")
    print(f"📸 预计最大采集数量: {total_combinations * IMAGES_PER_KEYWORD} 张")

    for subject in SUBJECTS:
        for style in STYLES:
            # 随机选取一个朝代词，或者不加
            era = random.choice(ERAS)

            # 组合出关键词，例如：“唐代 荔枝道 壁画”
            keyword = f"{era} {subject} {style}"

            # 执行采集
            current_id = download_images_for_keyword(driver, keyword, current_id, existing_hashes)

            count += 1
            # 每搜完一个词，休息一下
            print(f"💤 休息 2 秒...")
            time.sleep(2)

    print("\n🎉 海量采集完成！")
    driver.quit()


if __name__ == '__main__':
    main()