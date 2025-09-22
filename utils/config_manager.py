"""配置管理模块
提供对config.json配置文件的读写功能
"""

import json
import os
from typing import Dict, List

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.json')

def get_config() -> Dict:
    """获取当前配置
    
    Returns:
        Dict: 包含所有配置项的字典
    """
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def update_config(new_config: Dict) -> None:
    """更新整个配置文件
    
    Args:
        new_config: 新的配置字典
    """
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(new_config, f, ensure_ascii=False, indent=4)

def get_other_names_str() -> str:
    """获取other_name列表的字符串形式
    
    Returns:
        str: 用"，"连接的名称字符串
    """
    config = get_config()
    return "，".join(config['other_name'])

def update_name(new_name: str) -> None:
    """更新name配置
    
    Args:
        new_name: 新的名称
    """
    config = get_config()
    config['name'] = new_name
    update_config(config)

def update_personality(new_personality: str) -> None:
    """更新personality配置
    
    Args:
        new_personality: 新的人格描述
    """
    config = get_config()
    config['personality'] = new_personality
    update_config(config)

def update_other_names(new_names: List[str]) -> None:
    """更新other_name列表
    
    Args:
        new_names: 新的其他名称列表
    """
    config = get_config()
    config['other_name'] = new_names
    update_config(config)
