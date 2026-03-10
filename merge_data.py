import os
import json

# 配置目录
SOURCE_DIR = './data_en'  # 处理翻译后的英文目录
OUTPUT_DIR = './'         # 索引文件存放目录
CHUNK_SIZE = 1000         # 每 1000 条数据切分一个文件

def merge_and_index():
    all_items = []
    
    # 1. 读取所有 JSON 文件
    files = [f for f in os.listdir(SOURCE_DIR) if f.endswith('.json')]
    print(f"开始合并 {len(files)} 个文件...")

    for filename in files:
        with open(os.path.join(SOURCE_DIR, filename), 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                if isinstance(data, list):
                    all_items.extend(data)
            except Exception as e:
                print(f"读取 {filename} 出错: {e}")

    # 2. 提取并清洗所有标签 (支持数组和字符串混合)
    unique_tags = set()
    for item in all_items:
        tag_data = item.get('标签', [])
        if isinstance(tag_data, list):
            for t in tag_data:
                if t: unique_tags.add(str(t).strip())
        elif isinstance(tag_data, str) and tag_data:
            unique_tags.add(tag_data.strip())
    
    sorted_tags = sorted(list(unique_tags))
    print(f"提取到 {len(sorted_tags)} 个唯一标签")

    # 3. 数据切分 (Chunking) 以提升前端加载性能
    chunk_files = []
    for i in range(0, len(all_items), CHUNK_SIZE):
        chunk = all_items[i : i + CHUNK_SIZE]
        chunk_filename = f'all_data_{i // CHUNK_SIZE}.json'
        with open(os.path.join(OUTPUT_DIR, chunk_filename), 'w', encoding='utf-8') as f:
            json.dump(chunk, f, ensure_ascii=False)
        chunk_files.append(chunk_filename)

    # 4. 生成 data_index.json
    # 索引结构：包含文件列表和全局标签列表
    index_data = {
        "files": chunk_files,
        "tags": sorted_tags,
        "total": len(all_items)
    }
    
    # 为了兼容你之前的 index.html，我们依然可以只导出一个数组文件名列表
    # 但建议导出这个对象。如果保持原来的格式，就只写 chunk_files
    with open(os.path.join(OUTPUT_DIR, 'data_index.json'), 'w', encoding='utf-8') as f:
        json.dump(chunk_files, f, ensure_ascii=False)

    print(f"成功合并 {len(all_items)} 条数据，生成 {len(chunk_files)} 个分片文件。")

if __name__ == "__main__":
    merge_and_index()