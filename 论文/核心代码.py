# =============================================================================
#  《基于Flask与AI技术的智慧家居健康分析系统设计与实现》
#  核心代码汇编 —— 供第四章"系统实现"部分截图使用
#
#  文件结构（按论文章节顺序排列）：
#    模块一  Flask 应用初始化与 SPA 路由 .............. 第四章 4.1 §用户认证模块
#    模块二  JWT 用户注册与登录接口 ................... 第四章 4.1 §用户认证模块
#    模块三  数据模型 ORM 设计（User 树形自关联）....... 第四章 4.1 §体征上报模块
#    模块四  数据入库、字段校验与 SOS 预警 ............. 第四章 4.1 §体征上报模块
#    模块五  nearest_report 跨表时间对齐算法 .......... 第四章 4.1 §体征上报模块
#    模块六  本地随机森林健康评分 ...................... 第四章 4.1 §AI健康评分模块
#    模块七  环境关联分析（None 容错处理） ............. 第四章 4.1 §环境监测模块
#    模块八  DeepSeek API 统一调用封装 ................ 第四章 4.1 §AI深度报告模块
#    模块九  深度干预方案提示词工程 ................... 第四章 4.1 §AI深度报告模块
#    模块十  自然语言健康日记解析 ..................... 第四章 4.1 §健康日记模块
#    模块十一 智能镜情绪分析与降级容错 ................. 第四章 4.1 §智能镜模块
#    模块十二 PDF 健康周报生成（数据汇总+渲染） ........ 第四章 4.1 §PDF导出模块
#    模块十三 桌面应用启动器（Flask线程+pywebview窗口）.. 第四章 4.1 §桌面打包模块
# =============================================================================


# ─────────────────────────────────────────────────────────────────────────────
# 模块一  Flask 应用初始化与 Vue SPA 路由
# 来源文件：app.py
# 实现思路：
#   1. resource_path() 适配 PyInstaller 打包后 _MEIPASS 临时目录路径，
#      确保 static/dist 与 templates 在 exe 运行时也能被正确定位。
#   2. Flask 以 static/dist 作为静态文件根目录，static_url_path='' 使
#      前端构建产物可直接通过根路径访问，无需 /static/dist 前缀。
#   3. catch-all 路由拦截所有非 /api 请求，将 Vue Router 的 HTML5
#      History 模式路径全部重定向至 index.html，实现前后端路由共存。
# ─────────────────────────────────────────────────────────────────────────────
import os, sys
from flask import Flask, send_from_directory

def resource_path(relative):
    """兼容开发环境与 PyInstaller 打包环境的资源路径解析"""
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)

app = Flask(
    __name__,
    static_folder=resource_path('static/dist'),   # Vue 构建产物目录
    static_url_path='',                            # 映射到根路径
    template_folder=resource_path('templates'),
)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
    """Vue SPA catch-all 路由：静态文件直接返回，其余均返回 index.html"""
    dist_dir = resource_path('static/dist')
    file_path = os.path.join(dist_dir, path)
    if path and os.path.isfile(file_path):
        return send_from_directory(dist_dir, path)
    return send_from_directory(dist_dir, 'index.html')


# ─────────────────────────────────────────────────────────────────────────────
# 模块二  JWT 用户注册与登录接口
# 来源文件：app.py
# 实现思路：
#   1. 注册接口对 username 唯一性做数据库级校验，密码以
#      generate_password_hash(PBKDF2-SHA256) 哈希存储，杜绝明文泄露。
#   2. 登录接口使用 check_password_hash 验证后，通过 create_access_token
#      签发含 user_id 的 JWT，有效期 7 天，前端存入 localStorage。
#   3. 受保护路由统一使用 @jwt_required() 装饰器鉴权，身份通过
#      get_jwt_identity() 从令牌 payload 中解析，无需查询 Session。
# ─────────────────────────────────────────────────────────────────────────────
from flask import request, jsonify
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)
from werkzeug.security import generate_password_hash, check_password_hash

