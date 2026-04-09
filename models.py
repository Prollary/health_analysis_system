from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# 初始化数据库对象
db = SQLAlchemy()

# 1. 用户表 (User)
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, default=datetime.now)
    # role: 'admin' (子女/管理员), 'member' (老人/被监护人)
    role = db.Column(db.String(20), default='member') 
    email = db.Column(db.String(120)) # 用于接收告警的邮箱
    # 记录该成员所属的管理员 ID
    parent_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # 建立与数据和报告的关联关系
    sensor_data = db.relationship('SensorData', backref='user', lazy=True)
    reports = db.relationship('HealthReport', backref='user', lazy=True)
    # 建立自关联关系
    family_members = db.relationship('User', backref=db.backref('parent', remote_side=[id]))

# 2. 设备数据表 (SensorData)
class SensorData(db.Model):
    __tablename__ = 'sensor_data'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    heart_rate = db.Column(db.Integer)       # 心率
    sleep_hours = db.Column(db.Float)        # 睡眠时长
    steps = db.Column(db.Integer)            # 步数
    temperature = db.Column(db.Float)        # 体温
    room_temp = db.Column(db.Float)          # 卧室温度 (℃)
    humidity = db.Column(db.Float)           # 相对湿度 (%)
    co2_level = db.Column(db.Integer)        # CO2浓度 (ppm)
    
    timestamp = db.Column(db.DateTime, default=datetime.now)

# 3. 健康报告表 (HealthReport)
class HealthReport(db.Model):
    __tablename__ = 'health_reports'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    health_score = db.Column(db.Integer)     # AI 计算的健康分
    ai_suggestion = db.Column(db.Text)       # AI 给出的建议
    cloud_ai_report = db.Column(db.Text)   # 存储百度 AI 返回的深度建议
    risk_level = db.Column(db.String(20))    # 风险等级（低/中/高）
    created_at = db.Column(db.DateTime, default=datetime.now)