import logging
import asyncio
from typing import Dict, List
from tqdm import tqdm
from ..utils.wechat import WeChatNotifier
from ..processors.ai_processor import AIProcessor
from src.utils.news_cache import NewsCache

class NotificationProcessor:
    def __init__(self, test_mode=True):  # 默认使用测试模式
        self.logger = logging.getLogger(__name__)
        self.wechat = WeChatNotifier()
        self.ai_processor = AIProcessor()
        self.test_mode = test_mode
        
        # 重试配置
        self.max_retries = 3
        self.retry_delay = 5  # 秒
        
        self.news_cache = NewsCache()
        
    async def process_and_send(self, news_items: Dict[str, List[Dict]]) -> None:
        """处理新闻并逐条发送"""
        try:
            # 合并所有新闻
            all_news = []
            for items in news_items.values():
                all_news.extend(items)
            
            self.logger.info(f"Total news to process: {len(all_news)}")
            
            # 过滤和排序新闻
            news_to_send = self.news_cache.filter_and_sort_news(all_news)
            self.logger.info(f"Filtered news to send: {len(news_to_send)}")
            
            # 逐条处理和发送
            for news in news_to_send:
                try:
                    # 生成AI分析
                    analysis = await self._retry_operation(
                        self.ai_processor.analyze_news,
                        news,
                        operation_name="AI分析"
                    )
                    
                    if not analysis:
                        self.logger.error(f"无法获取AI分析: {news['title']}")
                        continue
                    
                    # 格式化消息
                    message = self._format_message(news, analysis)
                    
                    # 发送消息
                    if await self.wechat.send_message(message):
                        self.logger.info(f"准备添加新闻到缓存: {news['title']}")
                        # 只有成功推送的才加入缓存
                        self.news_cache.add_news(news)
                        self.logger.info(f"推送成功并已加入缓存: {news['title']}")
                    else:
                        self.logger.error(f"推送失败: {news['title']}")
                    
                except Exception as e:
                    self.logger.error(f"处理新闻出错: {str(e)}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"批量处理新闻出错: {str(e)}")
    
    async def _retry_operation(self, operation, *args, operation_name="操作"):
        """重试机制"""
        for attempt in range(self.max_retries):
            try:
                if asyncio.iscoroutinefunction(operation):
                    result = await operation(*args)
                else:
                    result = operation(*args)
                return result
            
            except Exception as e:
                self.logger.warning(
                    f"{operation_name}失败 (尝试 {attempt + 1}/{self.max_retries}): {str(e)}"
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                continue
        return None
    
    def _format_message(self, news: Dict, analysis: str) -> str:
        """格式化消息内容"""
        return (
            f"## 📰 {news['title']}\n\n"
            f"**来源**: {news['source']}\n"
            f"**评分**: {news['article_score']:.2f}\n"
            f"**标签**: {', '.join(news.get('tags', []))}\n\n"
            f"### 🔍 AI分析:\n{analysis}\n\n"
            f"[阅读原文]({news['link']})"
        ) 

# 将测试模式设置为False
notifier = NotificationProcessor(test_mode=False) 