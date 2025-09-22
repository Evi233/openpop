import json
import os
from typing import Dict, Any
from utils.tools.weather import get_weather_by_city

def get_tools():
    """读取并返回./../data/tools.json文件内容"""
    file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'tools.json')
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def use_tools(tool_name: str, params) -> Dict[str, Any]:
    """
    根据工具名和参数执行相应操作
    :param tool_name: 工具名（如 "get_weather"）
    :param params: 参数，可以是 JSON 字符串、字典或其他类型
    :return: 执行结果（字典格式）
    """
    # 处理不同类型的参数输入
    if isinstance(params, str):
        try:
            params_dict = json.loads(params)  # 尝试解析为JSON
        except json.JSONDecodeError:
            params_dict = params  # 如果不是JSON，保持原样
    elif isinstance(params, dict):
        params_dict = params
    else:
        params_dict = params  # 其他类型直接传递

    # 根据工具名执行不同操作
    if tool_name == "get_weather":
        return get_weather_by_city(params_dict)
    else:
        return {"error": f"Tool '{tool_name}' not found"}

