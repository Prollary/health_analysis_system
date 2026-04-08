from models import db, SensorData
from datetime import datetime

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