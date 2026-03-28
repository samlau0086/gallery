import os
import json
import argparse
import glob
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
from DrissionPage import SessionPage

# --- 配置 ---
DEFAULT_MAX_WORKERS = 5 
TIMEOUT = 30

def get_authenticated_session(sample_url):
    print(f"正在尝试绕过验证: {sample_url}")
    page = SessionPage()
    page.get(sample_url)
    
    if 'image' in page.response.headers.get('Content-Type', ''):
        print("验证通过，已获取 Session。")
        return page.session
    else:
        print("验证失败，可能需要手动干预或检查 URL。")
        return page.session

def download_image(session, url, item_id, json_name, save_dir):
    original_filename = os.path.basename(urlparse(url).path)
    new_filename = f"{json_name}_{item_id}_{original_filename}"
    file_path = os.path.join(save_dir, new_filename)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://xcimg.szwego.com/" 
    }

    if os.path.exists(file_path):
        current_size = os.path.getsize(file_path)
        if current_size >= 2048:
            print(f" [跳过] 资源已存在: {new_filename}")
            return 
        else:
            try:
                os.remove(file_path)
            except:
                pass
            print(f" [重下] 修正损坏文件: {new_filename}")

    try:
        response = session.get(url, headers=headers, stream=True, timeout=TIMEOUT)
        content_type = response.headers.get('Content-Type', '').lower()
        if 'text/html' in content_type:
            print(f" [拦截] {new_filename} 仍需验证")
            return

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
                # --- 修改处：通过切片 [:1] 仅获取图片列表的第一张 ---
                images = item.get("图片", [])
                if images:
                    img_url = images[0]
                    all_tasks.append((img_url, art_no, json_base_name))

    if all_tasks:
        auth_session = get_authenticated_session(all_tasks[0][0])
        print(f"开始下载 {len(all_tasks)} 张封面图...")
        with ThreadPoolExecutor(max_workers=args.threads) as executor:
            for task in all_tasks:
                executor.submit(download_image, auth_session, *task, args.output)

if __name__ == "__main__":
    main()