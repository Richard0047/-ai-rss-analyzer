import logging
import signal
import sys
from src.scheduler import NewsScheduler  # 使用绝对导入

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def signal_handler(signum, frame):
    """处理退出信号"""
    logging.info("接收到退出信号，正在停止服务...")
    sys.exit(0)

def main():
    """主程序入口"""
    try:
        # 注册信号处理
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        scheduler = NewsScheduler()
        scheduler.start()
    except Exception as e:
        logging.error(f"程序运行出错: {str(e)}", exc_info=True)
    finally:
        logging.info("程序已退出")

if __name__ == "__main__":
    main() 