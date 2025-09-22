"""聊天记录保存模块
将聊天记录保存为JSON格式
"""

import json
import os
from pathlib import Path
from datetime import datetime

# 聊天记录目录
HISTORY_DIR = os.path.join(os.path.dirname(__file__), '..', 'chat_history')
# 确保目录存在
Path(HISTORY_DIR).mkdir(parents=True, exist_ok=True)

def save_chat_history(sender: str, user_message: str, ai_response: str):
    """保存单条聊天记录
    
    Args:
        sender: 发送者名称
        user_message: 用户消息内容
        ai_response: AI回复内容
    """
    # 当前日期作为文件名
    today = datetime.now().strftime('%Y-%m-%d')
    history_file = os.path.join(HISTORY_DIR, f'{today}.json')
    
    # 创建记录数据结构
    record = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'sender': sender,
        'user_message': user_message,
        'ai_response': ai_response
    }
    
    # 读取现有记录或创建新文件
    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        history = []
    
    # 添加新记录
    history.append(record)
    
    # 保存文件
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
