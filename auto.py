import csv
import os
import time
import random
import requests
import base64
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# --- 配置区 ---
CSV_FILE = 'data.csv'
EXCEL_FILE = 'new_places.xlsx'
IMAGE_DIR = 'images'
SHOW_BROWSER = True


# --- 初始化浏览器 ---
def setup_driver():
    print("🚗 正在启动浏览器驱动...")
    chrome_options = Options()
    if not SHOW_BROWSER:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


# --- 获取下一个ID ---
def get_next_id():
    if not os.path.exists(CSV_FILE):
        return 1
    last_id = 0
    try:
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['id'] and row['id'].isdigit():
                    last_id = int(row['id'])
    except:
        pass
    return last_id + 1


# --- 🔥 修改点1：读取现有数据 (返回 名字:ID 的字典) ---
def get_existing_data():
    """
    返回一个字典，格式为 {'地名': 'ID'}
    这样我们不仅知道存在，还知道它的ID是多少，方便覆盖更新
    """
    data_map = {}
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['name']:
                    # 记录 名字 -> ID 的映射
                    data_map[row['name']] = row['id']
    return data_map


# --- 🔥 新增功能：更新CSV中的某一行 ---
def update_csv_row(target_id, new_row_data):
    """
    读取整个文件，找到对应ID的行进行替换，然后重写文件
    """
    rows = []
    # 1. 读取所有数据
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)  # 读取表头
        rows.append(header)
        for row in reader:
            # 如果这一行的ID等于我们要更新的ID，就用新数据替换
            if row[0] == str(target_id):
                rows.append(new_row_data)
            else:
                rows.append(row)

    # 2. 重新写入文件
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    print(f"    📝 ID:{target_id} 的数据已更新覆盖")


# --- 查坐标 (API) ---
def get_coordinates(place_name):
    url = "https://nominatim.openstreetmap.org/search"
    params = {'q': place_name, 'format': 'json', 'limit': 1, 'accept-language': 'zh-CN'}
    headers = {'User-Agent': 'Lizhidao_Project_Student_Demo'}
    try:
        res = requests.get(url, params=params, headers=headers, timeout=5)
        data = res.json()
        if data:
            return data[0]['lat'], data[0]['lon']
    except:
        pass
    return "0", "0"


# --- Selenium 下载图片 ---
def download_image_selenium(driver, keyword, save_name):
    print(f"    🔍 搜索图片: {keyword} ...")
    search_url = f"https://www.bing.com/images/search?q={keyword}"
    driver.get(search_url)
    time.sleep(random.uniform(2, 4))
    try:
        img_elements = driver.find_elements(By.CSS_SELECTOR, "img.mimg")
        if not img_elements:
            print("    ⚠️ 未找到图片元素")
            return False
        img_url = img_elements[0].get_attribute("src")
        save_path = os.path.join(IMAGE_DIR, save_name)

        if img_url.startswith("data:image"):
            base64_data = img_url.split(",")[1]
            with open(save_path, "wb") as f:
                f.write(base64.decodebytes(base64_data.encode()))
            print(f"    ✅ 图片更新成功 (Base64)")
            return True
        elif img_url.startswith("http"):
            res = requests.get(img_url, timeout=10)
            with open(save_path, "wb") as f:
                f.write(res.content)
            print(f"    ✅ 图片更新成功 (URL)")
            return True
    except Exception as e:
        print(f"    ❌ 下载出错: {e}")
    return False


# --- 主程序 ---
def main():
    print("🤖 交互式采集脚本启动...")
    if not os.path.exists(IMAGE_DIR): os.makedirs(IMAGE_DIR)
    if not os.path.exists(EXCEL_FILE):
        print(f"❌ 找不到 {EXCEL_FILE}")
        return

    driver = setup_driver()
    driver.minimize_window()

    try:
        df = pd.read_excel(EXCEL_FILE)
        # 获取 {名字: ID} 字典
        existing_map = get_existing_data()

        # 计算下一个新ID (用于新增数据)
        next_new_id = get_next_id()

        print(f"📊 Excel共有 {len(df)} 行数据...")

        for index, row in df.iterrows():
            place_name = str(row.iloc[0]).strip()
            place_type = str(row.iloc[1]).strip()
            place_desc = str(row.iloc[2]).strip()

            if not place_name or place_name == 'nan': continue

            # --- 🔥 修改点2：交互逻辑 ---
            target_id = None  # 这条数据最终使用的ID
            need_process = True  # 是否需要处理（抓取坐标图片等）

            if place_name in existing_map:
                # 发现重复！询问用户
                print(f"\n⚠️ 发现重复: 【{place_name}】 (ID: {existing_map[place_name]})")
                user_choice = input(f"   是否更新此条数据？(y/n/q退出): ").lower().strip()

                if user_choice == 'y':
                    print("   🔄 正在更新数据...")
                    target_id = existing_map[place_name]  # 使用旧ID覆盖
                    # 保持 need_process = True，继续往下走去抓取新数据
                elif user_choice == 'q':
                    print("👋 用户中止任务")
                    break
                else:
                    print("   ⏩ 跳过")
                    need_process = False  # 标记为不需要处理
            else:
                # 是新数据
                print(f"\n🆕 新增数据: 【{place_name}】 (ID: {next_new_id})")
                target_id = next_new_id
                next_new_id += 1  # 只有新增时，ID计数器才加1

            # --- 开始处理 (如果是新增 OR 用户选择了更新) ---
            if need_process and target_id:
                # 1. 查坐标 (重新查，因为可能你想更新坐标)
                lat, lng = get_coordinates(place_name)

                # 2. 下图片 (覆盖旧图片，文件名保持不变，还是 ID.jpg)
                img_filename = f"{target_id}.jpg"
                download_image_selenium(driver, f"{place_name} 风景", img_filename)

                # 3. 准备这一行的数据
                row_data = [target_id, place_name, lat, lng, place_type, place_desc, img_filename]

                # 4. 写入 CSV
                if place_name in existing_map:
                    # 如果是更新模式 -> 调用专门的更新函数
                    update_csv_row(target_id, row_data)
                else:
                    # 如果是新增模式 -> 直接追加到末尾
                    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow(row_data)
                    print(f"    📝 新增写入完成")
                    # 新增完后，把它加到内存的查重字典里，防止Excel里有两行一样的导致重复添加
                    existing_map[place_name] = str(target_id)

                time.sleep(1)

    finally:
        print("\n🏁 任务结束。")
        driver.quit()


if __name__ == '__main__':
    main()