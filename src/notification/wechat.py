from typing import List, Dict
import logging
import json
import requests
from datetime import datetime
from ..config import Config

class WeChatNotifier:
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        self.access_token = None
        self.token_expires = 0

    def _get_access_token(self) -> str:
        """获取或刷新访问令牌"""
        now = datetime.now().timestamp()
        
        # 如果令牌未过期，直接返回
        if self.access_token and now < self.token_expires:
            return self.access_token
            
        try:
            url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
            params = {
                "corpid": self.config.WECHAT['corp_id'],
                "corpsecret": self.config.WECHAT['corp_secret']
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if data["errcode"] == 0:
                self.access_token = data["access_token"]
                self.token_expires = now + data["expires_in"] - 300  # 提前5分钟刷新
                return self.access_token
            else:
                self.logger.error(f"获取访问令牌失败: {data}")
                return None
                
        except Exception as e:
            self.logger.error(f"获取访问令牌时出错: {str(e)}")
            return None

    def format_news_message(self, news_items: List[Dict]) -> str:
        """将新闻格式化为Markdown消息"""
        if not news_items:
            return "暂无新闻更新"
            
        message = "# 最新科技新闻动态\n\n"
        
        # 按标签分组新闻
        categorized_news = {}
        for item in news_items:
            for tag in item.get('tags', ['其他']):
                if tag not in categorized_news:
                    categorized_news[tag] = []
                categorized_news[tag].append(item)
        
        # 按分类生成消息
        for category, items in categorized_news.items():
            message += f"## {category.upper()}\n\n"
            for item in items[:5]:  # 每个分类最多显示5条
                message += f"- [{item['title']}]({item['link']})\n"
                if 'ai_summary' in item:
                    message += f"  > {item['ai_summary']}\n"
                message += "\n"
        
        return message

    def send_message(self, message: str) -> bool:
        """发送消息到企业微信"""
        token = self._get_access_token()
        if not token:
            return False
            
        try:
            url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}"
            data = {
                "touser": "@all",
                "msgtype": "markdown",
                "agentid": self.config.WECHAT['agent_id'],
                "markdown": {
                    "content": message
                }
            }
            
            response = requests.post(url, json=data)
            result = response.json()
            
            if result["errcode"] == 0:
                self.logger.info("消息发送成功")
                return True
            else:
                self.logger.error(f"消息发送失败: {result}")
                return False
                
        except Exception as e:
            self.logger.error(f"发送消息时出错: {str(e)}")
            return False

    def send_batch(self, news_items: List[Dict]) -> bool:
        """批量发送新闻"""
        message = self.format_news_message(news_items)
        return self.send_message(message) 