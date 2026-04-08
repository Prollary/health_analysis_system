import pandas as pd
import numpy as np
import random

def generate_health_dataset(num_records=10000):
    data = []
    for _ in range(num_records):
        # --- 1. 模拟生理指标 ---
        hr = random.randint(50, 120)        # 心率
        sleep = round(random.uniform(4, 10), 1) # 睡眠
        steps = random.randint(500, 15000)    # 步数
        
        # --- 2. 模拟环境指标 ---
        # 设定一定的概率出现异常环境
        is_bad_env = random.random() < 0.2 
        if is_bad_env:
            room_temp = round(random.uniform(27.0, 33.0), 1) # 高温
            co2 = random.randint(1200, 2500)                # 高浓度CO2
            humidity = round(random.uniform(70.0, 90.0), 1)  # 高湿度
        else:
            room_temp = round(random.uniform(20.0, 25.0), 1) # 舒适
            co2 = random.randint(400, 800)                  # 清新
            humidity = round(random.uniform(40.0, 60.0), 1)  # 适宜

        # --- 3. 联动标注逻辑 (AI学习的核心规则) ---
        penalty = 0
        # 生理异常
        if hr > 100 or hr < 60: penalty += 1
        if steps < 3000: penalty += 1
        
        # 联动异常：环境差 + 表现差 -> 权重更高
        if room_temp > 28.0 and sleep < 6.5: penalty += 2 # 高温导致睡眠质量极差
        if co2 > 1500 and steps < 1000: penalty += 1      # 空气浊且久坐
        
        # 确定标签 (0:健康, 1:亚健康, 2:风险)
        if penalty == 0:
            label = 0
        elif penalty <= 2:
            label = 1
        else:
            label = 2
            
        data.append([hr, sleep, steps, room_temp, humidity, co2, label])

    # 导出 CSV
    columns = ['heart_rate', 'sleep_hours', 'steps', 'room_temp', 'humidity', 'co2_level', 'health_label']
    df = pd.DataFrame(data, columns=columns)
    df.to_csv('health_training_data_v2.csv', index=False)
    print(f"✅ 已生成包含环境维度的训练集：health_training_data_v2.csv ({num_records}条)")

if __name__ == "__main__":
    generate_health_dataset()