from models import db, SensorData, HealthReport
from datetime import datetime, timedelta

# 解析 JSON 数据并存入 SensorData 表
def save_sensor_data(data):
    try:
        new_record = SensorData(
            user_id=data['user_id'],
            heart_rate=data['heart_rate'],
            sleep_hours=data['sleep_hours'],
            steps=data['steps'],
            temperature=data.get('temperature') if data.get('temperature') is not None else 36.5,
            room_temp=data.get('room_temp') if data.get('room_temp') is not None else 25.0,
            humidity=data.get('humidity') if data.get('humidity') is not None else 50.0,
            co2_level=data.get('co2_level') if data.get('co2_level') is not None else 400
        )
        db.session.add(new_record)
        db.session.commit()
        return True, "入库成功"
    except Exception as e:
        db.session.rollback()
        return False, str(e)

# 获取指定用户最近 X 天的健康数据
def get_health_history(user_id, days=7):
    try:
        start_time = datetime.now() - timedelta(days=days)
        records = SensorData.query.filter(
            SensorData.user_id == user_id,
            SensorData.timestamp >= start_time
        ).order_by(SensorData.timestamp.asc()).all()

        # 取该用户最新一条报告，所有传感器记录共用同一份最新评分
        latest_report = HealthReport.query.filter_by(user_id=user_id)\
            .order_by(HealthReport.created_at.desc()).first()

        score      = latest_report.health_score  if latest_report else None
        risk       = latest_report.risk_level    if latest_report else None
        suggestion = latest_report.ai_suggestion if latest_report else None

        data = [
            {
                "timestamp":     r.timestamp.strftime('%m-%d %H:%M'),
                "heart_rate":    r.heart_rate,
                "sleep_hours":   r.sleep_hours,
                "steps":         r.steps,
                "temperature":   r.temperature,
                "room_temp":     r.room_temp,
                "humidity":      r.humidity,
                "co2_level":     r.co2_level,
                "health_score":  score,
                "risk_level":    risk,
                "ai_suggestion": suggestion,
            }
            for r in records
        ]

        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}



#校验
def validate_health_data(data):
    """
    健康数据合规性校验
    """
    # 校验字段是否存在
    required = ['heart_rate', 'sleep_hours', 'steps']
    for field in required:
        if field not in data:
            return False, f"缺少关键指标: {field}"
    
    # 校验数值范围（医学逻辑）
    hr = data['heart_rate']
    if not (30 <= hr <= 220):
        return False, f"异常心率值: {hr} (合理范围 30-220)"
    
    sleep = data['sleep_hours']
    if not (0 <= sleep <= 24):
        return False, "睡眠时间必须在 0 到 24 小时之间"
    
    steps = data['steps']
    if steps < 0:
        return False, "步数不能为负数"
        
    return True, "校验通过"



def check_sos_condition(user, data):
    """
    SOS 哨兵：检测是否存在生命体征危机
    """
    hr = data.get('heart_rate', 70)
    is_sos = False
    reason = ""

    # 1. 极端心率拦截 (强规则)
    if hr > 130:
        is_sos = True
        reason = f"危险：检测到心率过快 ({hr} bpm)！"
    elif hr < 40:
        is_sos = True
        reason = f"危险：检测到心率过低 ({hr} bpm)！"

    # 2. 如果触发 SOS 且用户有绑定的管理员
    if is_sos and user.parent and user.parent.email:
        send_sos_email(user.parent.email, user.username, reason)
        return True, reason
    
    return False, ""

def send_sos_email(target_email, member_name, reason):
    """异步发送告警邮件（后台线程，不阻塞 HTTP 响应）"""
    import threading
    from app import mail, app as flask_app
    from flask_mail import Message

    def _send():
        with flask_app.app_context():
            try:
                msg = Message("【紧急告警】智慧家居健康舱提醒",
                              recipients=[target_email])
                msg.body = (
                    f"尊敬的家属：\n"
                    f"系统检测到您的家庭成员 {member_name} 的健康指标出现异常！\n"
                    f"异常详情：{reason}\n"
                    f"请立即确认其安全状态或联系社区医生。"
                )
                mail.send(msg)
                flask_app.logger.info(f"SOS 邮件已发送至 {target_email}，原因：{reason}")
            except Exception as e:
                flask_app.logger.error(f"SOS 邮件发送失败 ({target_email}): {e}")

    threading.Thread(target=_send, daemon=True).start()