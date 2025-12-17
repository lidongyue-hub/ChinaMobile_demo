import logging
import sys
from logging.handlers import RotatingFileHandler
import os

# 确保 logs 目录存在
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def setup_logging():
    """配置根 Logger，使其对所有模块生效"""
    logger = logging.getLogger()
    
    # 避免重复配置
    if logger.handlers:
        return
        
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s.%(funcName)s:%(lineno)d: %(message)s"
    )
    
    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件输出 (每天轮转，保留 7 天)
    file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, "backend.log"),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=7,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