# POST /api/auth/register
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({"code": 400, "msg": "用户名和密码不能为空"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"code": 409, "msg": "用户名已存在"}), 409
    new_user = User(
        username=username,
        password_hash=generate_password_hash(password),
        role=data.get('role', 'member')
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"code": 200, "msg": "注册成功"})

# POST /api/auth/login
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data.get('username')).first()
    if not user or not check_password_hash(user.password_hash, data.get('password', '')):
        return jsonify({"code": 401, "msg": "用户名或密码错误"}), 401
    token = create_access_token(identity=str(user.id))   # JWT payload 含 user_id
    return jsonify({"code": 200, "token": token, "user_id": user.id, "role": user.role})

# 受保护路由示例
@jwt_required()
def health_history_api():
    current_user_id = int(get_jwt_identity())   # 从 Token 解析身份，无需 Session
    result = get_health_history(user_id=current_user_id, days=7)
    return jsonify(result["data"]) if result["status"] == "success" \
        else jsonify({"error": result["message"]}), 500


# ─────────────────────────────────────────────────────────────────────────────
# 模块三  数据模型 ORM 设计（User 树形自关联）
# 来源文件：models.py
# 实现思路：
#   1. User.parent_id 通过自外键 ForeignKey('users.id') 实现树形家庭结构：
#      管理员（admin）parent_id=NULL，成员（member）指向管理员 id。
#   2. family_members relationship 利用 remote_side=[id] 声明自关联方向，
#      ORM 自动处理递归查询，admin.family_members 即返回其所有子成员。
#   3. SensorData 表合并存储体征与环境字段，环境字段设 nullable=True，
#      兼容未部署室内传感器的用户，避免非空约束导致数据上报失败。
# ─────────────────────────────────────────────────────────────────────────────
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    age           = db.Column(db.Integer)
    gender        = db.Column(db.String(10))
    role          = db.Column(db.String(20), default='member')  # admin / member
    email         = db.Column(db.String(120))                   # 接收 SOS 告警
    created_at    = db.Column(db.DateTime, default=datetime.now)
    # 自外键：实现管理员→成员的家庭树形结构
    parent_id     = db.Column(db.Integer, db.ForeignKey('users.id'))
    family_members = db.relationship(
        'User', backref=db.backref('parent', remote_side=[id])
    )

class SensorData(db.Model):
    __tablename__ = 'sensor_data'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    heart_rate  = db.Column(db.Integer)    # 心率 (bpm)
    sleep_hours = db.Column(db.Float)      # 睡眠时长 (h)
    steps       = db.Column(db.Integer)    # 步数
    temperature = db.Column(db.Float)      # 体温 (℃)
    room_temp   = db.Column(db.Float)      # 室温 (℃)  — 可为 NULL
    humidity    = db.Column(db.Float)      # 相对湿度 (%) — 可为 NULL
    co2_level   = db.Column(db.Integer)    # CO₂浓度 (ppm) — 可为 NULL
    timestamp   = db.Column(db.DateTime, default=datetime.now)


# ─────────────────────────────────────────────────────────────────────────────
# 模块四  数据入库、字段校验与 SOS 心率预警
# 来源文件：services.py
# 实现思路：
#   1. validate_health_data 在数据入库前对三个必填字段做医学范围校验，
#      不合规数据直接拒绝，错误信息精确到字段级别，方便前端回显。
#   2. save_sensor_data 使用 db.session.rollback() 在异常时回滚事务，
#      保证数据库一致性。
#   3. check_sos_condition 在每次数据写入后实时判断心率阈值（>130 或
#      <40 bpm），满足条件时调用 send_sos_email 向家属发送 HTML 告警邮件，
#      利用 user.parent.email 树形关联自动定位告警接收人。
# ─────────────────────────────────────────────────────────────────────────────

def validate_health_data(data):
    """健康数据医学范围校验，返回 (is_valid: bool, message: str)"""
    required = ['heart_rate', 'sleep_hours', 'steps']
    for field in required:
        if field not in data:
            return False, f"缺少关键指标: {field}"
    if not (30 <= data['heart_rate'] <= 220):
        return False, f"异常心率值: {data['heart_rate']} bpm（合理范围 30-220）"
    if not (0 <= data['sleep_hours'] <= 24):
        return False, "睡眠时间须在 0 到 24 小时之间"
    if data['steps'] < 0:
        return False, "步数不能为负数"
    return True, "校验通过"

