"""图片处理模块
用于识别和描述图片内容
"""

import requests
import json
import logging
from typing import Optional
from pathlib import Path

class ImageProcessor:
    def __init__(self, api_key: str, base_url: str = ""):
        """初始化图片处理器
        
        Args:
            api_key: API密钥
            base_url: API基础URL
        """
        self.api_key = api_key
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)
        
    def describe_image(self, image_url: str) -> Optional[str]:
        """描述图片内容
        
        Args:
            image_url: 图片URL
            
        Returns:
            str: 图片描述文本 (100字以内)
            None: 描述失败时返回None
        """
        try:
            url = f"{self.base_url}/chat/completions"
            payload = json.dumps({
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "system",
                        "content": "用户将会发送给你图片，请用一百字以内来描述图片，尽可能的详细"
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "描述："
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url
                                }
                            }
                        ]
                    }
                ]
            })
            
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            response = requests.post(url, headers=headers, data=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            return result.get('choices', [{}])[0].get('message', {}).get('content')
            
        except Exception as e:
            self.logger.error(f"图片描述失败: {e}")
            return None

    def save_image(self, image_url: str, save_path: str) -> bool:
        """保存图片到本地
        
        Args:
            image_url: 图片URL
            save_path: 保存路径
            
        Returns:
            bool: 是否保存成功
        """
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return True
            
        except Exception as e:
            self.logger.error(f"图片保存失败: {e}")
            return False
