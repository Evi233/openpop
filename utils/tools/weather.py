import requests
import json

def get_weather_by_city(city_name):
    """
    获取指定城市的天气信息
    
    参数:
        city_name (str): 城市名称
        
    返回:
        dict: 包含天气信息的JSON数据
    """
    # 构造API URL
    url = f"https://api.asilu.com/weather/?city={city_name}"
    
    try:
        # 发送GET请求
        response = requests.get(url)
        response.raise_for_status()  # 检查请求是否成功
        
        # 返回JSON数据
        return response.json()
        
    except requests.exceptions.RequestException as e:
        # 处理请求异常
        print(f"获取天气信息时出错: {e}")
        return None
    except json.JSONDecodeError as e:
        # 处理JSON解析异常
        print(f"解析天气信息时出错: {e}")
        return None

# 示例用法
if __name__ == "__main__":
    city = input("请输入城市名: ")
    weather_data = get_weather_by_city(city)
    
    if weather_data:
        print("获取到的天气信息:")
        print(json.dumps(weather_data, indent=4, ensure_ascii=False))
    else:
        print("未能获取天气信息")
