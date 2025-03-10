# AI RSS News Analyzer

一个基于 AI 的 RSS 新闻聚合和分析系统，支持多语言（中文/英文）新闻源，能够进行情感分析并实时推送分析结果。

## 功能特点

- 支持多语言 RSS 源订阅和聚合
- 基于 AI 的新闻内容分析和情感识别
- 支持多种推送渠道（企业微信、钉钉等）
- 自定义关键词过滤和分类
- 定时任务调度
- MongoDB 数据持久化

## 技术栈

- Python 3.11+
- MongoDB
- FastAPI
- APScheduler
- 多个 AI 模型支持 (DeepSeek, Dify 等)

## 安装

1. 克隆仓库

## 使用

1. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

2. 配置环境变量
   ```bash
   export SECRET_KEY='your-secret-key'
   export DATABASE_URL='mongodb://localhost:27017/'
   ```

3. 运行应用
   ```bash
   python main.py
   ```

## 贡献

1. Fork 仓库
2. 创建新分支
3. 提交更改
4. 创建 Pull Request

## 许可证

[MIT License](LICENSE) 