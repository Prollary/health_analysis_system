from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# 初始化数据库对象
db = SQLAlchemy()

# 1. 用户表 (User)
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
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
    # 加密密码（哈希）
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    # 校验密码
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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

# 4. 智能镜子面部情绪表 (FaceAnalysis)
class FaceAnalysis(db.Model):
    __tablename__ = 'face_analysis'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    emotion = db.Column(db.String(50))           # 识别出的情绪 (如：高兴、悲伤、愤怒、平静)
    fatigue_index = db.Column(db.Float)          # 疲劳指数 (根据情绪和生理指标综合计算)
    comprehensive_report = db.Column(db.Text)    # 结合血压/心率生成的身心综合报告
    timestamp = db.Column(db.DateTime, default=datetime.now)

# 5. 健康日记表 (HealthDiary)
class HealthDiary(db.Model):
    __tablename__ = 'health_diaries'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    raw_content = db.Column(db.Text, nullable=False)       # 老人输入的大白话原文本
    extracted_symptoms = db.Column(db.String(255))         # AI 提取的症状实体 (如：头晕, 胸闷)
    ai_advice = db.Column(db.Text)                         # AI 给出的就医建议
    timestamp = db.Column(db.DateTime, default=datetime.now)