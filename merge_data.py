import os
import json

def merge_jsons():
    combined = []
    data_dir = './data'
    
    if not os.path.exists(data_dir):
        print("Error: 'data' folder not found.")
        return

    for filename in os.listdir(data_dir):
        if filename.endswith('.json'):
            with open(os.path.join(data_dir, filename), 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            # 基础清洗，确保前端 React 不会因为缺少字段崩溃
                            item['标题'] = item.get('标题') or "无标题"
                            item['货号'] = str(item.get('货号') or "N/A")
                            item['标签'] = item.get('标签') or filename.replace('.json', '')
                            item['图片'] = item.get('图片') or []
                            combined.append(item)
                except Exception as e:
                    print(f"Skipping {filename}: {e}")

    with open('all_data.json', 'w', encoding='utf-8') as f:
        json.dump(combined, f, ensure_ascii=False)
    print(f"Success! Merged {len(combined)} items into all_data.json")

if __name__ == "__main__":
    merge_jsons()