from wxauto import WeChat
from openai import OpenAI
import time
import json
import os
import random
import requests
from datetime import datetime
from utils.willingness import WillingnessCalculator # type: ignore
from utils.image_processor import ImageProcessor # type: ignore
from utils.api_utils import call_deepseek_chat_api, parse_chat_response_xml # type: ignore
from utils.schedule import Schedule # type: ignore
from utils.logger import log_info, log_warning, log_error # type: ignore
from utils.chat_history import save_chat_history # type: ignore
from utils.user_stats import update_user_interaction # type: ignore
from utils.memory_manager import MemoryManager # type: ignore
from utils.long_term_memory import LongTermMemory # type: ignore
from utils.prompt_builder import PromptBuilder # type: ignore
from utils.moderation import ContentModerator, is_content_safe # type: ignore


# 加载配置文件
config_dir = os.path.join(os.path.dirname(__file__), 'config')
# 加载监听列表
with open(os.path.join(config_dir, 'listen_list.json'), 'r', encoding='utf-8') as f:
    listen_list = json.load(f)['listen_list']
# 加载主配置
with open(os.path.join(config_dir, 'config.json'), 'r', encoding='utf-8') as f:
    app_config = json.load(f)
# 处理other_name列表
other_names_str = "，".join(app_config['other_name'])
# 配置OpenAI API
base = app_config['other_name']['base_url']
key = app_config['other_name']['key']
image_processor_key = app_config['image_processor_key']
long_term_memory_key = app_config['long_term_memory_key']
moderator_key = app_config['moderator_key']
client = OpenAI(api_key=key, base_url=base)
wx = WeChat()
willingness_calc = WillingnessCalculator()  # 初始化意愿计算器
image_processor = ImageProcessor(base_url=base,api_key=image_processor_key)  # 初始化图片处理器
memory_manager = MemoryManager()  # 初始化记忆管理器
long_term_memory = LongTermMemory(baseurl=base,api_key=long_term_memory_key)  # 初始化长期记忆
prompt_builder = PromptBuilder(app_config)  # 初始化prompt构建器
schedule_manager = Schedule(baseurl=base,api_key=key)  # 初始化日程管理器
last_schedule_check = None
moderator = ContentModerator(baseurl=base,api_key=moderator_key)  # 初始化内容审查器

def get_history():

    # 加载更多历史消息
    wx.LoadMoreMessage()

    # 获取当前聊天窗口消息
    msgs = wx.GetAllMessage()
    #返回msgs
    return msgs
def on_message(msg, chat):
    log_info(f"收到来自 {chat.name} 的消息: {msg.content}")

for i in listen_list:
    wx.AddListenChat(nickname=i, callback=on_message)

wait = 1  # 设置3秒查看一次是否新消息
while True:
    try:
        # 每天0点生成新日程
        current_time = datetime.now()
        if current_time.hour == 0 and (last_schedule_check is None or last_schedule_check.day != current_time.day):
            schedule = schedule_manager.generate_schedule()
            log_info(f"已生成今日日程: {json.dumps(schedule, ensure_ascii=False, indent=2)}")
            last_schedule_check = current_time

        msgs = wx.GetNextNewMessage()
        for chat in msgs:
            one_msgs = msgs.get(chat)   # 获取消息内容
            
            # 回复收到
            for msg in one_msgs:

                if msg.type == 'friend':
                    sender = msg.sender
                    location_name = '私聊'
                    user_key = f"{sender}@{location_name}"
                    log_info(f'收到来自 [{location_name}] 的 [{sender}] 的消息: {msg.content}')
                    # 存储用户消息到临时记忆
                    memory_manager.add_memory(user_key, msg.content, is_bot=False)

                    # 计算回复概率并随机决定是否回复
                    reply_prob = willingness_calc.calculate_reply_probability(msg.content, sender, location_name)
                    should_reply = random.random() < reply_prob
                    log_info(f'回复概率: {reply_prob:.2%}, 决定: {"回复" if should_reply else "不回复"}')

                    if not should_reply:
                        continue

                    timenow = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                    log_info(f'当前时间：{timenow}')
                    # 获取用户最近的对话记忆
                    recent_memories = memory_manager.get_memories(user_key)
                    log_info(f'最近的对话记忆：{recent_memories}')
                    memory_context = "\n".join(
                        f"{'你' if mem['is_bot'] else sender}: {mem['message']}" 
                        for mem in recent_memories
                    )
                    log_info(f'格式化后的记忆上下文：{memory_context}')

                    # 搜索相关长期记忆(相似度>0.7)
                    related_memories = long_term_memory.search_memories(msg.content, sender=sender)
                    memory_recall = []
                    for mem in related_memories:
                        if mem.get('similarity', 0) > 0.7:
                            memory_recall.append(mem['content'])
                    log_info(f'相关长期记忆：{memory_recall}')
                    # 获取并格式化当前日程任务
                    current_schedule = schedule_manager.get_schedule()
                    current_tasks = json.dumps([
                        {
                            "name": task["name"],
                            "time": task["time"]
                        }
                        for task in current_schedule.get("tasks", [])
                    ], ensure_ascii=False, indent=4)

                    # 准备额外上下文，包含相关记忆和当前任务
                    additional_context = ""
                    if memory_recall:
                        additional_context += "相关记忆：\n" + "\n".join(f"- {mem}" for mem in memory_recall) + "\n\n"
                    if current_tasks:
                        additional_context += "当前计划任务：\n" + current_tasks + "\n"

                    prompt = prompt_builder.build_chat_prompt(
                        sender=sender,
                        message=msg.content,
                        memory_context=recent_memories,
                        current_time=timenow,
                        additional_context=additional_context.strip()
                    )
                    response = call_deepseek_chat_api(client, prompt)
                    log_info(f'API响应：{response}')
                    messages, weight_settings, _ = parse_chat_response_xml(response, sender=sender)
                    log_info(f'解析后的消息：{messages}')
                    if weight_settings:
                        for user, weight in weight_settings:
                            log_info(f'设置用户权重 - {user}: {weight}')
                    # 保存聊天记录和更新用户统计
                    save_chat_history(user_key, msg.content, response)
                    update_user_interaction(user_key)

                    # <<< 这里是实现你需求的核心修改点 >>>
                    if messages:
                        # 拼接所有消息为一个字符串，模拟机器人一次性说完所有话
                        full_bot_response = "\n".join(messages)
                        # 只存一次完整回复到记忆
                        memory_manager.add_memory(user_key, full_bot_response, is_bot=True)
                        log_info(f"已将拼接后的回复存入记忆 for '{user_key}': '{full_bot_response.replace(chr(10), ' ')}'")

                    for message_to_send in messages:
                        # 内容审查
                        if message_to_send.strip() if isinstance(message_to_send, str) else True:
                            log_info(f'发送给 [{location_name}] 的消息: \"{message_to_send}\"')
                            chat.SendMsg(message_to_send)
                            # 不再为每条消息单独调用 add_memory
                            time.sleep(random.uniform(0.5, 1.5))
                    # 此处将msg.content传递给大模型，再由大模型返回的消息回复即可实现ai聊天

        time.sleep(wait)
    except KeyboardInterrupt:
        log_warning('程序被用户中断退出')
        break
