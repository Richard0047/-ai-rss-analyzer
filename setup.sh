#!/bin/bash

echo "=== 开始部署新闻聚合机器人 ==="

# 1. 更新系统
echo "1. 更新系统..."
sudo apt-get update
sudo apt-get -y upgrade

# 2. 安装系统依赖
echo "2. 安装系统依赖..."
sudo apt-get install -y supervisor python3-pip python3-venv git

# 3. 创建 Python 虚拟环境
echo "3. 创建 Python 虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 4. 安装项目依赖
echo "4. 安装项目依赖..."
pip install --upgrade pip
pip install -r requirements.txt

# 5. 创建数据和日志目录
echo "5. 创建数据和日志目录..."
mkdir -p src/data

# 6. 配置日志目录
echo "6. 配置日志目录..."
sudo mkdir -p /var/log/news_bot
sudo chown -R ubuntu:ubuntu /var/log/news_bot

# 7. 配置 Supervisor
echo "7. 配置 Supervisor..."
sudo tee /etc/supervisor/conf.d/news_bot.conf << 'SUPERVISOR'
[program:news_bot]
directory=/home/ubuntu/news_bot
command=/home/ubuntu/news_bot/venv/bin/python -m src.main
user=ubuntu
autostart=true
autorestart=true
stderr_logfile=/var/log/news_bot/err.log
stdout_logfile=/var/log/news_bot/out.log
environment=PYTHONUNBUFFERED=1,PYTHONPATH="/home/ubuntu/news_bot"
SUPERVISOR

# 8. 重启 Supervisor
echo "8. 重启 Supervisor..."
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart news_bot

echo "=== 部署完成 ==="
