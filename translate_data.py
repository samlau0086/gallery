import os
import json
import sqlite3
import threading
import time
import concurrent.futures
from openai import OpenAI

# ================= 配置区 =================
client = OpenAI(
    api_key="sk-wHAkpaDwNrUKlju4jGnBKeFBbLg3kpIN6vu7hIALSdLGJRLM", 
    base_url="https://api.bianxie.ai/v1" 
)

SOURCE_DIR = "./data"
TARGET_DIR = "./data_en"
MODEL = "gpt-3.5-turbo"
CONCURRENT_WORKERS = 3  # 可以稍微调高到 3
# ==========================================

os.makedirs(TARGET_DIR, exist_ok=True)

db_lock = threading.Lock()
_db_conn = None

# 统计计数器
stats_lock = threading.Lock()
processed_count = 0
api_request_count = 0
cache_hit_count = 0

def get_db_conn():
    global _db_conn
    with db_lock:
        if _db_conn is None:
            _db_conn = sqlite3.connect('translation_v4.db', check_same_thread=False, timeout=30)
            _db_conn.execute('PRAGMA journal_mode=DELETE;') 
            _db_conn.execute('CREATE TABLE IF NOT EXISTS cache (original TEXT PRIMARY KEY, translated TEXT)')
            _db_conn.commit()
        return _db_conn

def get_cached_translation(text):
    global cache_hit_count
    conn = get_db_conn()
    with db_lock:
        cursor = conn.cursor()
        cursor.execute('SELECT translated FROM cache WHERE original = ?', (text,))
        result = cursor.fetchone()
        if result:
            with stats_lock: cache_hit_count += 1
        return result[0] if result else None

def save_to_cache(original, translated):
    conn = get_db_conn()
    with db_lock:
        try:
            conn.execute('INSERT OR REPLACE INTO cache (original, translated) VALUES (?, ?)', (original, translated))
            conn.commit()
        except Exception as e:
            print(f"\n[数据库错误] {e}")

def translate_text(text):
    global api_request_count
    if not text or not str(text).strip() or str(text).isdigit():
        return text
    
    text_str = str(text).strip()
    cached = get_cached_translation(text_str)
    if cached:
        return cached

    # 没命中缓存，才打印 API 请求日志
    with stats_lock:
        api_request_count += 1
        print(f"  [API 调用] 正在翻译内容: {text_str[:15]}...")

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": "Professional translator. Concise English only."},
                    {"role": "user", "content": text_str}
                ],
                temperature=0,
                timeout=25
            )
            translated = response.choices[0].message.content.strip()
            save_to_cache(text_str, translated)
            return translated
        except Exception as e:
            print(f"  [API 重试 {attempt+1}] {text_str[:10]}: {e}")
            time.sleep(2)
    return text_str

def process_file(filename, total_files):
    global processed_count
    if not filename.endswith('.json'):
        return

    # 1. 立即打印开始处理的日志，这样你就知道脚本没死
    print(f"▶ 正在读取文件: {filename}")

    base_name = filename.replace('.json', '')
    translated_name = translate_text(base_name)
    clean_name = "".join([c if c.isalnum() or c in ('-', '_') else "_" for c in translated_name]).lower()
    translated_filename = f"{clean_name}.json"
    
    target_path = os.path.join(TARGET_DIR, translated_filename)

    if os.path.exists(target_path):
        with stats_lock:
            processed_count += 1
        print(f"⏭  跳过已存在文件: {translated_filename}")
        return

    try:
        src_path = os.path.join(SOURCE_DIR, filename)
        with open(src_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    item['标题'] = translate_text(item.get('标题', ''))
                    item['标签'] = translate_text(item.get('标签', ''))

                with open(target_path, 'w', encoding='utf-8') as fw:
                    json.dump(data, fw, ensure_ascii=False, indent=2)

        with stats_lock:
            processed_count += 1
        print(f"✔  完成处理 [{processed_count}/{total_files}]: {translated_filename}")
        
    except Exception as e:
        print(f"❌ 处理文件 {filename} 失败: {e}")

def main():
    if not os.path.exists(SOURCE_DIR):
        print(f"错误: 找不到源文件夹 {SOURCE_DIR}")
        return

    files = [f for f in os.listdir(SOURCE_DIR) if f.endswith('.json')]
    total = len(files)
    
    print("=" * 60)
    print(f"项目名称: 英文相册数据翻译")
    print(f"任务总量: {total} 个文件")
    print(f"并发设置: {CONCURRENT_WORKERS}")
    print("提示: 如果半天没动，通常是中转 API 响应慢，请耐心等待...")
    print("=" * 60 + "\n")

    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
        executor.map(lambda f: process_file(f, total), files)
    
    if _db_conn:
        _db_conn.close()
    
    print("\n" + "=" * 60)
    print(f"🎉 任务全部完成!")
    print(f"总处理数: {processed_count}")
    print(f"API 调用: {api_request_count} 次")
    print(f"缓存节省: {cache_hit_count} 次")
    print("=" * 60)

if __name__ == "__main__":
    main()