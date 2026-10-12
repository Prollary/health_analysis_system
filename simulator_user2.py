# -*- coding: utf-8 -*-
"""
模拟传感器 - 用户 ID=2（成年用户 / 管理员）
双击此文件即可运行，数据发送至本机 Flask 后端
"""
import requests
import time
import random
import sys

URL    = "http://127.0.0.1:5000/api/sensor/upload"
USER_ID = 2
NAME   = "用户2（管理员）"

BANNER = f"""
╔══════════════════════════════════════════════╗
║      HealthAI 智慧舱 · 模拟传感器             ║
║      目标用户：{NAME:<24}  ║
║      发送地址：{URL:<24}  ║
╚══════════════════════════════════════════════╝
  按 Ctrl+C 停止模拟
"""

def generate_data():
    """成年用户体征：心率正常，偶发SOS（>130）"""
    sos_trigger = random.random() < 0.08          # 8% 概率触发心率过快
    bad_env     = random.random() < 0.4           # 40% 概率环境较差

    hr = random.randint(135, 155) if sos_trigger else random.randint(62, 105)

    return {
        "user_id":     USER_ID,
        "heart_rate":  hr,
        "sleep_hours": round(random.uniform(5.0, 8.5), 1),
        "steps":       random.randint(1500, 12000),
        "temperature": round(random.uniform(36.2, 37.1), 1),
        "room_temp":   round(random.uniform(29.0, 33.0) if bad_env else random.uniform(20.0, 26.0), 1),
        "humidity":    round(random.uniform(75.0, 88.0) if bad_env else random.uniform(40.0, 60.0), 1),
        "co2_level":   random.randint(1200, 2200) if bad_env else random.randint(400, 750),
    }

def run(interval=3):
    print(BANNER)
    count = 0
    while True:
        count += 1
        payload = generate_data()
        hr = payload["heart_rate"]
        sos_flag = "  [!!! SOS !!!]" if hr > 130 or hr < 40 else ""

        try:
            resp = requests.post(URL, json=payload, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                sos_srv = "  << 服务端SOS触发 >>" if data.get("sos_alert") else ""
                print(f"[{count:04d}] OK  心率={hr:3d}bpm  "
                      f"睡眠={payload['sleep_hours']}h  "
                      f"步数={payload['steps']:>5d}  "
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
