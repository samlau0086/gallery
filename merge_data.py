import os
import json

def merge_jsons():
    combined = []
    data_dir = './data'
    chunk_size = 10000  # 每个分片的大小
    
    if not os.path.exists(data_dir):
        print("未找到 data 文件夹")
        return

    # 1. 遍历所有 JSON
    for filename in os.listdir(data_dir):
        if filename.endswith('.json'):
            with open(os.path.join(data_dir, filename), 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            # 清洗数据，确保搜索不报错
                            item['标题'] = item.get('标题') or ""
                            item['货号'] = str(item.get('货号') or "")
                            item['标签'] = item.get('标签') or filename.replace('.json', '')
                            combined.append(item)
                except Exception as e:
                    print(f"解析 {filename} 失败: {e}")

    # 2. 物理分片并极致压缩
    total = len(combined)
    file_list = []
    for i in range(0, total, chunk_size):
        chunk = combined[i : i + chunk_size]
        file_name = f'all_data_{len(file_list)}.json'
        with open(file_name, 'w', encoding='utf-8') as f:
            # separators 去掉 JSON 里的空格，大幅压缩体积
            json.dump(chunk, f, ensure_ascii=False, separators=(',', ':'))
        file_list.append(file_name)

    # 3. 生成索引文件
    with open('data_index.json', 'w', encoding='utf-8') as f:
        json.dump(file_list, f)
    
    print(f"处理完成：共 {total} 条，分片数 {len(file_list)}")

if __name__ == "__main__":
    merge_jsons()