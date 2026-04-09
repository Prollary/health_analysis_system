import numpy as np
import pandas as pd
import joblib


def calculate_health_score(heart_rate, sleep_hours, steps, room_temp, humidity, co2_level, model):
    """
    输入实时数据，输出 AI 的诊断结果与健康分
    """
    # 构造特征矩阵
    features = pd.DataFrame([{
        'heart_rate': heart_rate,
        'sleep_hours': sleep_hours,
        'steps': steps,
        'room_temp': room_temp,
        'humidity': humidity,
        'co2_level': co2_level
    }])

    # 获取 AI 的预测分类 (0: 健康, 1: 亚健康, 2: 高风险)
    predicted_class = model.predict(features)[0]

    # 获取 AI 的预测概率矩阵
    probabilities = model.predict_proba(features)[0]
    p_health = probabilities[0]
    p_sub_health = probabilities[1]
    p_risk = probabilities[2]

    # 计算连续的健康分 (HealthScore)
    health_score = (p_health * 100) + (p_sub_health * 60) + (p_risk * 20)

    # 根据结果生成建议
    if predicted_class == 0:
        risk_level = "低风险"
        suggestion = "状态极佳！各项体征平稳，请继续保持规律作息与充足的运动。"
    elif predicted_class == 1:
        risk_level = "中风险"
        suggestion = "处于亚健康状态。可能近期睡眠不足或缺乏运动，建议适当调整作息。"
    else:
        risk_level = "高风险"
        suggestion = "健康风险较高！体征存在明显异常，请结合自身感受注意休息，必要时就医。"

    # 调用联动分析引擎
    linkage_analysis = analyze_env_linkage(sleep_hours, steps, room_temp, humidity, co2_level)

    # 返回结构化的诊断报告
    return {
        "health_score": round(health_score, 1), 
        "risk_level": risk_level,
        "suggestion": suggestion,  # 机器学习得出的宏观健康建议
        "linkage_analysis": linkage_analysis, 
        "details": {
            "p_healthy": round(p_health * 100, 1),
            "p_sub_health": round(p_sub_health * 100, 1),
            "p_risk": round(p_risk * 100, 1)
        }
    }

def analyze_environment_linkage(temp, humidity, co2, steps, sleep_hours):
    """
    环境与生理数据的联动诊断引擎
    """
    alerts = []
    recommendations = []

    # 联动场景 1：久坐与室内空气联动预警
    # 逻辑：近期步数极少（<500步） 且 CO2 浓度偏高（>1000ppm）
    if steps < 500 and co2 > 1000:
        alerts.append({
            "type": "fatigue_risk",
            "level": "warning",
            "message": f"🚨 疲劳风险预警：检测到您当前处于久坐状态，且室内CO2浓度偏高({co2}ppm)。"
        })
        recommendations.append("建议立即开窗通风，并起身活动5-10分钟，以防大脑缺氧导致的头晕疲劳。")

    # 联动场景 2：环境-睡眠关联分析
    # 逻辑：室温高于26度，且睡眠时长低于健康标准（<7小时）
    if temp > 26.0 and sleep_hours < 7.0:
        alerts.append({
            "type": "sleep_environment",
            "level": "info",
            "message": f"💡 睡眠环境提醒：昨晚卧室温度较高({temp}℃)，您的深度睡眠时长受到明显影响。"
        })
        recommendations.append("AI 建议：今晚入睡前将空调设定为 24℃-26℃ 睡眠模式，并保持相对湿度在 50% 左右。")

    return {
        "has_alert": len(alerts) > 0,
        "alerts": alerts,
        "recommendations": recommendations
    }

# ai_service.py

def analyze_env_linkage(sleep_hours, steps, room_temp, humidity, co2_level):
    """
    生理数据与家居环境的联动分析引擎
    """
    suggestions = []
    alerts = [] # 用于标记需要强制弹窗的严重预警

    # 1. 睡眠与温度联动分析
    if sleep_hours < 6.5:
        if room_temp > 26.0:
            suggestions.append("🌡️ 【环境-睡眠联动】检测到室温偏高（>26℃）且您处于睡眠不足状态。建议今晚开启空调睡眠模式（24-26℃），有助于延长深度睡眠。")
        elif room_temp < 18.0:
            suggestions.append("❄️ 【环境-睡眠联动】检测到室温偏低（<18℃），易导致肌肉紧绷和频繁起夜。建议适当开启暖气或增加被褥。")

    # 2. 久坐与室内空气联动预警
    # 设定：步数极少代表处于静坐/办公状态，此时高CO2极易引发疲劳
    if steps < 500 and co2_level > 1000:
        alert_msg = f"⚠️ 【久坐缺氧预警】您近期活动量极少，且室内CO2浓度高达 {co2_level}ppm！极易引发大脑缺氧、头晕和疲劳，请立即开窗通风并起身活动！"
        suggestions.append(alert_msg)
        alerts.append("high_co2_sedentary")
    
    # 3. 湿度与体感舒适度
    if humidity > 70.0:
        suggestions.append("💧 【环境舒适度】室内湿度过高，易滋生霉菌并加重体感闷热，建议开启抽湿设备。")

    # 如果没有触发任何警报，给一个基础安抚
    if not suggestions:
        suggestions.append("🌱 当前家居环境适宜，各项生理指标与环境处于良好平衡状态。")

    return {
        "env_suggestions": suggestions,
        "active_alerts": alerts
    }