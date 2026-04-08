import numpy as np

def calculate_health_score(heart_rate, sleep_hours, steps, model):
    """
    输入实时数据，输出 AI 的诊断结果与健康分
    """
    # 1. 构造特征矩阵
    features = np.array([[heart_rate, sleep_hours, steps]])

    # 2. 获取 AI 的预测分类 (0: 健康, 1: 亚健康, 2: 高风险)
    predicted_class = model.predict(features)[0]

    # 3. 获取 AI 的预测概率矩阵
    probabilities = model.predict_proba(features)[0]
    p_health = probabilities[0]
    p_sub_health = probabilities[1]
    p_risk = probabilities[2]

    # 4. 计算连续的健康分 (HealthScore)
    health_score = (p_health * 100) + (p_sub_health * 60) + (p_risk * 20)

    # 5. 根据结果生成建议
    if predicted_class == 0:
        risk_level = "低风险"
        suggestion = "状态极佳！各项体征平稳，请继续保持规律作息与充足的运动。"
    elif predicted_class == 1:
        risk_level = "中风险"
        suggestion = "处于亚健康状态。可能近期睡眠不足或缺乏运动，建议适当调整作息。"
    else:
        risk_level = "高风险"
        suggestion = "健康风险较高！体征存在明显异常，请结合自身感受注意休息，必要时就医。"

    # 6. 返回结构化的诊断报告
    return {
        "health_score": round(health_score, 1), # 保留一位小数，如 85.2
        "risk_level": risk_level,
        "suggestion": suggestion,
        "details": {
            "p_healthy": round(p_health * 100, 1),
            "p_sub_health": round(p_sub_health * 100, 1),
            "p_risk": round(p_risk * 100, 1)
        }
    }