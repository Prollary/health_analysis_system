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

        # 预取该用户所有报告（按时间升序），用于与传感器记录匹配最近的健康评分
        reports = HealthReport.query.filter_by(user_id=user_id)\
            .order_by(HealthReport.created_at.asc()).all()

        # 为每条传感器记录找离它最近（且不晚于它）的一条报告
        def nearest_report(sensor_ts):
            matched = None
            for rp in reports:
                if rp.created_at <= sensor_ts:
                    matched = rp
                else:
                    break
            return matched

        data = [
            {
                "timestamp":    r.timestamp.strftime('%m-%d %H:%M'),
                "heart_rate":   r.heart_rate,
                "sleep_hours":  r.sleep_hours,
                "steps":        r.steps,
                "temperature":  r.temperature,
                "room_temp":    r.room_temp,
                "humidity":     r.humidity,
                "co2_level":    r.co2_level,
                # 关联最近报告的评分字段
                "health_score": (lambda rp: rp.health_score if rp else None)(nearest_report(r.timestamp)),
                "risk_level":   (lambda rp: rp.risk_level   if rp else None)(nearest_report(r.timestamp)),
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
    """发送告警邮件"""
    from app import mail # 延迟导入避免循环依赖
    msg = Message("【紧急告警】智慧家居健康舱提醒",
                  recipients=[target_email])
    msg.body = f"尊敬的家属：\n系统检测到您的家庭成员 {member_name} 的健康指标出现异常！\n异常详情：{reason}\n请立即确认其安全状态或联系社区医生。"
    # 注意：在生产中建议使用异步发送，这里演示同步逻辑
    mail.send(msg)