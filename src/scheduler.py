import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.scrapers.news_scraper import NewsScraper
from src.processors.text_processor import TextProcessor
from src.processors.notification_processor import NotificationProcessor

class NewsScheduler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scheduler = AsyncIOScheduler()
        
        # 初始化组件
        self.scraper = NewsScraper()
        self.text_processor = TextProcessor()
        self.notifier = NotificationProcessor(test_mode=False)  # 实际推送模式

    async def fetch_and_process(self):
        """获取、处理并推送新闻"""
        try:
            self.logger.info(f"开始新闻处理任务 - {datetime.now()}")
            
            # 1. 获取新闻
            all_news = []
            for source in self.scraper.config.RSS_SOURCES['domestic'] + self.scraper.config.RSS_SOURCES['international']:
                news_items = self.scraper.fetch_rss_feed(source)
                all_news.extend(news_items)
            
            # 2. 关键词过滤
            filtered_news = self.scraper.filter_by_keywords(all_news)
            
            # 3. 文本处理
            processed_news = self.text_processor.process_batch(all_news)
            
            # 4. 推送新闻
            await self.notifier.process_and_send(filtered_news)
            
            self.logger.info("新闻处理任务完成")
            
        except Exception as e:
            self.logger.error(f"新闻处理任务出错: {str(e)}", exc_info=True)

    def start(self):
        """启动定时任务"""
        # 配置调度器
        self.scheduler = AsyncIOScheduler(
            job_defaults={
                'misfire_grace_time': None,  # 不限制错过的时间
                'coalesce': True,  # 合并错过的任务
                'max_instances': 1  # 同一时间只允许一个实例运行
            }
        )

        # 每15分钟执行一次
        self.scheduler.add_job(
            self.fetch_and_process,
            CronTrigger(minute='*/30'),  # 改为每30分钟
            id='news_job',
            name='新闻处理任务'
        )
        
        # 添加立即执行的任务
        self.scheduler.add_job(
            self.fetch_and_process,
            'date',  # 立即执行一次
            id='initial_job',
            name='初始新闻处理'
        )
        
        self.scheduler.start()
        self.logger.info("定时任务已启动")
        
        try:
            # 保持程序运行
            asyncio.get_event_loop().run_forever()
        except (KeyboardInterrupt, SystemExit):
            self.logger.info("正在停止定时任务...")
            self.scheduler.shutdown()

    def stop(self):
        """停止调度器"""
        self.scheduler.shutdown()
        self.logger.info("调度器已停止")

    def get_status(self):
        """获取调度器状态"""
        return {
            'running': self.scheduler.running,
            'jobs': len(self.scheduler.get_jobs()),
            'next_run': self.scheduler.get_job('news_job').next_run_time
        } 