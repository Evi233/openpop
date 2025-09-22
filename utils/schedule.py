import json
from datetime import datetime
from openai import OpenAI
from utils.logger import logger
import os

class Schedule:
    def __init__(self, baseurl,api_key: str):
        """日程管理类
        
        Args:
            api_key: API密钥
        """
        self.client = OpenAI(api_key=api_key, base_url=baseurl)
        self.schedule_file = "data/schedule.json"
        
    def generate_schedule(self) -> dict:
        """生成并返回日程JSON
        
        Returns:
            dict: 包含日程信息的JSON对象
        """
        try:
            prompt = """今天是{current_date}，你是泡泡，是一个初中生。请严格按照JSON格式生成日程安排，输出示例：
            [
                {{
                    "name": "工作",
                    "time": "09:00-12:00"
                }},
                {{
                    "name": "休息",
                    "time": "12:00-13:00"
                }}...... 
            ]
            
            要求：
            1. 必须输出合法JSON格式
            2. 每个任务必须包含name和time字段
            3. 时间安排合理不冲突
            4. 包含适当的休息时间
            5. 总任务数控制在6-8个""".format(
                current_date=datetime.now().strftime("%Y-%m-%d")
            )
            
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                response_format={"type": "json_object"},
                max_tokens=1000
            )
            
            schedule = json.loads(response.choices[0].message.content)
            self._save_schedule(schedule)
            logger.info("成功生成并保存日程JSON")
            return schedule
            
        except Exception as e:
            logger.error(f"生成日程失败: {str(e)}")
            raise

    def _save_schedule(self, schedule: dict):
        """保存日程到文件"""
        os.makedirs(os.path.dirname(self.schedule_file), exist_ok=True)
        with open(self.schedule_file, 'w', encoding='utf-8') as f:
            json.dump(schedule, f, ensure_ascii=False, indent=2)

    def get_schedule(self) -> dict:
        """获取当前日程"""
        try:
            with open(self.schedule_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("未找到日程文件，将生成新日程")
            return self.generate_schedule()
        except Exception as e:
            logger.error(f"读取日程失败: {str(e)}")
            raise