def save_sensor_data(data):
    """将上报的体征/环境数据写入 SensorData 表"""
    try:
        record = SensorData(
            user_id     = data['user_id'],
            heart_rate  = data['heart_rate'],
            sleep_hours = data['sleep_hours'],
            steps       = data['steps'],
            temperature = data.get('temperature', 36.5),
            room_temp   = data.get('room_temp'),    # 允许为 NULL
            humidity    = data.get('humidity'),
            co2_level   = data.get('co2_level'),
        )
        db.session.add(record)
        db.session.commit()
        return True, "入库成功"
    except Exception as e:
        db.session.rollback()
        return False, str(e)

def check_sos_condition(user, data):
    """SOS 哨兵：极端心率触发时向家属发送告警邮件"""
    hr = data.get('heart_rate', 70)
    if hr > 130:
        reason = f"危险：检测到心率过快（{hr} bpm）！"
    elif hr < 40:
        reason = f"危险：检测到心率过低（{hr} bpm）！"
    else:
        return False, ""
    # 通过树形关联获取管理员邮箱
    if user.parent and user.parent.email:
        send_sos_email(user.parent.email, user.username, reason)
    return True, reason

def send_sos_email(target_email, member_name, reason):
    """通过 Flask-Mail 发送 SOS 告警邮件"""
    from app import mail
    from flask_mail import Message
    msg = Message(
        subject="【紧急告警】智慧家居健康舱提醒",
        recipients=[target_email]
    )
    msg.body = (
        f"尊敬的家属：\n"
        f"系统检测到您的家庭成员 {member_name} 的健康指标出现异常！\n"
        f"异常详情：{reason}\n"
        f"请立即确认其安全状态或联系社区医生。"
    )
    mail.send(msg)


# ─────────────────────────────────────────────────────────────────────────────
# 模块五  nearest_report 跨表时间对齐算法
# 来源文件：services.py → get_health_history()
# 实现思路：
#   SensorData 与 HealthReport 不存在直接外键关联，但前端需要在每条体征
#   记录旁展示对应的健康评分。nearest_report() 以升序遍历 HealthReport，
#   为每条传感器记录找到时间戳不晚于它的最近一条报告，实现跨表"软关联"。
#   此算法时间复杂度 O(N×M)，在 7 天数据量级下性能完全满足要求。
# ─────────────────────────────────────────────────────────────────────────────

def get_health_history(user_id, days=7):
    from datetime import datetime, timedelta
    start_time = datetime.now() - timedelta(days=days)

    # 查询指定时间范围内的传感器记录
    records = SensorData.query.filter(
        SensorData.user_id == user_id,
        SensorData.timestamp >= start_time
    ).order_by(SensorData.timestamp.asc()).all()

    # 预取该用户全部健康报告（升序），用于 nearest_report 匹配
    reports = HealthReport.query.filter_by(user_id=user_id) \
        .order_by(HealthReport.created_at.asc()).all()

    def nearest_report(sensor_ts):
        """返回时间戳 ≤ sensor_ts 的最近一条 HealthReport，无则返回 None"""
        matched = None
        for rp in reports:
            if rp.created_at <= sensor_ts:
                matched = rp
            else:
                break       # 已升序排列，后续均大于 sensor_ts，可提前退出
        return matched

    # 构造行对象列表，附带关联评分
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
            "health_score": (lambda rp: rp.health_score if rp else None)(nearest_report(r.timestamp)),
            "risk_level":   (lambda rp: rp.risk_level   if rp else None)(nearest_report(r.timestamp)),
        }
        for r in records
    ]
    return {"status": "success", "data": data}


