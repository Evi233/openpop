"""用户互动统计模块
记录用户互动次数和时间权重
"""

import json
import os
import re
from pathlib import Path
from datetime import datetime

USER_STATS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'user_stats.json')
MAX_WEIGHT = 15

def init_user_stats():
    """初始化用户统计数据文件"""
    data_dir = os.path.dirname(USER_STATS_FILE)
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    
    if not os.path.exists(USER_STATS_FILE):
        with open(USER_STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump({"users": {}}, f, ensure_ascii=False, indent=2)

def calculate_weight(days: int, base_weight: float = 1.0) -> float:
    """计算时间权重
    Args:
        days: 距离当前时间的天数
        base_weight: 基础权重值 (1-15)
    Returns:
        float: 权重值 (0-15之间)
    """
    return max(0, min(MAX_WEIGHT, base_weight - days * 0.1))  # 每天衰减10%权重

def update_user_interaction(username: str):
    """更新用户互动记录
    Args:
        username: 用户名
    """
    init_user_stats()
    
    with open(USER_STATS_FILE, 'r+', encoding='utf-8') as f:
        data = json.load(f)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if username not in data['users']:
            data['users'][username] = {
                "interaction_count": 0,
                "interactions": [],
                "last_interaction": None,
                "base_weight": 1.0
            }
        
        # 计算距离上次互动的天数
        last_interaction = data['users'][username]['last_interaction']
        days_since = 0
        if last_interaction:
            last_date = datetime.strptime(last_interaction, '%Y-%m-%d %H:%M:%S')
            days_since = (datetime.now() - last_date).days
        
        # 添加新互动记录
        base_weight = data['users'][username].get('base_weight', 1.0)
        interaction = {
            "timestamp": now,
            "days_since": days_since,
            "weight": calculate_weight(days_since, base_weight)
        }
        
        data['users'][username]['interactions'].append(interaction)
        data['users'][username]['interaction_count'] += 1
        data['users'][username]['last_interaction'] = now
        
        # 保存更新
        f.seek(0)
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.truncate()

def set_user_weight(username: str, weight: float):
    """设置用户基础权重
    Args:
        username: 用户名
        weight: 权重值 (1-15)
    """
    init_user_stats()
    weight = max(1, min(MAX_WEIGHT, weight))  # 限制在1-15之间
    
    with open(USER_STATS_FILE, 'r+', encoding='utf-8') as f:
        data = json.load(f)
        if username not in data['users']:
            data['users'][username] = {
                "interaction_count": 0,
                "interactions": [],
                "last_interaction": None
            }
        data['users'][username]['base_weight'] = weight
        f.seek(0)
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.truncate()

def get_user_stats(username: str) -> dict:
    """获取用户统计数据
    Args:
        username: 用户名
    Returns:
        dict: 用户统计信息
    """
    init_user_stats()
    
    with open(USER_STATS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data['users'].get(username, {
            "interaction_count": 0,
            "interactions": [],
            "last_interaction": None,
            "base_weight": 1.0
        })

def get_user_weight(username: str) -> float:
    """获取用户当前权重
    Args:
        username: 用户名
    Returns:
        float: 权重值
    """
    stats = get_user_stats(username)
    if not stats['interactions']:
        return stats.get('base_weight', 1.0)
    return stats['interactions'][-1]['weight']

def parse_weight_tags(text: str) -> tuple:
    """解析权重标签
    Args:
        text: 包含权重标签的文本
    Returns:
        tuple: (清理后的文本, [(用户名, 权重)])
    """
    weight_tags = re.findall(r'<weight>(.*?):(\d+)</weight>', text)
    cleaned_text = re.sub(r'<weight>.*?</weight>', '', text)
    return cleaned_text, [(user, float(weight)) for user, weight in weight_tags]
