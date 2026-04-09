from models import db, SensorData
from datetime import datetime, timedelta

# 解析 JSON 数据并存入 SensorData 表
def save_sensor_data(data):
    try:
        new_record = SensorData(
            user_id=data['user_id'],
            heart_rate=data['heart_rate'],
            sleep_hours=data['sleep_hours'],
            steps=data['steps'],
            temperature=data.get('temperature', 36.5),
            room_temp=data.get('room_temp', 25.0),
            humidity=data.get('humidity', 50.0),
            co2_level=data.get('co2_level', 400)
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

        # 返回行对象数组，前端直接按字段名访问
        data = [
            {
                "timestamp":   r.timestamp.strftime('%m-%d %H:%M'),
                "heart_rate":  r.heart_rate,
                "sleep_hours": r.sleep_hours,
                "steps":       r.steps,
                "temperature": r.temperature,
                "room_temp":   r.room_temp,
                "humidity":    r.humidity,
                "co2_level":   r.co2_level,
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