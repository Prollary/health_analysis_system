import requests
import time
import random

# Flask 服务器的地址
URL = "http://127.0.0.1:5000/api/sensor/upload"

def generate_mock_data(user_id=1):
    """随机生成符合常理的健康数据"""
    data = {
        "user_id": user_id,
        "heart_rate": random.randint(60, 100),       # 模拟心率在 60-100 之间波动
        "sleep_hours": round(random.uniform(5, 9), 1), # 模拟睡眠 5-9 小时
        "steps": random.randint(1000, 15000),         # 模拟步数
        "temperature": round(random.uniform(36.1, 37.2), 1) # 模拟体温
    }
    return data

def start_simulation(interval=5):
    """
    开始模拟发送数据
    :param interval: 发送间隔时间（秒）
    """
    print(f"🚀 模拟传感器已启动，目标地址: {URL}")
    print(f"⏰ 每隔 {interval} 秒发送一次数据，按 Ctrl+C 停止...\n")
    
    try:
        while True:
            # 1. 生成数据
            payload = generate_mock_data(user_id=1)
            
            # 2. 发送 POST 请求
            try:
                response = requests.post(URL, json=payload, timeout=5)
                
                # 3. 打印结果
                if response.status_code == 200:
                    print(f"✅ 发送成功: {payload}")
                else:
                    print(f"❌ 发送失败，状态码: {response.status_code}, 详情: {response.text}")
            
            except requests.exceptions.ConnectionError:
                print("⚠️ 无法连接到服务器，请确保 Flask 应用已运行且地址正确。")
            
            # 4. 等待
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n🛑 模拟已停止。")

if __name__ == "__main__":
    start_simulation(interval=3) # 每 3 秒发送一次