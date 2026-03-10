import os
import json

# 配置目录
SOURCE_DIR = './data' 
OUTPUT_DIR = './'         
CHUNK_SIZE = 1000  # 每 1000 条数据切分一个文件

def merge_and_index():
    all_items = []
    
    if not os.path.exists(SOURCE_DIR):
        print(f"找不到目录: {SOURCE_DIR}")
        return

    # 1. 读取并合并所有翻译后的数据
    files = [f for f in os.listdir(SOURCE_DIR) if f.endswith('.json')]
    print(f"正在读取 {len(files)} 个文件...")

    for filename in files:
        with open(os.path.join(SOURCE_DIR, filename), 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                if isinstance(data, list):
                    all_items.extend(data)
            except Exception as e:
                print(f"读取 {filename} 失败: {e}")

    # 2. 提取全局唯一标签 (用于前端导航栏)
    unique_tags = set()
    for item in all_items:
        tags = item.get('标签', [])
        # 兼容处理：确保不管是字符串还是数组都能被正确读入 set
        if isinstance(tags, list):
            for t in tags:
                if t: unique_tags.add(str(t).strip())
        elif isinstance(tags, str) and tags:
            unique_tags.add(tags.strip())
            # 顺便把 item 里的字符串转成数组，统一格式
            item['标签'] = [tags.strip()]

    sorted_tags = sorted(list(unique_tags))
    print(f"共提取到 {len(sorted_tags)} 个分类标签")

    # 3. 物理切分分片文件 (保留数组格式)
    chunk_files = []
    for i in range(0, len(all_items), CHUNK_SIZE):
        chunk = all_items[i : i + CHUNK_SIZE]
        chunk_filename = f'all_data_{i // CHUNK_SIZE}.json'
        with open(os.path.join(OUTPUT_DIR, chunk_filename), 'w', encoding='utf-8') as f:
            # 这里的 json.dump 会完整保留数组结构
            json.dump(chunk, f, ensure_ascii=False)
        chunk_files.append(chunk_filename)

    # 4. 生成 data_index.json
    with open(os.path.join(OUTPUT_DIR, 'data_index.json'), 'w', encoding='utf-8') as f:
        json.dump(chunk_files, f, ensure_ascii=False)

    print(f"✅ 任务完成！总条数: {len(all_items)}，分片数: {len(chunk_files)}")

if __name__ == "__main__":
    merge_and_index()