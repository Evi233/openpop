"""监听列表管理模块
提供对listen_list.json配置文件的增删改查功能
"""

import json
import os
from typing import List

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'listen_list.json')

def get_listen_list() -> List[str]:
    """获取当前监听列表
    
    Returns:
        List[str]: 当前监听的对象列表
    """
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config['listen_list']

def add_to_listen_list(name: str) -> bool:
    """添加新的监听对象
    
    Args:
        name: 要添加的对象名称
        
    Returns:
        bool: 是否添加成功(False表示已存在)
    """
    config = {}
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    if name in config['listen_list']:
        return False
        
    config['listen_list'].append(name)
    
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)
    return True

def remove_from_listen_list(name: str) -> bool:
    """移除监听对象
    
    Args:
        name: 要移除的对象名称
        
    Returns:
        bool: 是否移除成功(False表示不存在)
    """
    config = {}
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    if name not in config['listen_list']:
        return False
        
    config['listen_list'].remove(name)
    
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)
    return True

def save_listen_list(names: List[str]) -> None:
    """直接保存整个监听列表(覆盖)
    
    Args:
        names: 新的监听对象列表
    """
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump({'listen_list': names}, f, ensure_ascii=False, indent=4)