# ─────────────────────────────────────────────────────────────────────────────
# 模块六  本地随机森林健康评分
# 来源文件：ai_service.py → calculate_health_score()
# 实现思路：
#   1. 以 pandas DataFrame 构造特征矩阵，与训练时的特征顺序保持一致。
#   2. model.predict_proba() 返回三类（健康/亚健康/高风险）的概率分布，
#      加权求和得到连续健康分：健康概率×100 + 亚健康×60 + 高风险×20。
#   3. 健康分反映"健康程度"而非分类标签，使前端 KPI 展示更直观平滑。
# ─────────────────────────────────────────────────────────────────────────────
import pandas as pd

def calculate_health_score(heart_rate, sleep_hours, steps,
                           room_temp, humidity, co2_level, model):
    """本地随机森林推理：返回健康评分、风险等级与环境关联建议"""
    features = pd.DataFrame([{
        'heart_rate':  heart_rate,
        'sleep_hours': sleep_hours,
        'steps':       steps,
        'room_temp':   room_temp,
        'humidity':    humidity,
        'co2_level':   co2_level,
    }])

    predicted_class = model.predict(features)[0]         # 0:健康 1:亚健康 2:高风险
    proba = model.predict_proba(features)[0]             # 三类概率向量

    # 加权健康分：越接近 100 越健康
    health_score = proba[0] * 100 + proba[1] * 60 + proba[2] * 20

    risk_map = {0: "低风险", 1: "中风险", 2: "高风险"}
    suggestion_map = {
        0: "状态极佳！请继续保持规律作息与充足运动。",
        1: "处于亚健康状态，建议适当调整作息，增加有氧运动。",
        2: "健康风险较高！体征存在明显异常，请注意休息，必要时就医。",
    }
    return {
        "health_score": round(health_score, 1),
        "risk_level":   risk_map[predicted_class],
        "suggestion":   suggestion_map[predicted_class],
        "details": {
            "p_healthy":    round(proba[0] * 100, 1),
            "p_sub_health": round(proba[1] * 100, 1),
            "p_risk":       round(proba[2] * 100, 1),
        }
    }


# ─────────────────────────────────────────────────────────────────────────────
# 模块七  环境关联分析（None 容错处理）
# 来源文件：ai_service.py → analyze_env_linkage()
# 实现思路：
#   历史数据库记录中环境字段可能为 NULL（早期未部署传感器），直接参与
#   数值比较会抛出 "NoneType > float" TypeError。在函数入口用 if x is not
#   None else default 统一替换，保证后续逻辑的安全执行。
#   规则引擎按 GB/T 18883-2022 阈值分三类场景输出建议文本。
# ─────────────────────────────────────────────────────────────────────────────

def analyze_env_linkage(sleep_hours, steps, room_temp, humidity, co2_level):
    """环境-生理联动分析：所有入参做 None 安全默认值替换"""
    # None 容错：防止历史数据缺失字段导致 NoneType 比较崩溃
    sleep_hours = sleep_hours if sleep_hours is not None else 7.0
    steps       = steps       if steps       is not None else 5000
    room_temp   = room_temp   if room_temp   is not None else 22.0
    humidity    = humidity    if humidity    is not None else 50.0
    co2_level   = co2_level   if co2_level   is not None else 500

    suggestions = []

    # 规则1：睡眠不足 + 室温异常 → 睡眠环境建议
    if sleep_hours < 6.5:
        if room_temp > 26.0:
            suggestions.append(
                "【环境-睡眠联动】室温偏高（>26℃）且睡眠不足，"
                "建议今晚开启空调睡眠模式（24-26℃）。"
            )
        elif room_temp < 18.0:
            suggestions.append(
                "【环境-睡眠联动】室温偏低（<18℃），易导致频繁起夜，"
                "建议适当开启暖气。"
            )

    # 规则2：久坐 + CO₂ 偏高 → 缺氧预警（GB/T 18883 阈值 1000 ppm）
    if steps < 500 and co2_level > 1000:
        suggestions.append(
            f"【久坐缺氧预警】活动量极少且室内 CO₂ 高达 {co2_level} ppm，"
            "极易引发头晕疲劳，请立即开窗通风并起身活动！"
        )

    # 规则3：湿度过高 → 除湿建议
    if humidity > 70.0:
        suggestions.append("【湿度过高】室内湿度>70%，易滋生霉菌，建议开启除湿设备。")

    if not suggestions:
        suggestions.append("当前家居环境适宜，各项指标处于良好平衡状态。")

    return {"env_suggestions": suggestions}


