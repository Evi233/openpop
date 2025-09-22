"""日志模块
提供文件日志记录功能
"""

import logging
import os
from pathlib import Path
from datetime import datetime

# 日志目录
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
# 确保日志目录存在
Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

# 日志文件名格式
LOG_FILE = os.path.join(LOG_DIR, f"{datetime.now().strftime('%Y-%m-%d')}.log")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def log_info(message: str):
    """记录INFO级别日志"""
    logger.info(message)

def log_warning(message: str):
    """记录WARNING级别日志"""
    logger.warning(message)

def log_error(message: str):
    """记录ERROR级别日志"""
    logger.error(message)

def log_debug(message: str):
    """记录DEBUG级别日志"""
    logger.debug(message)
