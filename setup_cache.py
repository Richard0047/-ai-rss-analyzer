import os
import json
import time
import shutil

def setup_cache():
    # 定义所有可能的缓存文件位置
    possible_locations = [
        os.path.join('src', 'data'),  # 主要位置
        os.path.join(os.getcwd(), 'src', 'data'),  # 当前工作目录
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src', 'data'),  # 项目根目录
    ]
    
    print("=== Cleaning Cache Files ===")
    
    # 清理所有位置的缓存文件
    for base_dir in possible_locations:
        if os.path.exists(base_dir):
            print(f"\nChecking directory: {base_dir}")
            # 清理所有相关文件
            for filename in os.listdir(base_dir):
                if filename.startswith('news_cache'):
                    file_path = os.path.join(base_dir, filename)
                    try:
                        os.remove(file_path)
                        print(f"Removed: {file_path}")
                    except Exception as e:
                        print(f"Error removing {file_path}: {e}")
    
    # 确保主缓存目录存在
    cache_dir = os.path.join('src', 'data')
    os.makedirs(cache_dir, exist_ok=True)
    print(f"\nCreated/verified directory: {cache_dir}")
    
    # 创建新的缓存文件
    cache_file = os.path.join(cache_dir, 'news_cache.json')
    initial_cache = {
        "items": {},
        "last_cleanup": time.time(),
        "version": "1.0"
    }
    
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(initial_cache, f, ensure_ascii=False, indent=2)
    print(f"Created new cache file: {cache_file}")
    
    # 设置权限
    os.chmod(cache_file, 0o644)
    print(f"Set permissions on cache file to 644")
    
    # 验证
    with open(cache_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        print(f"\nVerified cache file structure: {data.keys()}")
        print(f"Cache items count: {len(data['items'])}")

if __name__ == "__main__":
    print("Starting cache cleanup and initialization...")
    setup_cache()
    print("\nCache setup completed!")