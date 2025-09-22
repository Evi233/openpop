import time
import random
import json
from typing import Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
from utils.logger import log_info, log_warning

class WillingnessCalculator:
    def __init__(self, bot_config: Dict):
        self.bot_name = bot_config.get("name", "泡泡")
        self.bot_aliases = bot_config.get("other_name", [])
        
        self.user_profiles: Dict[str, Dict[str, Any]] = {}
        self.last_check_time = datetime.now()
        self.CHECK_INTERVAL = timedelta(seconds=10)

        # --- 新增：模式状态管理 ---
        self.global_reply_mode = "default"  # 'default', 'high', 'low', 'always', 'test'
        self.user_reply_overrides = {}    # e.g., {"张三@私聊": "always"}

        # --- 核心参数 ---
        self.HIGH_MODE_BASE_PROB = 0.75
        self.LOW_MODE_BASE_PROB = 0.15
        self.FOLLOW_UP_PROB_BONUS = 0.4
        self.MENTION_GUARANTEED_PROB = 0.95
        self.EMOJI_PROB_MULTIPLIER = 0.3
        self.FOLLOW_UP_THRESHOLD = timedelta(minutes=2)
        self.CONTEXT_RESET_THRESHOLD = timedelta(minutes=5)

    # --- 新增：模式控制方法 ---
    def set_global_mode(self, mode: str) -> bool:
        """设置全局回复模式。"""
        valid_modes = ["default", "high", "low", "always", "test"]
        if mode in valid_modes:
            self.global_reply_mode = mode
            log_info(f"全局回复模式已切换为: {mode}")
            return True
        return False

    def set_user_override(self, user_key: str, mode: str) -> bool:
        """为特定用户设置覆盖模式。"""
        valid_modes = ["always", "low", "default"]
        if mode in valid_modes:
            if mode == "default":
                self.user_reply_overrides.pop(user_key, None)
                log_info(f"用户 '{user_key}' 的特定回复模式已移除。")
            else:
                self.user_reply_overrides[user_key] = mode
                log_info(f"用户 '{user_key}' 的回复模式已设置为: {mode}")
            return True
        return False

    def _get_or_create_user_profile(self, user_key: str) -> Dict[str, Any]:
        if user_key not in self.user_profiles:
            self.user_profiles[user_key] = {
                "last_message_time": datetime.now(),
                "last_reply_time": None,
                "last_skip_time": None,
                "is_high_mode": False,
                "context_reset_time": datetime.now(),
            }
        return self.user_profiles[user_key]

    def _check_and_switch_mode(self, user_key: str):
        # 这里可以实现更复杂的动态模式切换逻辑
        profile = self._get_or_create_user_profile(user_key)
        # 示例：根据时间或活跃度切换高/低模式
        now = datetime.now()
        if profile["last_reply_time"] and (now - profile["last_reply_time"] < timedelta(minutes=10)):
            profile["is_high_mode"] = True
        else:
            profile["is_high_mode"] = False

    def _periodic_checks(self):
        now = datetime.now()
        if now - self.last_check_time > self.CHECK_INTERVAL:
            # 可以在这里做一些周期性检查或状态清理
            self.last_check_time = now

    # --- 修改：calculate_reply_probability 集成新模式 ---
    def calculate_reply_probability(self, content: str, sender: str, chat_name: str) -> float:
        user_key = f"{sender}@{chat_name}"

        # 1. 检查强制模式 (用户特定 > 全局)
        user_mode = self.user_reply_overrides.get(user_key)
        if user_mode == "always":
            log_info(f"用户 '{user_key}' 触发 'always' 模式，强制回复。")
            return 1.0
        if user_mode == "low":
            log_info(f"用户 '{user_key}' 触发 'low' 模式，强制不回复。")
            return 0.0
            
        if self.global_reply_mode == "always":
            log_info("全局 'always' 模式触发，强制回复。")
            return 1.0
        if self.global_reply_mode == "test":
            log_info("全局 'test' 模式触发，强制不回复。")
            return 0.0

        # 2. 如果是 'default' 或 'high'/'low'，则进入动态计算
        self._periodic_checks()
        profile = self._get_or_create_user_profile(user_key)
        self._check_and_switch_mode(user_key)

        # 检查是否被@或提及
        is_mentioned = False
        mention_keywords = [self.bot_name] + self.bot_aliases
        for kw in mention_keywords:
            if kw in content:
                is_mentioned = True
                break
        if is_mentioned:
            log_info(f"消息中提及了机器人，回复概率提升至 {self.MENTION_GUARANTEED_PROB}")
            return self.MENTION_GUARANTEED_PROB

        # 基础概率
        if profile["is_high_mode"]:
            base_prob = self.HIGH_MODE_BASE_PROB
        else:
            base_prob = self.LOW_MODE_BASE_PROB

        # high/low 模式下调整基础概率
        if self.global_reply_mode == "high":
            base_prob = min(1.0, base_prob + 0.3)
        elif self.global_reply_mode == "low":
            base_prob = max(0.0, base_prob - 0.3)

        # 连续对话加成
        now = datetime.now()
        follow_up_bonus = 0.0
        if profile["last_reply_time"] and (now - profile["last_reply_time"] < self.FOLLOW_UP_THRESHOLD):
            follow_up_bonus = self.FOLLOW_UP_PROB_BONUS

        # emoji加成
        emoji_bonus = 0.0
        emoji_count = sum(1 for c in content if ord(c) > 10000)
        if emoji_count > 0:
            emoji_bonus = self.EMOJI_PROB_MULTIPLIER * min(emoji_count, 3)

        # 计算最终概率
        final_prob = base_prob + follow_up_bonus + emoji_bonus
        final_prob = max(0.0, min(1.0, final_prob))

        log_info(f"意愿计算 for '{user_key}': 全局模式='{self.global_reply_mode}', 动态模式={'高' if profile['is_high_mode'] else '低'}, "
                 f"最终概率={final_prob:.2%}")

        return final_prob

    def update_state_after_reply(self, sender: str, chat_name: str):
        user_key = f"{sender}@{chat_name}"
        profile = self._get_or_create_user_profile(user_key)
        profile["last_reply_time"] = datetime.now()
        profile["last_message_time"] = datetime.now()
        profile["context_reset_time"] = datetime.now()
        # 可以在这里添加更多状态更新逻辑

    def update_state_after_skip(self, sender: str, chat_name: str):
        user_key = f"{sender}@{chat_name}"
        profile = self._get_or_create_user_profile(user_key)
        profile["last_skip_time"] = datetime.now()
        profile["last_message_time"] = datetime.now()
        # 可以在这里添加更多状态更新逻辑
