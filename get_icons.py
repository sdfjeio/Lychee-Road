import os
import requests

# 图标保存路径
ICON_DIR = 'images'

# 这里我选了一组风格统一的扁平化彩色图标
ICONS = {
    "icon_station.png": "https://cdn-icons-png.flaticon.com/128/2069/2069670.png",  # 驿站/亭子
    "icon_lychee.png": "https://cdn-icons-png.flaticon.com/128/7354/7354366.png",  # 荔枝/产地
    "icon_mountain.png": "https://cdn-icons-png.flaticon.com/128/2913/2913520.png",  # 山峰/自然
    "icon_default.png": "https://cdn-icons-png.flaticon.com/128/684/684908.png"  # 默认地标
}


def main():
    if not os.path.exists(ICON_DIR):
        os.makedirs(ICON_DIR)

    print("🎨 开始下载图标素材...")

    for name, url in ICONS.items():
        save_path = os.path.join(ICON_DIR, name)
        try:
            print(f"   ⬇️ 正在下载: {name}...")
            content = requests.get(url, timeout=10).content
            with open(save_path, 'wb') as f:
                f.write(content)
        except Exception as e:
            print(f"   ❌ 下载失败 {name}: {e}")

    print("\n✅ 图标准备完毕！请检查 images 文件夹。")


if __name__ == '__main__':
    main()