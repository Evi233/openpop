# utils/api_utils.py

"""API 工具模块
包含与Deepseek API交互和消息解析相关的工具函数
"""
from openai import OpenAI
from typing import List, Dict
import re
import json

# 假设这些是你自己的模块，如果不存在，请确保创建或注释掉
try:
    from utils.tools_manager import get_tools, use_tools
    from utils.user_stats import parse_weight_tags, set_user_weight
    from utils.long_term_memory import LongTermMemory
    from utils.logger import log_info, log_error
except ImportError:
    # 提供占位符以确保代码可运行，即使依赖不完整
    def get_tools(): return []
    def use_tools(name, args): return f"Tool '{name}' used with args: {args}"
    def parse_weight_tags(text): return text, []
    def set_user_weight(user, weight): pass
    class LongTermMemory:
        def add_memory(self, sender, content): pass
    def log_info(msg): print(f"[INFO] {msg}")
    def log_error(msg): print(f"[ERROR] {msg}")


def call_deepseek_chat_api(client: OpenAI, messages: List[Dict], model: str = "deepseek-chat") -> str:
    """调用Deepseek聊天API获取响应，支持工具调用
    
    Args:
        client: OpenAI客户端实例
        messages: 符合OpenAI格式的对话列表
        model: 使用的模型名称，默认为"deepseek-chat"
        
    Returns:
        str: API返回的最终响应内容
    """
    tools = get_tools()
    print("\n" + "="*25 + " 发送给API的JSON (第一次调用) " + "="*25)
    print(json.dumps(messages, ensure_ascii=False, indent=2))
    print("="*75 + "\n")
    try:
        # 第一次API调用
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools if tools else None,
            tool_choice="auto",
            temperature=0.7,
        )
        
        message = response.choices[0].message
        
        # 处理工具调用
        if hasattr(message, 'tool_calls') and message.tool_calls:
            # 添加助手消息（包含工具调用）
            messages.append({
                "role": "assistant",
                "content": message.content if message.content else "",
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    } for tool_call in message.tool_calls
                ]
            })
            
            # 处理每个工具调用
            for tool_call in message.tool_calls:
                tool_result = use_tools(
                    tool_call.function.name,
                    tool_call.function.arguments
                )
                
                # 添加工具响应
                messages.append({
                    "role": "tool",
                    "content": str(tool_result),
                    "tool_call_id": tool_call.id
                })
            
            # 第二次API调用
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools if tools else None,
                temperature=0.7,
            )
            message = response.choices[0].message
        
        return message.content if message.content else ""

    except Exception as e:
        log_error(f"调用 DeepSeek API 时出错: {e}")
        return "抱歉，我在连接我的大脑时遇到了一点问题，请稍后再试。"


def parse_chat_response_xml(xml_string: str, sender: str = "system") -> tuple[list[str], list[tuple[str, float]], list[dict], list[str]]:
    """解析聊天响应中的XML格式消息、权重标签、记忆内容和引用回复

    Args:
        xml_string: 包含XML格式消息的字符串
        sender: 消息发送者名称，用于记忆存储

    Returns:
        tuple: (消息列表, 权重设置列表, 记忆内容对象列表, 引用回复列表)
        如果没有找到任何标签，则返回原始内容作为消息列表中的唯一元素，其他列表为空
    """
    # 检查是否包含任何我们关心的XML标签
    if not re.search(r'<(message|memory|user_weights|quote)[^>]*>', xml_string, re.S):
        return ([xml_string.strip()], [], [], [])

    # 提取并移除 <user_weights> 标签
    weight_settings = []
    weight_match = re.search(r'<user_weights>(.*?)</user_weights>', xml_string, re.S)
    if weight_match:
        weight_content = weight_match.group(1)
        user_tags = re.findall(r'<user\s+name="([^"]+)"\s+weight="([^"]+)"/>', weight_content)
        for name, weight in user_tags:
            try:
                weight_settings.append((name, float(weight)))
            except ValueError:
                log_error(f"无效的权重值 '{weight}' for user '{name}'")
        xml_string = xml_string[:weight_match.start()] + xml_string[weight_match.end():]

    messages = re.findall(r'<message>(.*?)</message>', xml_string, re.S)
    memory_contents_raw = re.findall(r'<memory>(.*?)</memory>', xml_string, re.S)
    quotes = re.findall(r'<quote>(.*?)</quote>', xml_string, re.S)

    cleaned_messages = []
    for msg in messages:
        cleaned_msg = re.sub(r'<thinking>.*?</thinking>', '', msg, flags=re.S).strip()
        if cleaned_msg:
            cleaned_messages.append(cleaned_msg)

    cleaned_quotes = []
    for q in quotes:
        cleaned_q = re.sub(r'<thinking>.*?</thinking>', '', q, flags=re.S).strip()
        if cleaned_q:
            cleaned_quotes.append(cleaned_q)

    if not cleaned_messages and not memory_contents_raw and not weight_settings and not cleaned_quotes and xml_string.strip():
        return [xml_string.strip()], [], [], []

    # 存储长期记忆（解析 memory 为 JSON，提取 topic/summary）
    parsed_memory_for_return = []
    if memory_contents_raw:
        try:
            memory_db = LongTermMemory()
            for raw_memory_json in memory_contents_raw:
                if raw_memory_json.strip():
                    try:
                        parsed_memory = json.loads(raw_memory_json)
                        topic = parsed_memory.get("topic", "未知主题")
                        summary = parsed_memory.get("summary", raw_memory_json)
                        memory_db.add_memory(sender=sender, topic=topic, summary=summary)
                        parsed_memory_for_return.append(parsed_memory)
                    except json.JSONDecodeError as jde:
                        log_error(f"解析<memory>标签内JSON失败: {raw_memory_json} - {jde}")
                    except Exception as add_e:
                        log_error(f"添加长期记忆（已解析）失败: {raw_memory_json} - {add_e}")
        except Exception as e:
            log_error(f"初始化或处理长期记忆时发生错误: {str(e)}")

    return cleaned_messages, weight_settings, parsed_memory_for_return, cleaned_quotes
