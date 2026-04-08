from models import db, SensorData
from datetime import datetime, timedelta

def save_sensor_data(data):
    """
    解析 JSON 数据并存入 SensorData 表
    :param data: 字典格式的传感器数据
    :return: (bool, message)
    """
    try:
        # 1. 数据校验（确保必要字段存在）
        required_fields = ['user_id', 'heart_rate', 'sleep_hours', 'steps']
        for field in required_fields:
            if field not in data:
                return False, f"缺少必要字段: {field}"

        # 2. 构造数据库模型对象
        new_record = SensorData(
            user_id=data['user_id'],
            heart_rate=data['heart_rate'],
            sleep_hours=data['sleep_hours'],
            steps=data['steps'],
            temperature=data.get('temperature', 36.5), # 使用 .get 处理可选字段
            timestamp=datetime.now()
        )

        # 3. 执行入库
        db.session.add(new_record)
        db.session.commit()
        
        return True, "数据入库成功"

    except Exception as e:
        # 如果出错，回滚数据库会话
        db.session.rollback()
        return False, f"数据库写入失败: {str(e)}"



def get_health_history(user_id, days=7):
    """
    获取指定用户最近 X 天的健康数据
    """
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