# ─────────────────────────────────────────────────────────────────────────────
# 模块八  DeepSeek API 统一调用封装
# 来源文件：cloud_ai_service.py
# 实现思路：
#   使用 OpenAI SDK 的兼容接口接入 DeepSeek，仅需替换 base_url。
#   _client() 每次调用时实例化客户端，api_key 通过 dotenv 环境变量注入，
#   不在代码中硬编码。_chat() 作为统一出口，接收 messages 列表与可选
#   kwargs（如 max_tokens、response_format），屏蔽底层 SDK 细节。
# ─────────────────────────────────────────────────────────────────────────────
import os, json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def _client():
    """创建 DeepSeek 兼容 OpenAI 客户端（api_key 从 .env 读取）"""
    return OpenAI(
        api_key=os.getenv('DEEPSEEK_API_KEY'),
        base_url='https://api.deepseek.com'
    )

def _chat(messages, model='deepseek-chat', **kwargs):
    """统一 Chat Completion 调用出口，返回文本内容字符串"""
    resp = _client().chat.completions.create(
        model=model,
        messages=messages,
        **kwargs
    )
    return resp.choices[0].message.content


# ─────────────────────────────────────────────────────────────────────────────
# 模块九  深度干预方案提示词工程
# 来源文件：cloud_ai_service.py → generate_detailed_intervention()
# 实现思路：
#   提示词采用"角色设定 + 用户画像注入 + 结构化输出要求"三段式设计：
#   - 角色：资深临床营养师和运动康复专家
#   - 上下文：年龄/性别/风险等级/近期体征指标
#   - 输出约束：两大 Markdown 节（饮食推荐 ≥500字 + 运动处方 ≥500字）
#   max_tokens=4096 确保大模型不因 token 限制截断输出。
# ─────────────────────────────────────────────────────────────────────────────

def generate_detailed_intervention(user_profile, analysis_data):
    """根据用户画像生成 1000+ 字个性化健康干预方案"""
    age    = user_profile.get('age', '未知')
    gender = user_profile.get('gender', '未知')
    risk   = analysis_data.get('risk_level', '中风险')
    hr     = analysis_data.get('heart_rate', '--')
    sleep  = analysis_data.get('sleep', '--')
    steps  = analysis_data.get('steps', '--')

    prompt = f"""你是一位资深的临床营养师和运动康复专家。请为以下用户定制详尽的【健康干预方案】。

用户画像：年龄 {age} 岁，性别 {gender}，健康风险等级：{risk}。
最新指标：心率 {hr} bpm，睡眠 {sleep} h，步数 {steps} 步。

## 【个性化饮食推荐】
- 结合用户年龄、性别、风险等级给出具体食物清单
- 每种食物说明：为什么要吃、怎么吃、含哪些核心营养素
- 字数不少于 500 中文字符

## 【定制化运动处方】
- 结合体征数据推荐适合的运动类型
- 每种运动说明：为什么做、怎么做、具体时长与强度、对身体的好处
- 字数不少于 500 中文字符

语气专业且富有亲和力，使用 Markdown 结构化排版。"""

    try:
        return _chat([{"role": "user", "content": prompt}], max_tokens=4096)
    except Exception as e:
        return f"干预方案生成失败: {e}"


# ─────────────────────────────────────────────────────────────────────────────
# 模块十  自然语言健康日记 NLP 解析
# 来源文件：cloud_ai_service.py → parse_health_diary()
# 实现思路：
#   1. 提示词要求模型严格返回 JSON 格式，通过 response_format=json_object
#      开启 DeepSeek 的 JSON Mode，降低格式错误概率。
#   2. 双重容错：先尝试直接 json.loads，失败后清洗 markdown 代码块再解析，
#      最终兜底返回固定结构，保证接口永远不返回 500。
# ─────────────────────────────────────────────────────────────────────────────

