import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import numpy as np
from openai import OpenAI
from utils.logger import logger
import json

class LongTermMemory:
    def __init__(self, baseurl,db_path: str = "data/memories.db", api_key: str = "000"):
        """初始化长期记忆系统
        
        Args:
            db_path: SQLite数据库路径
            api_key: OpenAI API密钥
        """
        self.db_path = db_path
        self.client = OpenAI(
            base_url=baseurl,
            api_key=api_key
        )
        self._init_db()

    def _init_db(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建记忆表，新增 'topic' 字段
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            content TEXT NOT NULL,  -- 此处存储 summary
            topic TEXT NOT NULL,    -- 新增 topic 字段
            embedding BLOB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建向量索引 (FTS5 仍索引 content 和 sender)
        cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts 
        USING fts5(sender, content, topic) -- FTS也更新为索引topic
        ''')
        
        conn.commit()
        conn.close()

    def _get_embedding(self, text: str) -> List[float]:
        """获取文本的嵌入向量
        
        Args:
            text: 要嵌入的文本
            
        Returns:
            嵌入向量列表
        """
        print(f"[DEBUG] _get_embedding called: text={text}")
        response = self.client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding

    def add_memory(self, sender: str, topic: str, summary: str):
        """添加长期记忆
        
        Args:
            sender: 发送者
            topic: 记忆的主题
            summary: 记忆的摘要内容 (用于嵌入和检索)
        """
        try:
            logger.info("Adding memory from %s (Topic: %.30s): %.50s...", sender, str(topic), str(summary))
            embedding = self._get_embedding(summary)
            embedding_str = json.dumps(embedding)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO memories (sender, content, topic, embedding)
            VALUES (?, ?, ?, ?)
            ''', (sender, summary, topic, embedding_str))
            
            cursor.execute('''
            INSERT INTO memories_fts (sender, content, topic)
            VALUES (?, ?, ?)
            ''', (sender, summary, topic))
            
            conn.commit()
            conn.close()
            logger.info(f"Memory added successfully for {sender} (Topic: {topic})")
        except Exception as e:
            logger.error(f"Failed to add memory: {str(e)}")
            raise

    def search_memories(self, query: str, sender: Optional[str] = None, limit: int = 5) -> List[Dict]:
        """
        搜索相关记忆

        Args:
            query: 搜索查询
            sender: 可选，限制特定发送者
            limit: 返回结果数量

        Returns:
            记忆列表，按相关性排序
        """
        print(f"[DEBUG] search_memories called: query={query}, sender={sender}, limit={limit}")
        logger.info("Searching memories: query='%s', sender='%s', limit=%d", query, sender, limit)
        query_embedding = self._get_embedding(query)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if sender:
            cursor.execute('''
            SELECT id, sender, content, topic, embedding, created_at
            FROM memories
            WHERE sender = ?
            ''', (sender,))
        else:
            cursor.execute('''
            SELECT id, sender, content, topic, embedding, created_at
            FROM memories
            ''')
            
        results = []
        for row in cursor.fetchall():
            try:
                similarity = self._cosine_similarity(row[4], query_embedding)
                results.append({
                    "id": row[0],
                    "sender": row[1],
                    "content": row[2],
                    "topic": row[3],
                    "created_at": row[5],
                    "similarity": similarity
                })
            except Exception as e:
                logger.error(f"Error calculating similarity: {str(e)}")
                continue
                
        results.sort(key=lambda x: x["similarity"], reverse=True)
        conn.close()
        logger.info("Memory search returned %d results. Top topics: %s", len(results[:limit]), [r['topic'] for r in results[:limit]])
        return results[:limit]

    def _cosine_similarity(self, vec1_str: str, vec2: List[float]) -> float:
        """计算两个向量的余弦相似度
        
        Args:
            vec1_str: 数据库中的向量JSON字符串
            vec2: 查询向量列表
            
        Returns:
            余弦相似度
        """
        vec1 = np.array(json.loads(vec1_str), dtype=np.float32)
        vec2 = np.array(vec2, dtype=np.float32)
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        similarity = dot_product / (norm1 * norm2)
        return max(0.0, min(1.0, similarity))

    def extract_memory_tags(self, text: str) -> List[str]:
        """从文本中提取<memory>标签内容
        
        Args:
            text: 要解析的文本
            
        Returns:
            记忆内容列表
        """
        import re
        return re.findall(r'<memory>(.*?)</memory>', text, re.DOTALL)
