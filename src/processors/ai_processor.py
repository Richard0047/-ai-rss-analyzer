from typing import List, Dict
import logging
import requests
from datetime import datetime
from ..config import Config
import asyncio
import aiohttp

class AIProcessor:
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        self.dify_headers = {
            "Authorization": f"Bearer {self.config.DIFY['api_key']}",
            "Content-Type": "application/json"
        }
        self.timeout = aiohttp.ClientTimeout(total=30)  # 30秒超时

    def call_dify_api(self, prompt: str) -> str:
        """调用Dify API进行处理"""
        try:
            url = f"{self.config.DIFY['api_endpoint']}/chat-messages"
            payload = {
                "inputs": {},
                "query": prompt,
                "response_mode": "blocking",
                "conversation_id": None,
                "user": "news_processor"
            }
            
            response = requests.post(
                url, 
                headers=self.dify_headers,
                json=payload,
                timeout=30  # 添加超时设置
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('answer', '')
            else:
                self.logger.error(f"Dify API调用失败: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            self.logger.error("Dify API请求超时")
            return None
        except Exception as e:
            self.logger.error(f"调用Dify API时出错: {str(e)}")
            return None

    def call_siliconflow_api(self, prompt: str) -> str:
        """调用硅基流动 API进行处理"""
        try:
            headers = {
                "Authorization": f"Bearer {self.config.SILICONFLOW['api_key']}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.config.SILICONFLOW['model'],
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 1024,
                "stream": False
            }
            
            # 禁用代理设置
            session = requests.Session()
            session.trust_env = False  # 不使用环境变量中的代理设置
            
            # 增加超时时间到60秒
            response = session.post(
                self.config.SILICONFLOW['api_endpoint'],
                headers=headers,
                json=payload,
                timeout=60,
                verify=True
            )
            
            self.logger.info(f"API响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.logger.info("成功获取API响应")
                return data['choices'][0]['message']['content']
            else:
                self.logger.error(f"API响应详情: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            self.logger.error("API请求超时 (60秒)")
            return None
        except requests.exceptions.SSLError as e:
            self.logger.error(f"SSL验证错误: {str(e)}")
            return None
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"连接错误: {str(e)}")
            self.logger.info("尝试检查: 1. 网络连接 2. 防火墙设置 3. 代理设置")
            return None
        except Exception as e:
            self.logger.error(f"调用API时出错: {str(e)}")
            return None

    def prepare_prompt(self, item: Dict) -> str:
        """准备发送给AI的提示"""
        return f"""作为一个专业的科技新闻分析师，请对以下新闻进行分析并以Markdown格式输出：

新闻内容：
标题：{item['title']}
来源：{item['source']}
正文：{item['summary']}

请按以下结构进行分析：

## 核心要点
用3-5个简短的句子总结新闻最重要的信息。每句话以"•"开头，确保突出新闻的关键信息。

## 详细分析

### 相关方
- 主要公司/机构：列出新闻中提到的主要公司、机构及其角色
- 合作方/竞争方：相关的合作伙伴或竞争对手（如有）

### 关键数据
- 技术指标：具体的技术参数、性能数据等
- 商业数据：市场份额、投资金额、营收等数据（如有）
- 时间节点：重要的时间信息

### 创新亮点
- 技术创新：新技术、新特性、技术突破等
- 商业创新：新商业模式、新应用场景等（如有）

## 影响分析

### 短期影响（0-6个月）
分析此事件在半年内可能产生的直接影响

### 中长期影响（6个月以上）
分析此事件可能带来的深远影响

### 行业启示
总结这个新闻对行业从业者的启示和建议

请用专业、客观的语言进行分析，确保内容准确、逻辑清晰。如果某些信息新闻中未提供，可以基于专业判断进行合理推测，但需要标注"(推测)"。"""

    def process_item(self, item: Dict) -> Dict:
        """处理单条新闻"""
        try:
            enhanced_item = item.copy()
            
            # 只处理未处理过的新闻
            if not enhanced_item.get('ai_processed'):
                prompt = self.prepare_prompt(item)
                # 使用硅基流动API替代Dify
                ai_response = self.call_siliconflow_api(prompt)
                
                if ai_response:
                    enhanced_item['ai_summary'] = ai_response
                    enhanced_item['ai_processed'] = True
                    enhanced_item['ai_processed_at'] = datetime.now().isoformat()
                
            return enhanced_item
            
        except Exception as e:
            self.logger.error(f"AI处理新闻时出错: {str(e)}")
            return item

    def process_batch(self, items: List[Dict]) -> List[Dict]:
        """批量处理新闻"""
        enhanced_items = []
        for item in items:
            # 只处理带有特定标签的新闻
            if 'tags' in item and any(tag in ['ai_ml', 'tech_innovation', 'investment'] 
                                    for tag in item['tags']):
                enhanced_item = self.process_item(item)
                enhanced_items.append(enhanced_item)
            else:
                enhanced_items.append(item)
        return enhanced_items

    async def analyze_news(self, news: Dict) -> str:
        """分析单条新闻"""
        try:
            # 先尝试硅基流动API
            analysis = await self._get_ai_analysis_siliconflow(news)
            if analysis:
                return analysis
            
            # 如果失败，尝试Dify API
            analysis = await self._get_ai_analysis_dify(news)
            if analysis:
                return analysis
            
            # 如果都失败，返回简单摘要
            return f"新闻摘要: {news.get('summary', '无摘要')}"
            
        except Exception as e:
            self.logger.error(f"AI分析失败: {str(e)}")
            return news.get('summary', '无摘要')  # 失败时返回原始摘要
    
    def _generate_prompt(self, news: Dict) -> str:
        """生成AI分析提示词"""
        return (
            f"请简要分析以下科技新闻的要点和影响（200字以内）：\n\n"
            f"标题：{news['title']}\n"
            f"摘要：{news.get('summary', '无摘要')}\n"
            f"标签：{', '.join(news.get('tags', []))}\n"
        )
    
    async def _get_ai_analysis_siliconflow(self, news: Dict) -> str:
        """调用硅基流动API获取分析结果"""
        try:
            prompt = self._generate_prompt(news)
            
            # 使用硅基流动API
            analysis = self.call_siliconflow_api(prompt)
            if analysis:
                return analysis
            
            return "AI分析服务暂时不可用"
            
        except Exception as e:
            self.logger.error(f"获取AI分析失败: {str(e)}")
            return "AI分析出错，请稍后重试"
    
    async def _get_ai_analysis_dify(self, news: Dict) -> str:
        """调用Dify API获取分析结果"""
        try:
            prompt = self._generate_prompt(news)
            prompt = prompt.encode('utf-8').decode('utf-8')  # 确保UTF-8编码
            
            # 使用Dify API
            analysis = self.call_dify_api(prompt)
            if analysis:
                return analysis
            
            return "AI分析服务暂时不可用"
            
        except Exception as e:
            self.logger.error(f"获取AI分析失败: {str(e)}")
            return "AI分析出错，请稍后重试"
    
    async def _get_ai_analysis_deepseek(self, prompt: str) -> str:
        """调用DeepSeek AI服务获取分析结果"""
        # TODO: 实现DeepSeek AI调用逻辑
        pass 