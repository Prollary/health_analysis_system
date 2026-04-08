import qianfan
import os

def get_cloud_ai_advice(heart_rate, sleep, steps, room_temp, co2):
    """
    调用百度文心一言获取深度分析
    """
    # 自动读取环境变量 QIANFAN_AK 和 QIANFAN_SK
    chat_comp = qianfan.ChatCompletion()
    
    prompt = f"""
    你是智慧家居健康助手。请分析以下数据并给出100字以内的建议：
    1. 生理：心率{heart_rate}bpm, 睡眠{sleep}h, 步数{steps}。
    2. 环境：室温{room_temp}℃, CO2浓度{co2}ppm。
    请结合环境对生理的影响（如高CO2对疲劳的影响）给出专业指导。
    """
    
    try:
        resp = chat_comp.do(model="ERNIE-Speed-128K", messages=[{"role": "user", "content": prompt}])
        return resp.body['result']
    except Exception as e:
        return f"云端诊断服务暂时不可用 ({str(e)})"