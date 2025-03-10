from typing import List, Dict, Optional, Union
import logging
from datetime import datetime, timedelta
from pymongo import MongoClient, ASCENDING, DESCENDING, UpdateOne
from pymongo.errors import DuplicateKeyError, BulkWriteError
from ..config import Config

class Database:
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        
        try:
            # 连接设置
            client_options = {
                'serverSelectionTimeoutMS': 30000,     # 增加服务器选择超时
                'connectTimeoutMS': 30000,             # 增加连接超时
                'socketTimeoutMS': 30000,              # 增加套接字超时
                'ssl': True,
                'ssl_cert_reqs': 'CERT_NONE',
                'retryWrites': True,
                'tlsAllowInvalidCertificates': True,
                'directConnection': False,             # 禁用直接连接
                'connect': True,                       # 立即连接
                'maxPoolSize': 1,                      # 减小连接池大小
                'waitQueueTimeoutMS': 30000           # 增加等待队列超时
            }
            
            # 连接MongoDB Atlas
            self.client = MongoClient(
                self.config.DATABASE['uri'],
                **client_options
            )
            
            # 强制连接检查
            self.db = self.client.get_database(self.config.DATABASE['name'])
            self.collection = self.db.get_collection(self.config.DATABASE['collection'])
            
            # 测试连接
            self.client.admin.command('ping')
            self.logger.info("成功连接到MongoDB Atlas")
            
            # 创建索引
            self._create_indexes()
            
        except Exception as e:
            self.logger.error(f"MongoDB连接失败: {str(e)}")
            raise

    def _create_indexes(self):
        """创建必要的索引"""
        try:
            # 创建唯一索引防止重复新闻
            self.collection.create_index(
                [('unique_id', ASCENDING)],
                unique=True
            )
            
            # 创建复合索引支持查询
            self.collection.create_index([
                ('published', DESCENDING),
                ('source', ASCENDING),
                ('language', ASCENDING),
                ('tags', ASCENDING)
            ])
            
            # 创建文本索引支持全文搜索
            self.collection.create_index([
                ('title', 'text'),
                ('summary', 'text'),
                ('keywords', 'text')
            ])
            
            self.logger.info("数据库索引创建完成")
            
        except Exception as e:
            self.logger.error(f"创建索引时出错: {str(e)}")

    def save_item(self, item: Dict) -> bool:
        """保存单条新闻"""
        try:
            # 添加更新时间
            item['updated_at'] = datetime.now().isoformat()
            
            # 使用unique_id作为唯一标识，如果存在则更新
            result = self.collection.update_one(
                {'unique_id': item['unique_id']},
                {'$set': item},
                upsert=True
            )
            
            return True
        except DuplicateKeyError:
            self.logger.info(f"新闻已存在: {item.get('title', '')}")
            return False
        except Exception as e:
            self.logger.error(f"保存新闻时出错: {str(e)}")
            return False

    def save_batch(self, items: List[Dict]) -> int:
        """批量保存新闻"""
        try:
            if not items:
                return 0
                
            # 准备批量更新操作
            operations = []
            for item in items:
                item['updated_at'] = datetime.now().isoformat()
                operations.append(
                    UpdateOne(
                        {'unique_id': item['unique_id']},
                        {'$set': item},
                        upsert=True
                    )
                )
            
            # 执行批量操作
            result = self.collection.bulk_write(operations, ordered=False)
            
            self.logger.info(f"批量保存完成: {result.upserted_count} 新增, {result.modified_count} 更新")
            return result.upserted_count + result.modified_count
            
        except BulkWriteError as e:
            self.logger.error(f"批量保存时出错: {str(e.details)}")
            return len(items) - len(e.details['writeErrors'])
        except Exception as e:
            self.logger.error(f"批量保存时出错: {str(e)}")
            return 0

    def get_latest_news(self, 
                       limit: int = 100, 
                       tags: Optional[List[str]] = None,
                       language: Optional[str] = None,
                       processed_only: bool = True
                       ) -> List[Dict]:
        """获取最新新闻"""
        query = {}
        
        if tags:
            query['tags'] = {'$in': tags}
        
        if language:
            query['language'] = language
            
        if processed_only:
            query['text_processed'] = True
            
        return list(self.collection.find(
            query,
            {'_id': 0}
        ).sort('published', DESCENDING).limit(limit))

    def get_unprocessed_news(self, 
                           limit: int = 50,
                           tags: Optional[List[str]] = None
                           ) -> List[Dict]:
        """获取未经处理的新闻"""
        query = {
            'text_processed': {'$ne': True}
        }
        
        if tags:
            query['tags'] = {'$in': tags}
            
        return list(self.collection.find(
            query,
            {'_id': 0}
        ).limit(limit))

    def search_news(self,
                   keyword: str,
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None,
                   tags: Optional[List[str]] = None,
                   limit: int = 50
                   ) -> List[Dict]:
        """搜索新闻"""
        query = {
            '$text': {'$search': keyword}
        }
        
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query['$gte'] = start_date
            if end_date:
                date_query['$lte'] = end_date
            query['published'] = date_query
            
        if tags:
            query['tags'] = {'$in': tags}
            
        return list(self.collection.find(
            query,
            {'_id': 0, 'score': {'$meta': 'textScore'}}
        ).sort([('score', {'$meta': 'textScore'})]).limit(limit))

    def get_stats(self) -> Dict:
        """获取数据统计信息"""
        try:
            total_count = self.collection.count_documents({})
            processed_count = self.collection.count_documents({'text_processed': True})
            ai_processed_count = self.collection.count_documents({'ai_processed': True})
            
            # 获取最近24小时的新闻数量
            yesterday = datetime.now() - timedelta(days=1)
            recent_count = self.collection.count_documents({
                'created_at': {'$gte': yesterday.isoformat()}
            })
            
            return {
                'total_news': total_count,
                'processed_news': processed_count,
                'ai_processed_news': ai_processed_count,
                'recent_24h': recent_count,
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"获取统计信息时出错: {str(e)}")
            return {}

    def close(self):
        """关闭数据库连接"""
        if self.client:
            self.client.close() 