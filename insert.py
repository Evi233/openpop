import sqlite3
from utils.logger import logger

def reset_memory_ids():
    """重置memories表的ID序列"""
    try:
        conn = sqlite3.connect('data/memories.db')
        cursor = conn.cursor()
        
        # 1. 创建新表结构
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS memories_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            content TEXT NOT NULL,
            embedding BLOB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 2. 转移数据并重置ID
        cursor.execute('''
        INSERT INTO memories_new (sender, content, embedding, created_at)
        SELECT sender, content, embedding, created_at 
        FROM memories 
        ORDER BY created_at
        ''')
        
        # 3. 删除原表
        cursor.execute('DROP TABLE memories')
        
        # 4. 重命名新表
        cursor.execute('ALTER TABLE memories_new RENAME TO memories')
        
        # 4. 重建索引
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_memories_sender 
        ON memories(sender)
        ''')
        
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_memories_created_at 
        ON memories(created_at)
        ''')
        
        conn.commit()
        # 验证ID是否从1开始
        cursor.execute('SELECT MIN(id), MAX(id), COUNT(*) FROM memories')
        min_id, max_id, count = cursor.fetchone()
        logger.info(f"成功重置memories表的ID序列: 最小ID={min_id}, 最大ID={max_id}, 记录数={count}")
        
    except Exception as e:
        logger.error(f"重置ID序列失败: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    reset_memory_ids()
