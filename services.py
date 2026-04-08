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

def get_health_history(user_id, days=7):
    """获取历史数据"""
    try:
        start_time = datetime.now() - timedelta(days=days)
        records = SensorData.query.filter(
            SensorData.user_id == user_id,
            SensorData.timestamp >= start_time
        ).order_by(SensorData.timestamp.asc()).all()

        return {
            "status": "success",
            "data": {
                "times": [r.timestamp.strftime('%m-%d %H:%M') for r in records],
                "heart_rates": [r.heart_rate for r in records],
                "steps": [r.steps for r in records],
                "sleep_hours": [r.sleep_hours for r in records],
                "room_temps": [r.room_temp for r in records],
                "co2_levels": [r.co2_level for r in records]
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}



# 获取指定用户最近 X 天的健康数据
def get_health_history(user_id, days=7):
    try:
        # 1. 计算起始时间（当前时间减去 7 天）
        start_time = datetime.now() - timedelta(days=days)

        # 2. 从数据库查询数据
        # 筛选条件：用户ID匹配 且 时间大于等于起始时间
        # 排序：按时间从旧到新（以便折线图从左往右画）
        records = SensorData.query.filter(
            SensorData.user_id == user_id,
            SensorData.timestamp >= start_time
        ).order_by(SensorData.timestamp.asc()).all()

        # 3. 格式化数据以适配 ECharts
        times = [r.timestamp.strftime('%m-%d %H:%M') for r in records]
        heart_rates = [r.heart_rate for r in records]
        steps = [r.steps for r in records]
        sleep_hours = [r.sleep_hours for r in records]

        return {
            "status": "success",
            "data": {
                "times": times,
                "heart_rates": heart_rates,
                "steps": steps,
                "sleep_hours": sleep_hours
            }
        }
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