import logging
import aiohttp
import json
from src.config import Config

class WeChatNotifier:
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        self.webhook_url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={self.config.WECHAT['webhook_key']}"
        
    async def send_message(self, content: str) -> bool:
        """通过群机器人发送消息"""
        try:
            data = {
                "msgtype": "markdown",  # 使用markdown格式以获得更好的显示效果
                "markdown": {
                    "content": content
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("errcode") == 0:
                            return True
                        else:
                            self.logger.error(f"发送消息失败: {result}")
                    else:
                        self.logger.error(f"请求失败: {response.status}")
                        
            return False
            
        except Exception as e:
            self.logger.error(f"发送消息时出错: {str(e)}")
            return False

    async def send_markdown(self, content: str) -> bool:
        """发送markdown格式消息"""
        try:
            access_token = await self.get_access_token()
            if not access_token:
                return False
                
            url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
            
            data = {
                "touser": "@all",
                "msgtype": "markdown",
                "agentid": self.config.WECHAT['agent_id'],
                "markdown": {
                    "content": content
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("errcode") == 0:
                            return True
                        else:
                            self.logger.error(f"发送markdown消息失败: {result}")
                    else:
                        self.logger.error(f"请求失败: {response.status}")
                        
            return False
            
        except Exception as e:
            self.logger.error(f"发送markdown消息时出错: {str(e)}")
            return False 