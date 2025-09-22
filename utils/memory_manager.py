"""临时记忆管理模块
用于存储和管理用户的临时对话记忆
"""

import json
import os
from pathlib import Path
from typing import List, Dict
from datetime import datetime

class MemoryManager:
    def __init__(self, max_rounds: int = 50, storage_dir: str = "data/temp_memory"):
        """初始化记忆管理器
        
        Args:
            max_rounds: 每个用户最大存储轮数
            storage_dir: 存储目录路径
        """
        self.max_rounds = max_rounds
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_user_file(self, user_id: str) -> Path:
        """获取用户记忆文件路径"""
        return self.storage_dir / f"{user_id}.json"
        
    def add_memory(self, user_id: str, message: str, is_bot: bool = False):
        """添加一条记忆
        
        Args:
            user_id: 用户ID
            message: 消息内容
            is_bot: 是否是机器人发送的消息
        """
        mem_file = self._get_user_file(user_id)
        memories = self._load_memories(user_id)
        
        # 添加新记忆
        memories.append({
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "is_bot": is_bot
        })
        
        # 只保留最近的max_rounds条
        if len(memories) > self.max_rounds:
            memories = memories[-self.max_rounds:]
            
        # 保存到文件
        with open(mem_file, 'w', encoding='utf-8') as f:
            json.dump(memories, f, ensure_ascii=False, indent=2)
            
    def _load_memories(self, user_id: str) -> List[Dict]:
        """加载用户记忆"""
        mem_file = self._get_user_file(user_id)
        if not mem_file.exists():
            return []
            
        try:
            with open(mem_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
            
    def get_memories(self, user_id: str) -> List[Dict]:
        """获取用户记忆"""
        return self._load_memories(user_id)
        
    def clear_memories(self, user_id: str):
        """清空用户记忆"""
        mem_file = self._get_user_file(user_id)
        if mem_file.exists():
            mem_file.unlink()
