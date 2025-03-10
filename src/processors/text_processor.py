import re
from typing import List, Dict, Optional
import html
import logging
from datetime import datetime
from dateutil import parser
from langdetect import detect
from bs4 import BeautifulSoup
import hashlib

class TextProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 常见的HTML实体和特殊字符映射
        self.html_char_map = {
            '&nbsp;': ' ', '&quot;': '"', '&amp;': '&',
            '&lt;': '<', '&gt;': '>', '&apos;': "'",
            '\xa0': ' ', '\u3000': ' '
        }

    def clean_html(self, text: str) -> str:
        """清理HTML标签和特殊字符"""
        if not text:
            return ""
            
        try:
            # 检查是否是HTML内容
            if '<' in text and '>' in text:
                soup = BeautifulSoup(text, 'html.parser')
                clean_text = soup.get_text()
            else:
                clean_text = text
            
            # 替换HTML实体和特殊字符
            for char, replacement in self.html_char_map.items():
                clean_text = clean_text.replace(char, replacement)
                
            # 解码剩余的HTML实体
            clean_text = html.unescape(clean_text)
            
            # 规范化空白字符
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            
            return clean_text
            
        except Exception as e:
            self.logger.warning(f"HTML清理失败: {str(e)}")
            return text.strip()

    def detect_language(self, text: str) -> str:
        """改进的语言检测"""
        try:
            # 使用更多的文本样本
            text_sample = text[:1000]  # 使用前1000个字符
            # 多次检测取众数
            detections = []
            for i in range(3):
                try:
                    detections.append(detect(text_sample))
                except:
                    continue
            
            if not detections:
                return 'unknown'
            
            # 返回出现最多的语言
            from collections import Counter
            return Counter(detections).most_common(1)[0][0]
        except:
            return 'unknown'

    def extract_keywords(self, text: str, max_keywords: int = 5) -> List[str]:
        """提取文本关键词（基于预定义的关键词列表）"""
        try:
            # 将文本转换为小写以进行不区分大小写的匹配
            text = text.lower()
            matched_keywords = []
            
            # 遍历所有预定义的关键词类别
            for category, keywords in self.config.KEYWORDS.items():
                # 对每个关键词进行匹配
                for keyword in keywords:
                    if keyword.lower() in text:
                        matched_keywords.append(keyword)
            
            # 去重并返回前N个关键词
            unique_keywords = list(dict.fromkeys(matched_keywords))
            return unique_keywords[:max_keywords]
            
        except Exception as e:
            self.logger.error(f"关键词提取失败: {str(e)}")
            return []

    def normalize_date(self, date_str: str) -> str:
        """统一日期格式为ISO格式"""
        try:
            if not date_str:
                return datetime.now().isoformat()
            parsed_date = parser.parse(date_str)
            return parsed_date.isoformat()
        except Exception as e:
            self.logger.warning(f"日期解析失败 {date_str}: {str(e)}")
            return datetime.now().isoformat()

    def generate_summary(self, text: str, max_length: int = 200, min_length: int = 50) -> str:
        """生成文本摘要（增加最小长度限制）"""
        try:
            # 清理文本
            clean_text = self.clean_html(text)
            
            # 按句子分割（支持中英文标点）
            sentences = re.split(r'[.!?。！？;；]+\s*', clean_text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if not sentences:
                return clean_text[:max_length]
            
            # 计算每个句子的重要性分数
            sentence_scores = {}
            for sentence in sentences:
                score = 0
                # 1. 句子长度评分（过长或过短都不适合作为摘要）
                length = len(sentence)
                if 10 < length < 100:
                    score += 1
                
                # 2. 关键词匹配评分
                lower_sentence = sentence.lower()
                for category, keywords in self.config.KEYWORDS.items():
                    for keyword in keywords:
                        if keyword.lower() in lower_sentence:
                            score += 2  # 包含关键词的句子更重要
                
                # 3. 位置评分（通常第一句话更重要）
                if sentence == sentences[0]:
                    score += 2
                elif sentences.index(sentence) < 3:
                    score += 1
                
                # 4. 特征词评分
                feature_words = {
                    '总之', '总而言之', '综上所述',  # 中文总结性词语
                    'in conclusion', 'therefore', 'as a result',  # 英文总结性词语
                    '最重要的是', '值得注意的是',  # 中文重要性标记
                    'importantly', 'significantly',  # 英文重要性标记
                    '首先', '其次', '最后',  # 中文顺序词
                    'first', 'second', 'finally'  # 英文顺序词
                }
                for word in feature_words:
                    if word in lower_sentence:
                        score += 1
                
                sentence_scores[sentence] = score
            
            # 按分数排序句子
            ranked_sentences = sorted(
                sentence_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            # 生成摘要
            summary = []
            current_length = 0
            
            # 确保至少包含一个句子
            first_sentence = ranked_sentences[0][0]
            summary.append(first_sentence)
            current_length = len(first_sentence)
            
            # 添加其他重要句子，直到达到长度限制
            for sentence, _ in ranked_sentences[1:]:
                if current_length + len(sentence) + 1 > max_length:
                    break
                summary.append(sentence)
                current_length += len(sentence) + 1
            
            # 如果摘要太短，尝试添加更多句子
            while current_length < min_length and len(ranked_sentences) > len(summary):
                next_sentence = ranked_sentences[len(summary)][0]
                if current_length + len(next_sentence) > max_length:
                    break
                summary.append(next_sentence)
                current_length += len(next_sentence)
            
            # 按原文顺序重新排序
            original_order = []
            for s in sentences:
                if s in summary:
                    original_order.append(s)
            
            # 添加省略号表示被截断
            result = '。'.join(original_order)
            if len(result) < len(clean_text):
                result += '...'
            
            return result
            
        except Exception as e:
            self.logger.error(f"生成摘要失败: {str(e)}")
            return text[:max_length]

    def process_item(self, item: Dict) -> Dict:
        """处理单条新闻数据"""
        try:
            processed_item = item.copy()
            
            # 清理文本内容
            processed_item['title'] = self.clean_html(item['title'])
            processed_item['summary'] = self.clean_html(item['summary'])
            
            # 如果有完整正文，也进行清理
            if 'full_content' in item:
                processed_item['full_content'] = self.clean_html(item['full_content'])
                # 如果没有摘要，从全文生成摘要
                if not processed_item['summary']:
                    processed_item['summary'] = self.generate_summary(processed_item['full_content'])
            
            # 检测语言
            if 'language' not in processed_item:
                text_for_detection = f"{processed_item['title']} {processed_item['summary']}"
                processed_item['language'] = self.detect_language(text_for_detection)
            
            # 规范化日期
            if 'published' in processed_item:
                processed_item['published'] = self.normalize_date(processed_item['published'])
            
            # 添加处理标记
            processed_item['text_processed'] = True
            processed_item['text_processed_at'] = datetime.now().isoformat()
            
            return processed_item
            
        except Exception as e:
            self.logger.error(f"处理新闻数据时出错: {str(e)}")
            return item

    def process_batch(self, items: List[Dict]) -> List[Dict]:
        """批量处理新闻数据"""
        processed_items = []
        for item in items:
            processed_item = self.process_item(item)
            processed_items.append(processed_item)
        return processed_items

    def assess_content_quality(self, text: str) -> float:
        """评估内容质量"""
        score = 0.0
        
        # 1. 文本长度评分
        length = len(text)
        if 500 <= length <= 3000:
            score += 3
        elif 200 <= length < 500:
            score += 2
        
        # 2. 结构完整性
        if '。' in text and '，' in text:
            score += 2
        
        # 3. 专业术语密度
        tech_terms = self._extract_tech_terms(text)
        term_density = len(tech_terms) / length
        score += min(3, term_density * 1000)
        
        # 4. 引用和数据
        if re.search(r'\d+%|\d+亿|\d+万', text):
            score += 2
        
        return score / 10  # 归一化到0-1 