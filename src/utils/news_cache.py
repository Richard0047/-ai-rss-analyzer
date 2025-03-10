import json
import hashlib
import os
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from src.config import Config

class NewsCache:
    def __init__(self, cache_file: str = 'news_cache.json', expire_days: int = 7):
        # 首先初始化 logger
        self.logger = logging.getLogger(__name__)
        
        # 获取项目根目录的绝对路径
        current_file = os.path.abspath(__file__)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
        self.logger.info(f"Project root: {project_root}")
        
        # 设置缓存文件路径
        self.cache_file = os.path.join(project_root, "src", "data", cache_file)
        self.logger.info(f"Cache file path: {self.cache_file}")
        
        # 检查所有可能的缓存位置
        possible_locations = [
            os.path.join(project_root, "src", "data", cache_file),  # 主要位置
            os.path.join(os.getcwd(), "src", "data", cache_file),   # 当前工作目录
        ]
        
        # 如果在外部SSD上运行，添加外部SSD路径
        if '/Volumes/Extreme SSD' in project_root:
            possible_locations.append("/Volumes/Extreme SSD/deploy/src/data/" + cache_file)
            self.logger.info("Added external SSD location to search paths")
        
        # 查找现有缓存
        existing_cache = None
        max_items = 0
        
        self.logger.info("=== Checking Cache Locations ===")
        for loc in possible_locations:
            self.logger.info(f"Checking location: {loc}")
            if os.path.exists(loc):
                try:
                    with open(loc, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if not isinstance(data, dict) or 'items' not in data:
                            self.logger.warning(f"Invalid cache structure in {loc}")
                            continue
                            
                        items_count = len(data.get('items', {}))
                        self.logger.info(f"Found {items_count} items in {loc}")
                        
                        # 验证缓存项的格式
                        is_valid = True
                        for key, item in data['items'].items():
                            if not isinstance(item, dict) or 'title' not in item or 'timestamp' not in item:
                                self.logger.warning(f"Invalid cache item format: {key}")
                                is_valid = False
                                break
                        
                        if not is_valid:
                            continue
                            
                        if items_count > max_items:
                            existing_cache = data
                            max_items = items_count
                            self.logger.info(f"Found larger cache with {items_count} items")
                            
                except json.JSONDecodeError as e:
                    self.logger.error(f"JSON decode error in {loc}: {str(e)}")
                    backup_file = f"{loc}.backup"
                    try:
                        os.rename(loc, backup_file)
                        self.logger.info(f"Renamed corrupted cache file to {backup_file}")
                    except Exception as rename_error:
                        self.logger.error(f"Failed to rename corrupted cache file: {str(rename_error)}")
                except Exception as e:
                    self.logger.error(f"Error reading cache from {loc}: {str(e)}")
        
        # 如果找到了现有缓存，使用它
        if existing_cache:
            self.logger.info(f"Using existing cache with {max_items} items")
            self.cache = existing_cache
        else:
            self.logger.info("Creating new cache")
            self.cache = {
                'items': {},
                'last_cleanup': time.time(),
                'version': '1.0'
            }
        
        self.expire_days = expire_days
        
        # 确保缓存目录存在
        cache_dir = os.path.dirname(self.cache_file)
        os.makedirs(cache_dir, exist_ok=True)
        
        # 立即保存以验证写入权限
        try:
            self._save_cache()
            self.logger.info("Successfully initialized cache")
        except Exception as e:
            self.logger.error(f"Failed to save initial cache: {str(e)}")
            raise

    def _save_cache(self):
        """保存缓存到文件"""
        try:
            self.logger.info(f"=== Saving Cache ===")
            self.logger.info(f"Target file: {self.cache_file}")
            
            # 验证缓存数据完整性
            if not isinstance(self.cache, dict) or 'items' not in self.cache:
                raise ValueError("Invalid cache structure")
            
            items_count = len(self.cache['items'])
            self.logger.info(f"Items count: {items_count}")
            
            # 创建临时文件
            temp_file = f"{self.cache_file}.tmp"
            self.logger.info(f"Writing to temp file: {temp_file}")
            
            # 确保目标目录存在
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            
            # 写入临时文件
            with open(temp_file, 'w', encoding='utf-8') as f:
                json_str = json.dumps(self.cache, ensure_ascii=False, indent=2)
                f.write(json_str)
                f.flush()
                os.fsync(f.fileno())
            
            # 验证临时文件
            with open(temp_file, 'r', encoding='utf-8') as f:
                temp_data = json.loads(f.read())
                if not isinstance(temp_data, dict) or 'items' not in temp_data:
                    raise ValueError("Verification failed: invalid data structure in temp file")
                if len(temp_data['items']) != items_count:
                    raise ValueError(f"Verification failed: temp file has {len(temp_data['items'])} items, memory has {items_count} items")
            
            # 如果原文件存在，创建备份
            if os.path.exists(self.cache_file):
                backup_file = f"{self.cache_file}.bak"
                try:
                    os.replace(self.cache_file, backup_file)
                    self.logger.info(f"Created backup: {backup_file}")
                except Exception as e:
                    self.logger.warning(f"Failed to create backup: {str(e)}")
            
            # 原子性地替换文件
            os.replace(temp_file, self.cache_file)
            self.logger.info("=== Cache Saved Successfully ===")
            
        except Exception as e:
            self.logger.error(f"Failed to save cache: {str(e)}", exc_info=True)
            if 'temp_file' in locals() and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    self.logger.info("Cleaned up temp file")
                except Exception as cleanup_error:
                    self.logger.error(f"Failed to clean up temp file: {str(cleanup_error)}")
            raise

    def _generate_hash(self, news: Dict) -> str:
        """生成新闻的唯一标识"""
        # 使用更多字段来确保唯一性
        content = f"{news['title']}{news.get('link', '')}{news.get('source', '')}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
        
    def _cleanup_expired(self):
        """清理过期缓存"""
        now = time.time()
        # 每天只清理一次
        if now - self.cache['last_cleanup'] < 86400:  # 24小时
            return
            
        expire_time = now - (self.expire_days * 86400)  # 7天前
        original_count = len(self.cache['items'])
        self.cache['items'] = {
            k: v for k, v in self.cache['items'].items()
            if v['timestamp'] > expire_time
        }
        new_count = len(self.cache['items'])
        if new_count != original_count:
            self.logger.info(f"Cleaned up {original_count - new_count} expired items")
        
        self.cache['last_cleanup'] = now
        self._save_cache()
        
    def add_news(self, news: Dict):
        """添加新闻到缓存"""
        try:
            news_hash = self._generate_hash(news)
            self.logger.debug(f"Generated hash for news: {news_hash}")
            
            if news_hash not in self.cache['items']:
                self.logger.info(f"Adding new news to cache: {news['title']} (hash: {news_hash})")
                self.cache['items'][news_hash] = {
                    'title': news['title'],
                    'source': news.get('source', ''),
                    'timestamp': time.time()
                }
                
                # 立即保存到文件
                try:
                    self._save_cache()
                    self.logger.info("Cache saved successfully")
                except Exception as save_error:
                    self.logger.error("Failed to save cache!", exc_info=True)
                    raise  # 重新抛出异常
                
            else:
                self.logger.debug(f"News already in cache: {news['title']} (hash: {news_hash})")
            
        except Exception as e:
            self.logger.error(f"Error adding news to cache: {str(e)}", exc_info=True)
            raise  # 重新抛出异常以确保调用者知道操作失败
        
    def is_exists(self, news: Dict) -> bool:
        """检查新闻是否已存在"""
        try:
            news_hash = self._generate_hash(news)
            exists = news_hash in self.cache['items']
            if exists:
                cached_item = self.cache['items'][news_hash]
                self.logger.debug(f"Found news in cache: {news['title']}")
                self.logger.debug(f"Cached item: {cached_item}")
            return exists
        except Exception as e:
            self.logger.error(f"Error checking news existence: {str(e)}", exc_info=True)
            return False
        
    def filter_and_sort_news(self, news_list: List[Dict], limit: int = 15) -> List[Dict]:
        """过滤未推送的新闻并按评分排序"""
        # 过滤出未推送的新闻
        unsent_news = [
            news for news in news_list 
            if not self.is_exists(news)
        ]
        
        # 按评分排序
        sorted_news = sorted(
            unsent_news,
            key=lambda x: float(x.get('article_score', 0)),
            reverse=True
        )
        
        # 返回前N条
        return sorted_news[:limit]