def parse_health_diary(diary_text):
    """将老人口语化日记解析为结构化 JSON（症状 + 就医建议）"""
    prompt = f"""你是一位专业全科医生。请分析以下老年人健康日记：
"{diary_text}"

任务：
1. 提取【症状实体】（若无异常则输出"无异常"）
2. 给出【家庭就医建议】

严格按以下 JSON 格式返回，不含其他字符：
{{"symptoms": "症状A, 症状B", "advice": "建议内容..."}}"""

    try:
        result_str = _chat(
            [{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}   # DeepSeek JSON Mode
        )
        return json.loads(result_str)
    except json.JSONDecodeError:
        # 容错：清洗 markdown 代码块后重试
        try:
            clean = result_str.replace('```json', '').replace('```', '').strip()
            return json.loads(clean)
        except Exception:
            return {"symptoms": "解析失败", "advice": "请重新提交日记内容"}
    except Exception as e:
        return {"symptoms": "解析失败", "advice": f"AI 服务异常: {e}"}


# ─────────────────────────────────────────────────────────────────────────────
# 模块十一  智能镜情绪分析与降级容错
# 来源文件：app.py → smart_mirror_analyze()
# 实现思路：
#   1. 前端以 Base64 编码上传人脸图像，接口剥离 data:image/jpeg;base64, 头部。
#   2. 优先调用 DeepSeek 视觉接口识别情绪；若失败（标准模型不支持图像输入），
#      自动降级为"时段+体征"规则推理，保证功能可用性。
#   3. 疲劳指数融合情绪（负面情绪+40）、心率（>90 bpm+30）、睡眠
#      （<6h+30）三维数据，综合评分驱动三档身心状态报告输出。
# ─────────────────────────────────────────────────────────────────────────────
import datetime as dt

def smart_mirror_analyze_logic(user_id, base64_image):
    """智能镜情绪分析核心逻辑（含降级容错）"""
    # 去除 Base64 数据 URI 头部
    if "," in base64_image:
        base64_image = base64_image.split(",")[1]

    # 尝试 DeepSeek 视觉分析
    face_res = analyze_face_emotion(base64_image)
    if face_res["status"] == "success":
        emotion = face_res["emotion"]
    else:
        # 降级：根据时段给出默认情绪，不中断流程
        hour = dt.datetime.now().hour
        emotion = "平静" if 8 <= hour <= 22 else "疲惫"

    # 获取最新生理数据，计算多模态疲劳指数
    latest = SensorData.query.filter_by(user_id=user_id) \
        .order_by(SensorData.timestamp.desc()).first()

    fatigue_index = 0
    if emotion in ["悲伤", "愤怒", "厌恶", "疲惫", "恐惧"]:
        fatigue_index += 40                                   # 负面情绪贡献
    if latest and latest.heart_rate and latest.heart_rate > 90:
        fatigue_index += 30                                   # 心率偏高贡献
    if latest and latest.sleep_hours and latest.sleep_hours < 6:
        fatigue_index += 30                                   # 睡眠不足贡献

    # 三档综合报告生成
    if fatigue_index >= 70:
        advice = "高压/深度疲劳状态，建议立即放下工作进行深呼吸放松。"
    elif fatigue_index >= 40:
        advice = "轻中度疲劳，建议适当休息，补充水分。"
    else:
        advice = "身心状态良好，继续保持规律作息。"

    report = f"面部情绪：{emotion}，疲劳指数 {fatigue_index}/100。{advice}"
    return {"emotion": emotion, "fatigue_index": fatigue_index, "report": report}


# ─────────────────────────────────────────────────────────────────────────────
# 模块十二  PDF 健康周报生成（数据汇总 + WeasyPrint 渲染）
# 来源文件：app.py → download_pdf()  /  pdf_service.py
# 实现思路：
#   1. 查询近 7 天 SensorData，计算平均心率/睡眠/步数作为 summary 统计摘要。
#   2. 取最新 HealthReport 的 cloud_ai_report 作为 AI 建议正文。
#   3. pdf_service.export_health_report_pdf 将数据传入 Jinja2 模板渲染为
#      HTML 字符串，再由 WeasyPrint HTML().write_pdf() 转换为 PDF 二进制。
#   4. 以 attachment 响应头返回，触发浏览器下载行为。
# ─────────────────────────────────────────────────────────────────────────────
from weasyprint import HTML
from flask import render_template

def export_health_report_pdf(user_name, history_data, ai_report, output_path, summary=None):
    """将健康周报数据渲染为 HTML 并通过 WeasyPrint 导出 PDF"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    html_content = render_template(
        'report_template.html',
        user_name    = user_name,
        history      = history_data,       # 近7日体征记录列表
        ai_report    = ai_report,          # DeepSeek 深度建议文本
        summary      = summary,            # 统计摘要（均值/评分/风险等级）
        generated_at = datetime.now().strftime('%Y-%m-%d %H:%M')
    )
    HTML(string=html_content).write_pdf(output_path)
    return output_path

def download_pdf_logic(user_id):
    """PDF 下载接口：汇总数据 → 调用导出函数 → 返回文件流"""
    from datetime import timedelta
    start_time = datetime.now() - timedelta(days=7)
    records = SensorData.query.filter(
        SensorData.user_id == user_id,
        SensorData.timestamp >= start_time
    ).order_by(SensorData.timestamp.asc()).all()

    # 统计摘要：各字段均值（过滤 None）
    hrs  = [r.heart_rate  for r in records if r.heart_rate  is not None]
    slps = [r.sleep_hours for r in records if r.sleep_hours is not None]
    stps = [r.steps       for r in records if r.steps       is not None]
    summary = {
        "avg_heart_rate": round(sum(hrs)  / len(hrs),  1) if hrs  else '--',
        "avg_sleep":      round(sum(slps) / len(slps), 1) if slps else '--',
        "avg_steps":      int(sum(stps)   / len(stps))    if stps else '--',
    }
    latest_report = HealthReport.query.filter_by(user_id=user_id) \
        .order_by(HealthReport.created_at.desc()).first()
    ai_report = latest_report.cloud_ai_report if latest_report \
        else "暂无 AI 报告，请先进行 AI 分析。"

    output_path = f"static/reports/report_{user_id}.pdf"
    export_health_report_pdf(
        user_name    = "用户",
        history_data = [{"timestamp": r.timestamp.strftime('%m-%d %H:%M'),
                         "heart_rate": r.heart_rate, "sleep_hours": r.sleep_hours,
                         "steps": r.steps} for r in records],
        ai_report    = ai_report,
        output_path  = output_path,
        summary      = summary,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 模块十三  桌面应用启动器（Flask 线程 + pywebview 原生窗口）
# 来源文件：main.py
# 实现思路：
#   1. 在守护线程（daemon=True）中启动 Flask，主线程退出时自动终止，
#      避免孤儿进程。use_reloader=False 防止 Werkzeug 双进程冲突。
#   2. urllib.request 轮询等待 Flask 就绪（最多 10s），确保窗口打开时
#      后端已可响应请求，避免首屏空白。
#   3. pywebview.create_window 创建无浏览器依赖的原生 WebView 窗口，
#      在 Windows 上使用 EdgeHTML/WebView2 引擎渲染 Vue SPA 页面。
# ─────────────────────────────────────────────────────────────────────────────
import threading, time, urllib.request
import webview

def start_flask():
    """在后台守护线程启动 Flask，关闭主窗口时自动退出"""
    from app import app
    app.run(host='127.0.0.1', port=5000,
            debug=False, use_reloader=False, threaded=True)

def launch_desktop_app():
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()

    # 轮询等待 Flask 就绪（最多 10 秒）
    for _ in range(20):
        try:
            urllib.request.urlopen('http://127.0.0.1:5000/', timeout=1)
            break
        except Exception:
            time.sleep(0.5)

    # 创建原生桌面窗口（不依赖外部浏览器）
    webview.create_window(
        title     = 'HealthAI 智慧家居健康管理系统',
        url       = 'http://127.0.0.1:5000/',
        width     = 1280,
        height    = 820,
        min_size  = (960, 600),
        resizable = True,
    )
    webview.start(debug=False)

if __name__ == '__main__':
    launch_desktop_app()
