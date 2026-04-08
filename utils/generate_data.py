import pandas as pd
import numpy as np
import random

def generate_health_dataset(num_records=1000):
    data = []
    for _ in range(num_records):
        # 随机生成基础指标
        hr = random.randint(50, 120)       # 心率
        sleep = round(random.uniform(4, 11), 1) # 睡眠
        steps = random.randint(500, 15000)   # 步数
        
        # 简单的逻辑标注算法 (这就是 AI 要学习的规则)
        score = 0
        if hr > 100 or hr < 60: score += 1   # 心率异常
        if sleep < 6 or sleep > 10: score += 1 # 睡眠异常
        if steps < 4000: score += 1           # 运动极少
        
        # 根据得分确定等级
        if score == 0:
            label = 0  # 健康
        elif score == 1:
            label = 1  # 亚健康
        else:
            label = 2  # 高风险
            
        data.append([hr, sleep, steps, label])

    # 转换为 DataFrame
    columns = ['heart_rate', 'sleep_hours', 'steps', 'health_label']
    df = pd.DataFrame(data, columns=columns)
    
    # 保存为 CSV 文件
    df.to_csv('health_training_data.csv', index=False)
    print(f"成功生成 {num_records} 条训练数据，已保存至 health_training_data.csv")

if __name__ == "__main__":
    generate_health_dataset()