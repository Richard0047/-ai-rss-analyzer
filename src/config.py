import os
from dotenv import load_dotenv
from typing import List

# 加载环境变量
load_dotenv()

class Config:
    # RSS源配置
    RSS_SOURCES = {
        'international': [
            {
                'name': 'Crunchbase News',
                'url': 'https://news.crunchbase.com/feed/',
                'language': 'en',
                'type': 'rss'
            },
            {
                'name': 'Seeking Alpha',
                'url': 'https://seekingalpha.com/feed.xml',
                'language': 'en',
                'type': 'rss'
            },
            {
                'name': 'Ars Technica',
                'url': 'https://feeds.arstechnica.com/arstechnica/index',
                'language': 'en',
                'type': 'rss'
            },
            {
                'name': 'MIT Technology Review',
                'url': 'https://www.technologyreview.com/feed/',
                'language': 'en',
                'type': 'rss'
            },
            {
                'name': 'The Register',
                'url': 'https://www.theregister.com/headlines.atom',
                'language': 'en',
                'type': 'rss'
            },
            {
                'name': 'ZDNet',
                'url': 'https://www.zdnet.com/news/rss.xml',
                'language': 'en',
                'type': 'rss'
            },
            {
                'name': 'CNET',
                'url': 'https://www.cnet.com/rss/news/',
                'language': 'en',
                'type': 'rss'
            },
            {
                'name': 'Josh Comeau',
                'url': 'https://www.joshwcomeau.com/rss.xml',
                'language': 'en',
                'type': 'rss'
            }
        ],
        'domestic': [
            {
                'name': '东方财富硬科技',
                'url': 'https://rsshub.app/eastmoney/search/硬科技',
                'language': 'zh',
                'type': 'rss'
            },
            {
                'name': '美团技术团队',
                'url': 'https://tech.meituan.com/feed/',
                'language': 'zh',
                'type': 'rss'
            },
            {
                'name': 'IT桔子',
                'url': 'https://www.itjuzi.com/api/telegraph.xml',
                'language': 'zh',
                'type': 'rss'
            },
            {
                'name': '微软研究院AI头条',
                'url': 'https://plink.anyfeeder.com/weixin/MSRAsia',
                'language': 'zh',
                'type': 'rss'
            },
            {
                'name': '36氪',
                'url': 'https://www.36kr.com/feed',
                'language': 'zh',
                'type': 'rss'
            },
            {
                'name': '少数派',
                'url': 'https://sspai.com/feed',
                'language': 'zh',
                'type': 'rss'
            },
            {
                'name': '奇客Solidot',
                'url': 'https://www.solidot.org/index.rss',
                'language': 'zh',
                'type': 'rss'
            },
            {
                'name': '机器之心',
                'url': 'https://www.jiqizhixin.com/rss',
                'language': 'zh',
                'type': 'rss'
            },
            {
                'name': '量子位',
                'url': 'https://www.qbitai.com/feed',
                'language': 'zh',
                'type': 'rss'
            },
            {
                'name': 'InfoQ',
                'url': 'https://www.infoq.cn/feed',
                'language': 'zh',
                'type': 'rss'
            }
        ]
    }

    # MongoDB配置
    DATABASE = {
        'uri': os.getenv('MONGODB_URI', 'mongodb://localhost:27017/news_aggregator'),
        'name': 'news_aggregator',
        'collection': 'news'
    }

    # 关键词过滤
    KEYWORDS = {
        'ai_ml': [
            # 基础AI
            'AI', '人工智能', '机器学习', 'Machine Learning',
            '深度学习', '神经网络', '强化学习',
            
            # 大语言模型
            'GPT', 'LLM', '大模型', 'DeepSeek', 'Claude',
            'Gemini', 'Transformer', 'AIGC', '生成式AI',
            '文心一言', '通义千问', '书生·浦语',
            
            # AI应用领域
            '计算机视觉', 'CV', 'NLP', '自然语言处理',
            '语音识别', '图像生成', '多模态', '向量数据库',
            'RAG', '知识库', 'AI Agent', '智能助手'
        ],
        
        'investment': [
            # 融资阶段
            '融资', '投资', 'IPO', '上市', '天使轮',
            'A轮', 'B轮', 'C轮', '融资轮', 'Pre-IPO',
            
            # 投资机构
            '风投', 'VC', 'PE', '创投', '基金',
            '红杉', '高瓴', 'IDG', '投资人',
            
            # 投资领域
            '并购', '股权', '估值', '退出', '清算',
            '众筹', '融资金额', '投后估值'
        ],
        
        'tech_innovation': [
            # 硬件技术
            '硬科技', '芯片', '量子计算', '半导体',
            '光刻机', 'GPU', 'TPU', 'ASIC',
            
            # 新兴技术
            '区块链', '元宇宙', '自动驾驶', '机器人',
            'IoT', '物联网', '5G', '6G', '边缘计算',
            
            # 企业技术
            '云计算', '新能源', 'AR', 'VR', 'XR',
            '智能制造', '数字孪生', '工业互联网'
        ],
        
        'business': [
            # 商业模式
            '创业', '商业模式', '营收', '利润',
            '市场份额', '用户增长', '商业化', '变现',
            
            # 企业发展
            '盈利', '战略', '商业计划', '商业分析',
            '商业洞察', '商业趋势', '独角兽',
            
            # 市场动态
            '市场规模', '行业报告', '竞争格局',
            '商业生态', '供应链', '渠道',
            
            # 新增关键词
            '投资', '股市', '市场', '经济',
            '产品', '营销', '管理', '创新',
            '数字化转型', '企业服务', 'B2B', 'B2C', 'DTC',
            # 新增投资相关关键词
            '科技投资', '产业基金', '风险投资', 'VC/PE',
            '融资', '上市', 'IPO', '并购', 'M&A',
            '产业升级', '技术创新', '研发投入'
        ],
        
        'development': [
            # 开发技术
            '开源', 'GitHub', '编程语言', 'Python',
            'Java', 'Golang', 'Rust', '微服务',
            
            # 架构设计
            '架构', '云原生', 'DevOps', 'CI/CD',
            '容器化', 'Docker', 'K8s', '数据库',
            
            # 系统特性
            '分布式', '高并发', '高可用', '中台',
            '服务网格', '微内核', '插件化'
        ],
        
        'tech': [
            # 现有关键词
            'AI', '人工智能', '机器学习', 'ChatGPT', 'LLM', '大模型',
            '深度学习', '神经网络', '算法', '编程', '开发', '技术',
            '云计算', '区块链', '元宇宙', '虚拟现实', 'VR', 'AR',
            '自动驾驶', '机器人', '量子计算', '芯片', '半导体',
            # 新增硬科技相关关键词
            '硬科技', '新材料', '光刻机', '光伏', '新能源',
            '生物科技', '航空航天', '高端制造', '智能制造',
            '碳中和', '储能', '新一代通信', '6G研发'
        ]
    }

    # Webhook配置
    WEBHOOK = {
        'dingtalk': 'your_dingtalk_webhook_url',
        'wechat': 'your_wechat_webhook_url'
    }

    # API配置
    API = {
        'host': '0.0.0.0',
        'port': 8000,
        'debug': True
    }

    # DeepSeek配置
    DEEPSEEK = {
        'api_key': os.getenv('DEEPSEEK_API_KEY'),
        'model': 'deepseek-chat'
    }

    # Dify配置
    DIFY = {
        'api_endpoint': 'https://api.dify.ai/v1',
        'api_key': os.getenv('DIFY_API_KEY'),
        'application_id': os.getenv('DIFY_APP_ID')
    }

    # 企业微信配置
    WECHAT = {
        'corp_id': os.getenv('WECHAT_CORP_ID'),
        'corp_secret': os.getenv('WECHAT_CORP_SECRET'),
        'agent_id': os.getenv('WECHAT_AGENT_ID'),
        'webhook_key': os.getenv('WECHAT_WEBHOOK_KEY')
    }

    # 钉钉配置
    DINGTALK = {
        'access_token': os.getenv('DINGTALK_ACCESS_TOKEN'),
        'secret': os.getenv('DINGTALK_SECRET')
    }

    # 定时任务配置
    SCHEDULE = {
        'news_fetch': '*/30 * * * *',    # 每30分钟抓取一次
        'ai_process': '*/30 * * * *',    # 每30分钟处理一次
        'notification': '0 */2 * * *'     # 每2小时推送一次（0,2,4...22点）
    }

    # 硅基流动配置
    SILICONFLOW = {
        'api_endpoint': 'https://api.siliconflow.cn/v1/chat/completions',
        'api_key': os.getenv('SILICONFLOW_API_KEY'),
        'model': 'Pro/deepseek-ai/DeepSeek-R1'
    } 