# -*- coding: utf-8 -*-
"""
模拟传感器 - 用户 ID=3（居家老人）
双击此文件即可运行，数据发送至本机 Flask 后端
"""
import requests
import time
import random
import sys

URL     = "http://127.0.0.1:5000/api/sensor/upload"
USER_ID = 3
NAME    = "用户3（居家老人）"

BANNER = f"""
╔══════════════════════════════════════════════╗
║      HealthAI 智慧舱 · 模拟传感器             ║
║      目标用户：{NAME:<24}  ║
║      发送地址：{URL:<24}  ║
╚══════════════════════════════════════════════╝
  按 Ctrl+C 停止模拟
"""

def generate_data():
    """居家老人体征：步数少，偶发心率过快或过慢SOS"""
    rnd = random.random()
    if rnd < 0.06:                           # 6% 心率过快
        hr = random.randint(135, 160)
    elif rnd < 0.10:                         # 4% 心率过慢
        hr = random.randint(28, 38)
    else:                                    # 正常范围
        hr = random.randint(55, 105)

    bad_env = random.random() < 0.45

    return {
        "user_id":     USER_ID,
        "heart_rate":  hr,
        "sleep_hours": round(random.uniform(4.0, 8.0), 1),
        "steps":       random.randint(200, 5500),   # 老人活动量较少
        "temperature": round(random.uniform(36.0, 37.3), 1),
        "room_temp":   round(random.uniform(29.0, 34.0) if bad_env else random.uniform(20.0, 26.0), 1),
        "humidity":    round(random.uniform(75.0, 90.0) if bad_env else random.uniform(40.0, 62.0), 1),
        "co2_level":   random.randint(1300, 2500) if bad_env else random.randint(400, 800),
    }

def run(interval=3):
    print(BANNER)
    count = 0
    while True:
        count += 1
        payload = generate_data()
        hr = payload["heart_rate"]

        if hr > 130:
            sos_flag = "  [!!! 心率过快 SOS !!!]"
        elif hr < 40:
            sos_flag = "  [!!! 心率过慢 SOS !!!]"
        else:
            sos_flag = ""

        try:
            resp = requests.post(URL, json=payload, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                sos_srv = "  << 服务端SOS触发·邮件发送 >>" if data.get("sos_alert") else ""
                print(f"[{count:04d}] OK  心率={hr:3d}bpm  "
                      f"睡眠={payload['sleep_hours']}h  "
                      f"步数={payload['steps']:>4d}  "
                      f"CO2={payload['co2_level']:>4d}ppm"
                      f"{sos_flag}{sos_srv}")
            else:
                print(f"[{count:04d}] ERR HTTP {resp.status_code}: {resp.text[:60]}")
        except requests.exceptions.ConnectionError:
            print(f"[{count:04d}] --- 无法连接服务器，等待重试...")
        except requests.exceptions.Timeout:
            print(f"[{count:04d}] --- 请求超时，跳过本次")
        except Exception as e:
            print(f"[{count:04d}] --- 异常: {e}")

        time.sleep(interval)

if __name__ == "__main__":
    try:
        run(interval=3)
    except KeyboardInterrupt:
        print("\n\n模拟已停止。")
    finally:
        print("\n按 Enter 键关闭窗口...", end="")
        input()
