import os
import json
import argparse
import glob
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
from DrissionPage import SessionPage

# --- 配置 ---
DEFAULT_MAX_WORKERS = 5 # 遇到验证码时建议线程不要开太高，避免触发更高频率限制
TIMEOUT = 30

def get_authenticated_session(sample_url):
    """
    使用 DrissionPage 模拟浏览器通过 JS 验证并获取 Cookie
    """
    print(f"正在尝试绕过验证: {sample_url}")
    page = SessionPage()
    # 访问一次图片链接，它会自动处理 JS 注入和跳转
    page.get(sample_url)
    
    # 检查是否成功（如果返回的是图片内容，则说明通过）
    if 'image' in page.response.headers.get('Content-Type', ''):
        print("验证通过，已获取 Session。")
        return page.session
    else:
        print("验证失败，可能需要手动干预或检查 URL。")
        return page.session

def download_image(session, url, item_id, json_name, save_dir):
    """
    使用带有验证 Cookie 的 session 下载图片
    新增：如果图片已存在且 > 2KB，则彻底跳过。
    """
    # 提取原文件名并构造新文件名
    original_filename = os.path.basename(urlparse(url).path)
    new_filename = f"{json_name}_{item_id}_{original_filename}"
    file_path = os.path.join(save_dir, new_filename)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://xcimg.szwego.com/" 
    }

    # --- 核心逻辑：跳过检测 ---
    if os.path.exists(file_path):
        current_size = os.path.getsize(file_path)
        
        # 判定条件：如果文件大于 2KB，认为已经下载成功（或者是之前留下的完整图片）
        if current_size >= 2048:
            print(f" [跳过] 资源已存在: {new_filename}")
            return # 直接结束函数，不发起请求
        else:
            # 如果文件很小，大概率是上次报错的脚本，删除它以便重新获取
            try:
                os.remove(file_path)
            except:
                pass
            print(f" [重下] 修正损坏文件: {new_filename}")

    try:
        # 发起请求
        response = session.get(url, headers=headers, stream=True, timeout=TIMEOUT)
        
        # 检查是否依然被防火墙拦截 (HTML 而不是 Image)
        content_type = response.headers.get('Content-Type', '').lower()
        if 'text/html' in content_type:
            print(f" [拦截] {new_filename} 仍需验证")
            return

        # 写入文件
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        print(f" [成功] 下载完成: {new_filename}")

    except Exception as e:
        print(f" [失败] {new_filename}: {e}")
        
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", default=".")
    parser.add_argument("-o", "--output", default="downloads")
    parser.add_argument("-t", "--threads", type=int, default=DEFAULT_MAX_WORKERS)
    args = parser.parse_args()

    if not os.path.exists(args.output): os.makedirs(args.output)

    json_files = glob.glob(os.path.join(args.input, "*.json"))
    if not json_files: return

    all_tasks = []
    for jf in json_files:
        json_base_name = os.path.splitext(os.path.basename(jf))[0]
        with open(jf, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                art_no = item.get("货号", "no-art")
                for img_url in item.get("图片", []):
                    all_tasks.append((img_url, art_no, json_base_name))

    # --- 核心步骤：先获取一个带验证信息的 Session ---
    if all_tasks:
        auth_session = get_authenticated_session(all_tasks[0][0])
        
        print(f"开始下载 {len(all_tasks)} 张图片...")
        with ThreadPoolExecutor(max_workers=args.threads) as executor:
            for task in all_tasks:
                executor.submit(download_image, auth_session, *task, args.output)

if __name__ == "__main__":
    main()