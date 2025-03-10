import feedparser
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from src.config import Config
import dateutil.parser as parser
import time

class NewsScraper:
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.trust_env = False  # 禁用代理设置

    def _generate_unique_id(self, url: str, title: str) -> str:
        """生成新闻条目的唯一ID"""
        content = f"{url}{title}".encode('utf-8')
        return hashlib.md5(content).hexdigest()

    def _extract_full_content(self, url: str) -> Optional[str]:
        """提取新闻页面的完整正文内容"""
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 移除不需要的元素
                for tag in soup.find_all(['script', 'style', 'nav', 'header', 'footer']):
                    tag.decompose()
                
                # 尝试找到主要内容区域
                content = None
                for selector in ['article', '.article-content', '.post-content', '.entry-content']:
                    content = soup.select_one(selector)
                    if content:
                        break
                
                if content:
                    return content.get_text(strip=True)
                return None
        except Exception as e:
            self.logger.warning(f"提取完整内容失败 {url}: {str(e)}")
            return None

    def _normalize_date(self, date_str: str) -> str:
        """统一日期格式为ISO格式"""
        try:
            if not date_str:
                return datetime.now().isoformat()
            
            # 处理中文时区标记
            date_str = date_str.replace(' +0800', '+0800')
            
            # 使用 dateutil.parser 替代 feedparser._parse_date
            parsed_date = parser.parse(date_str)
            return parsed_date.isoformat()
        
        except Exception as e:
            self.logger.warning(f"日期解析失败 {date_str}: {str(e)}")
            return datetime.now().isoformat()

    def fetch_rss_feed(self, source: Dict[str, str]) -> List[Dict]:
        """获取单个RSS源的新闻数据"""
        max_retries = 3
        retry_delay = 2  # 秒
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"开始获取 {source['name']} 的新闻 (尝试 {attempt + 1}/{max_retries})")
                
                # 使用requests获取RSS内容
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/rss+xml, application/xml'
                }
                
                try:
                    response = self.session.get(
                        source['url'],
                        headers=headers,
                        timeout=30
                    )
                    
                    if response.status_code != 200:
                        self.logger.error(f"RSS源HTTP错误 {source['name']}: {response.status_code}")
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            continue
                        return []
                    
                    # 添加调试信息
                    self.logger.debug(f"RSS源响应内容前500字符: {response.content[:500]}")
                    
                    # 使用feedparser解析内容
                    feed = feedparser.parse(response.content)
                    
                    # 添加调试信息
                    if hasattr(feed, 'feed'):
                        self.logger.debug(f"Feed标题: {feed.feed.get('title', 'No title')}")
                        self.logger.debug(f"条目数量: {len(feed.entries)}")
                    
                except requests.exceptions.RequestException as e:
                    self.logger.error(f"请求RSS源失败 {source['name']}: {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    return []
                
                # 检查feed是否有效
                if not hasattr(feed, 'entries') or not feed.entries:
                    self.logger.warning(f"RSS源没有新闻条目 {source['name']}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    return []

                news_items = []
                for entry in feed.entries:
                    try:
                        # 基本信息提取
                        item = {
                            'title': entry.get('title', '').strip(),
                            'link': entry.get('link', ''),
                            'summary': entry.get('summary', '').strip(),
                            'published': self._normalize_date(entry.get('published', '')),
                            'source': source['name'],
                            'source_type': source.get('type', 'rss'),
                            'language': source.get('language', 'zh'),
                            'created_at': datetime.now().isoformat(),
                            'unique_id': self._generate_unique_id(
                                entry.get('link', ''), 
                                entry.get('title', '')
                            ),
                            'processed': False
                        }

                        # 提取完整正文（如果配置允许）
                        if source.get('fetch_full_content', False):
                            full_content = self._extract_full_content(item['link'])
                            if full_content:
                                item['full_content'] = full_content

                        # 初步内容清理
                        for key in ['title', 'summary']:
                            if item[key]:
                                item[key] = ' '.join(item[key].split())

                        news_items.append(item)
                    except Exception as e:
                        self.logger.error(f"处理新闻条目时出错 {source['name']}: {str(e)}")
                        continue

                self.logger.info(f"成功获取 {len(news_items)} 条新闻 来自 {source['name']}")
                return news_items
                
            except Exception as e:
                self.logger.error(f"获取RSS源失败 {source['name']} (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return []

    def fetch_all_news(self) -> List[Dict]:
        """获取所有配置的RSS源的新闻数据"""
        all_news = []
        
        # 获取国际新闻
        for source in self.config.RSS_SOURCES['international']:
            news_items = self.fetch_rss_feed(source)
            all_news.extend(news_items)
            
        # 获取国内新闻
        for source in self.config.RSS_SOURCES['domestic']:
            news_items = self.fetch_rss_feed(source)
            all_news.extend(news_items)
            
        return all_news

    def _is_similar(self, text1: str, text2: str, threshold: float = 0.8) -> bool:
        """检查两段文本是否相似"""
        # 使用简单的词集合相似度
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        intersection = words1 & words2
        union = words1 | words2
        return len(intersection) / len(union) > threshold

    def _calculate_article_score(self, item: Dict) -> float:
        """计算文章的价值分数"""
        score = 0.0
        text = f"{item['title']} {item['summary']}".lower()
        is_english = item.get('language', 'unknown') == 'en'
        
        # 1. 优先来源基础分 (0-60分)
        priority_sources = {
            'IT桔子': 50,
            'Crunchbase News': 50,
            '微软研究院AI头条': 50,
            'Seeking Alpha': 50,
            '东方财富硬科技': 45,    # 新增，给予较高权重
            'techcrunch': 25,
            'mit technology review': 30,
            'ars technica': 12,
            'zdnet': 20,
            'engadget': 20,
            'cnet': 10,
            'the register': 10,
            '36氪': 30,
            '量子位': 40,
            '少数派': 30,
            '奇客solidot': 30
        }
        
        # 优先来源直接加上基础分
        source_name = item['source'].lower()
        base_score = next((s for n, s in priority_sources.items() if n.lower() in source_name), 5)
        score += base_score
        
        # 2. 科技相关性评分 (0-40分)
        tech_keywords = {
            'core': [
                # 中文关键词
                'ai', '人工智能', '机器学习', '深度学习', 
                '量子计算', '芯片', '半导体', '云计算',
                '区块链', '自动驾驶', '机器人', '5g', '6g',
                # 英文关键词
                'artificial intelligence', 'machine learning', 'deep learning',
                'quantum computing', 'semiconductor', 'cloud computing',
                'blockchain', 'autonomous driving', 'robotics',
                'neural network', 'transformer', 'large language model'
            ],
            'application': [
                # 中文关键词
                'saas', '算法', 'api', '开源', 'github',
                '数据库', '微服务', '架构', '编程语言',
                # 英文关键词
                'algorithm', 'open source', 'database', 'microservice',
                'architecture', 'programming', 'software', 'development',
                'technology', 'innovation', 'startup'
            ],
            'industry': [
                # 中文关键词
                '创新', '研发', '专利', '实验室', '技术',
                '工程师', '科技公司', '初创', '独角兽',
                # 英文关键词
                'innovation', 'research', 'patent', 'laboratory',
                'engineer', 'tech company', 'startup', 'unicorn'
            ]
        }
        
        tech_score = 0
        weights = [3, 2, 1]
        for i, category in enumerate(tech_keywords.keys()):
            # 英文文章给予更宽松的评分
            base_weight = weights[i] * (1.5 if is_english else 1.0)
            matches = sum(1 for k in tech_keywords[category] if k in text)
            tech_score += matches * base_weight
        
        score += min(40, tech_score * 2)
        
        # 3. 时效性评分 (0-20分)
        try:
            published_time = datetime.fromisoformat(item['published'].replace('Z', '+00:00'))
            hours_old = (datetime.now(published_time.tzinfo) - published_time).total_seconds() / 3600
            
            # 优先来源的时效性要求更宽松
            is_priority = base_score >= 60
            if is_priority:
                if hours_old <= 48:  # 优先来源48小时内
                    score += 20
                elif hours_old <= 72:  # 72小时内
                    score += 15
                elif hours_old <= 96:  # 96小时内
                    score += 10
            else:
                if hours_old <= 24:  # 普通来源24小时内
                    score += 20
                elif hours_old <= 48:  # 48小时内
                    score += 15
                elif hours_old <= 72:  # 72小时内
                    score += 10
        except Exception:
            score += 5  # 默认给5分
        
        # 4. 内容质量评分 (0-20分)
        content_score = 0
        # 优先来源的内容长度要求更宽松
        is_priority = base_score >= 60
        min_length = 80 if (is_english or is_priority) else 150
        
        if len(text) > min_length:
            content_score += 10
        if item.get('summary', ''):
            content_score += 5
        if len(item.get('title', '')) > (10 if (is_english or is_priority) else 15):
            content_score += 5
        score += content_score
        
        # 优先来源的最低分更低，确保基本都能通过
        min_score = 30 if (is_priority or is_english) else 50
        
        return max(min_score, round(score, 2))

    def filter_by_keywords(self, news_items: List[Dict], min_score: float = 50.0) -> Dict[str, List[Dict]]:
        """根据关键词过滤新闻并添加标签"""
        filtered_news = {
            'zh': [],
            'en': []
        }
        seen_content = set()
        
        for item in news_items:
            # 根据语言设置不同的最低分数要求
            lang = item.get('language', 'unknown')
            min_required_score = 40 if lang == 'en' else 50
            
            text = f"{item['title']} {item['summary']}".lower()
            
            # 先检查是否应该过滤掉
            if self._should_filter_out(text):
                continue
            
            # 计算文章分数
            item['article_score'] = self._calculate_article_score(item)
            
            # 只保留高分文章
            if item['article_score'] < min_required_score:
                continue
            
            # 检查是否与已有内容相似
            if any(self._is_similar(text, seen) for seen in seen_content):
                continue
            
            seen_content.add(text)
            
            # 标签和权重计算
            tag_weights = {}
            for category, keywords in self.config.KEYWORDS.items():
                weight = 0
                for keyword in keywords:
                    if keyword.lower() in text:
                        if keyword.lower() in item['title'].lower():
                            weight += 2
                        else:
                            weight += 1
                if weight > 0:
                    tag_weights[category] = weight
            
            # 选择权重最高的标签
            if tag_weights:
                # 将权重字典转换为列表并排序
                sorted_tags = sorted(
                    [(k, v) for k, v in tag_weights.items()],
                    key=lambda x: x[1],
                    reverse=True
                )
                
                # 只取前三个标签的名称
                item['tags'] = [tag for tag, _ in sorted_tags[:3]]
                item['tag_weights'] = tag_weights
            
            # 根据语言分类
            if lang in ['zh', 'en']:
                filtered_news[lang].append(item)
        
        # 对每种语言的新闻按分数排序
        for lang in filtered_news:
            filtered_news[lang] = sorted(
                filtered_news[lang], 
                key=lambda x: x['article_score'], 
                reverse=True
            )[:15]  # 只保留前10篇
        
        return filtered_news

    def _should_filter_out(self, text: str) -> bool:
        """检查是否应该过滤掉这篇文章"""
        # 广告/营销相关
        ad_keywords = {'优惠', '促销', '限时', '折扣', '特价'}
        # 八卦/娱乐相关
        gossip_keywords = {'绯闻', '八卦', '明星', '网红'}
        
        text = text.lower()
        return (
            any(k in text for k in ad_keywords) or
            any(k in text for k in gossip_keywords)
        ) 