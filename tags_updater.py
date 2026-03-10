import os
import json

DATA_DIR = r'C:\Users\samla\SynologyDrive\聊单\gallery\data'

# 定义关键词映射
TAG_MAP = {
    'clothing': 'Clothing',
    'pants': 'Clothing',
    'bag': 'Bags',
    'shoes': 'Shoes',
    'watch': 'Watches',
    'jewelry': 'Jewelry',
    'belt': 'Accessories'
}

def process_json_files():
    files = [f for f in os.listdir(DATA_DIR) if f.endswith('.json') and f != 'data_index.json']
    
    for filename in files:
        file_path = os.path.join(DATA_DIR, filename)
        
        # 确定该文件对应的基础标签
        assigned_tag = "Other"
        for keyword, tag in TAG_MAP.items():
            if keyword in filename.lower():
                assigned_tag = tag
                break
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            modified = False
            if isinstance(data, list):
                for item in data:
                    # 核心修改：将标签转为数组格式 [cite: 10, 24]
                    current_tags = item.get('标签', [])
                    if isinstance(current_tags, str):
                        current_tags = [current_tags] if current_tags else []
                    
                    if assigned_tag not in current_tags:
                        current_tags.append(assigned_tag)
                        item['标签'] = current_tags
                        modified = True
            
            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                print(f"Updated: {filename} with multiple tags support")
        except Exception as e:
            print(f"Error {filename}: {e}")

if __name__ == "__main__":
    process_json_files()