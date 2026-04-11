import os
import sys
import joblib
from flask import Flask, request, jsonify, render_template, send_file, send_from_directory
from models import db, User, SensorData, HealthReport, HealthDiary, FaceAnalysis
from services import save_sensor_data, get_health_history, check_sos_condition
from ai_service import calculate_health_score
import logging
from logging.handlers import RotatingFileHandler
from cloud_ai_service import get_cloud_ai_advice, parse_health_diary, analyze_face_emotion, generate_detailed_intervention
import pandas as pd
from flask_mail import Mail, Message
from werkzeug.exceptions import HTTPException
from pdf_service import export_health_report_pdf
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# 支持 PyInstaller 打包后资源路径
def resource_path(relative):
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)

app = Flask(
    __name__,
    static_folder=resource_path('static/dist'),
    static_url_path='',
    template_folder=resource_path('templates'),
)

# 配置日志：记录到 app.log
file_handler = RotatingFileHandler('app.log', maxBytes=1024 * 1024, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)

# 基础与数据库配置
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost:3306/smart_home_health'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = 'smtp.qq.com' # QQ邮箱
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = '2269626378@qq.com'
app.config['MAIL_PASSWORD'] = 'mtbapqvilqzreceh' 
app.config['MAIL_DEFAULT_SENDER'] = '2269626378@qq.com'
app.config['JWT_SECRET_KEY'] = 'smart-home-health-super-secret-key-2026' 
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(days=7) # 令牌 7 天有效

jwt = JWTManager(app)
mail = Mail(app)

# 加载 AI 模型
try:
    health_model = joblib.load('health_model.pkl')
    print("✅ AI 模型加载成功，系统已就绪。")
except Exception as e:
    print(f"❌ 模型加载失败: {e}")
    health_model = None

# 数据库与初始数据加载
db.init_app(app)

with app.app_context():
    db.create_all() # 创建所有表
    print("✅ 数据库表已成功创建/连接！")
    
    # 检查并创建初始管理员用户
    if not User.query.get(1):
        print("检测到无初始用户，正在创建...")
        new_user = User(id=1, username="admin", password_hash="123456")
        db.session.add(new_user)
        db.session.commit()
        print("✅ 初始用户(ID:1)创建成功！")

# 路由与 API 接口
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
    # API 请求不走这里（已由各 /api/* 路由处理）
    dist_dir = resource_path('static/dist')
    file_path = os.path.join(dist_dir, path)
    if path and os.path.isfile(file_path):
        return send_from_directory(dist_dir, path)
    return send_from_directory(dist_dir, 'index.html')

@app.route('/test_db')
def test_db():
    """测试接口：快速查看最新一条数据"""
    last_data = SensorData.query.order_by(SensorData.id.desc()).first()
    if last_data:
        return f"最新心率: {last_data.heart_rate}, 写入时间: {last_data.timestamp}"
    return "数据库里还没有数据哦。"

@app.route('/api/sensor/upload', methods=['POST'])
def upload_data():
    """接收硬件传感器上传的 JSON 数据"""
    json_data = request.get_json()
    if not json_data:
        return jsonify({"code": 400, "msg": "未接收到 JSON 数据"}), 400

    success, message = save_sensor_data(json_data)

    if success:
        # --- 本地 AI 自动评分（同步，仅用本地模型，不调云端）---
        if health_model is not None:
            try:
                analysis = calculate_health_score(
                    heart_rate=json_data.get('heart_rate', 70),
                    sleep_hours=json_data.get('sleep_hours', 7),
                    steps=json_data.get('steps', 5000),
                    room_temp=json_data.get('room_temp', 25.0),
                    humidity=json_data.get('humidity', 50.0),
                    co2_level=json_data.get('co2_level', 400),
                    model=health_model
                )
                auto_report = HealthReport(
                    user_id=json_data['user_id'],
                    health_score=analysis['health_score'],
                    risk_level=analysis['risk_level'],
                    ai_suggestion=analysis['suggestion']
                )
                db.session.add(auto_report)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                app.logger.warning(f"自动评分失败: {e}")

        # --- SOS 实时检测 ---
        current_user = db.session.get(User, json_data['user_id'])
        is_sos, sos_msg = check_sos_condition(current_user, json_data)

        return jsonify({
            "code": 200,
            "msg": message,
            "sos_alert": is_sos,
            "sos_msg": sos_msg
        }), 200

    return jsonify({"code": 500, "msg": message}), 500

@app.route('/api/health/history', methods=['GET'])
@jwt_required()
def health_history_api():
    """获取用户历史数据。管理员可通过 ?user_id=xxx 查询家庭成员数据"""
    current_user_id = int(get_jwt_identity())
    target_id = request.args.get('user_id', type=int, default=current_user_id)

    # 若请求的不是自己的数据，验证当前用户是否为该成员的管理员
    if target_id != current_user_id:
        current_user = db.session.get(User, current_user_id)
        target_user  = db.session.get(User, target_id)
        if not target_user or target_user.parent_id != current_user_id:
            return jsonify({"error": "无权限查看该成员数据"}), 403

    result = get_health_history(user_id=target_id, days=7)
    if result["status"] == "success":
        return jsonify(result["data"])
    return jsonify({"error": result["message"]}), 500



@app.route('/api/analyze/<int:user_id>', methods=['POST', 'GET'])
def analyze_health(user_id):
    if health_model is None:
        return jsonify({"code": 500, "msg": "AI 模型不可用"}), 500

    # 获取最新的一条传感器数据
    latest_data = SensorData.query.filter_by(user_id=user_id).order_by(SensorData.timestamp.desc()).first()
    if not latest_data:
        return jsonify({"code": 404, "msg": "未找到该用户的体征数据，无法分析"}), 404

    # 本地模型分析
    analysis_result = calculate_health_score(
        heart_rate=latest_data.heart_rate,
        sleep_hours=latest_data.sleep_hours,
        steps=latest_data.steps,
        room_temp=latest_data.room_temp,
        humidity=latest_data.humidity,
        co2_level=latest_data.co2_level,
        model=health_model
    )
    combined_suggestion = analysis_result["suggestion"]
    if analysis_result["linkage_analysis"]["env_suggestions"]:
        combined_suggestion += "\n" + analysis_result["linkage_analysis"]["env_suggestions"][0]

    # 百度云端 AI 深度分析 
    cloud_report = get_cloud_ai_advice(
        latest_data.heart_rate, 
        latest_data.sleep_hours,
        latest_data.steps,
        latest_data.room_temp,
        latest_data.co2_level
    )

    # 持久化报告
    new_report = HealthReport(
        user_id=user_id,
        health_score=analysis_result["health_score"],
        risk_level=analysis_result["risk_level"],
        ai_suggestion=analysis_result["suggestion"],
        cloud_ai_report=cloud_report  # 存入云端建议
    )
    db.session.add(new_report)
    db.session.commit()

    return jsonify({
        "code": 200,
        "data": {
            "local": analysis_result,
            "cloud_advice": cloud_report # 返回给前端
        }
    })

@app.route('/dashboard')
def dashboard():
    """渲染前端控制台页面"""
    return render_template('dashboard.html')


@app.route('/api/family/members')
def get_family_members():
    """获取管理员名下的所有家庭成员列表"""
    admin_id = 1  # 暂定
    admin = db.session.get(User, admin_id)
    members = [{"id": m.id, "name": m.username} for m in admin.family_members]
    return jsonify(members)

@app.route('/api/family/monitor/<int:member_id>')
def monitor_member(member_id):
    """管理员切换查看特定成员的数据"""
    # 逻辑复用 /api/health/history
    # 在前端传参时改变 ID 即可
    pass



# 健康日记接口
@app.route('/api/diary/submit', methods=['POST'])
def submit_diary():
    data = request.get_json()
    user_id = data.get('user_id', 1)
    diary_text = data.get('content')

    if not diary_text:
        return jsonify({"code": 400, "msg": "日记内容不能为空"}), 400

    # 调用千帆大模型解析
    ai_result = parse_health_diary(diary_text)

    # 存入数据库
    new_diary = HealthDiary(
        user_id=user_id,
        raw_content=diary_text,
        extracted_symptoms=ai_result.get("symptoms"),
        ai_advice=ai_result.get("advice")
    )
    db.session.add(new_diary)
    db.session.commit()

    return jsonify({"code": 200, "msg": "解析成功", "data": ai_result})



# 智能面部情绪接口
@app.route('/api/vision/smart_mirror', methods=['POST'])
def smart_mirror_analyze():
    data = request.get_json()
    user_id = data.get('user_id', 1)
    base64_image = data.get('image') # 前端传来的 Base64 图像

    if not base64_image:
        return jsonify({"code": 400, "msg": "未接收到图像数据"}), 400

    # 去除 base64 头部
    if "," in base64_image:
        base64_image = base64_image.split(",")[1]

    # 调用 DeepSeek 视觉分析情绪（不可用时自动降级）
    face_res = analyze_face_emotion(base64_image)
    if face_res["status"] == "success":
        emotion = face_res["emotion"]
    else:
        # 降级：根据时段给出默认情绪，不中断流程
        hour = datetime.datetime.now().hour
        emotion = "平静" if 8 <= hour <= 22 else "疲惫"

    # 从数据库获取最新生理数据，进行多模态身心综合分析
    latest_sensor = SensorData.query.filter_by(user_id=user_id).order_by(SensorData.timestamp.desc()).first()

    # 疲劳/压力指数计算（情绪 + 生理体征）
    fatigue_index = 0
    if emotion in ["悲伤", "愤怒", "厌恶", "疲惫", "恐惧"]:
        fatigue_index += 40
    if latest_sensor and latest_sensor.heart_rate and latest_sensor.heart_rate > 90:
        fatigue_index += 30
    if latest_sensor and latest_sensor.sleep_hours and latest_sensor.sleep_hours < 6:
        fatigue_index += 30

    hr_str    = f"{latest_sensor.heart_rate}bpm" if latest_sensor and latest_sensor.heart_rate else "未知"
    sleep_str = f"{latest_sensor.sleep_hours}h"  if latest_sensor and latest_sensor.sleep_hours else "未知"

    report = f"【身心综合报告】面部情绪识别为「{emotion}」，疲劳/压力指数 {fatigue_index}/100。" \
             f"结合今日心率 {hr_str}、睡眠 {sleep_str}，"
    if fatigue_index >= 70:
        report += "综合评估：高压/深度疲劳状态。建议立即放下工作，进行10分钟深呼吸或听舒缓音乐放松。"
    elif fatigue_index >= 40:
        report += "综合评估：轻中度疲劳。建议适当休息，补充水分，避免高强度用脑。"
    else:
        report += "综合评估：身心状态良好，继续保持规律作息。"

    # 存入数据库
    new_face_record = FaceAnalysis(
        user_id=user_id,
        emotion=emotion,
        fatigue_index=fatigue_index,
        comprehensive_report=report
    )
    db.session.add(new_face_record)
    db.session.commit()

    return jsonify({"code": 200, "msg": "分析成功", "data": {"emotion": emotion, "report": report, "fatigue_index": fatigue_index}})

# 生成包含深度干预方案的正式报告
@app.route('/api/health/report/generate/<int:user_id>')
def generate_full_report(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"code": 404, "msg": "用户不存在"}), 404

    latest_data = SensorData.query.filter_by(user_id=user_id).order_by(SensorData.timestamp.desc()).first()
    if not latest_data:
        return jsonify({"code": 404, "msg": "暂无体征数据，请先上传传感器数据"}), 404

    # 从最新报告中获取风险等级，没有则默认中风险
    latest_report = HealthReport.query.filter_by(user_id=user_id).order_by(HealthReport.created_at.desc()).first()
    risk_level = latest_report.risk_level if latest_report and latest_report.risk_level else '中风险'

    profile = {
        'age':    user.age    if user.age    is not None else '未知',
        'gender': user.gender if user.gender is not None else '未知'
    }
    analysis = {
        'risk_level': risk_level,
        'heart_rate': latest_data.heart_rate,
        'sleep':      latest_data.sleep_hours,
        'steps':      latest_data.steps
    }
    detailed_plan_dict = generate_detailed_intervention(profile, analysis)
    
    # 使用严格的分界符拼接
    detailed_plan = f"=====【饮食专区】=====\n{detailed_plan_dict.get('diet', '')}\n\n=====【运动专区】=====\n{detailed_plan_dict.get('exercise', '')}"

    report = HealthReport(
        user_id=user_id,
        cloud_ai_report=detailed_plan
    )
    db.session.add(report)
    db.session.commit()

    return jsonify({"code": 200, "msg": "方案已生成", "plan": detailed_plan})



# 下载 PDF 报表
@app.route('/api/health/report/download/<int:user_id>')
def download_pdf(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"code": 404, "msg": "用户不存在"}), 404

    # 获取近7天传感器数据
    from datetime import datetime, timedelta
    start_time = datetime.now() - timedelta(days=7)
    records = SensorData.query.filter(
        SensorData.user_id == user_id,
        SensorData.timestamp >= start_time
    ).order_by(SensorData.timestamp.asc()).all()

    history = [
        {
            "timestamp":   r.timestamp.strftime('%m-%d %H:%M'),
            "heart_rate":  r.heart_rate,
            "sleep_hours": r.sleep_hours,
            "steps":       r.steps,
            "room_temp":   r.room_temp,
            "humidity":    r.humidity,
            "co2_level":   r.co2_level,
        }
        for r in records
    ]

    # 最新报告
    latest_report = HealthReport.query.filter_by(user_id=user_id)\
        .order_by(HealthReport.created_at.desc()).first()

    # 统计摘要
    summary = None
    if records:
        hrs    = [r.heart_rate  for r in records if r.heart_rate  is not None]
        slps   = [r.sleep_hours for r in records if r.sleep_hours is not None]
        stps   = [r.steps       for r in records if r.steps       is not None]
        valid_report = HealthReport.query.filter(HealthReport.user_id==user_id, HealthReport.health_score != None).order_by(HealthReport.created_at.desc()).first()

        summary = {
            "avg_heart_rate": round(sum(hrs)  / len(hrs),  1) if hrs  else '--',
            "avg_sleep":      round(sum(slps) / len(slps), 1) if slps else '--',
            "avg_steps":      int(sum(stps)   / len(stps))    if stps else '--',
            "health_score":   valid_report.health_score if valid_report else None,
            "risk_level":     valid_report.risk_level   if valid_report else None,
        }

    ai_report = latest_report.cloud_ai_report if latest_report else "暂无 AI 报告，请先在首页进行 AI 分析。"

    os.makedirs("static/reports", exist_ok=True)
    output_file = f"static/reports/report_{user_id}.pdf"
    export_health_report_pdf(
        user_name=user.username,
        history_data=history,
        ai_report=ai_report,
        output_path=output_file,
        summary=summary
    )

    return send_file(output_file, as_attachment=True,
                     download_name=f"健康周报_{user.username}.pdf")



# 用户认证模块 (Auth)
@app.route('/api/auth/register', methods=['POST'])
def register():
    """用户注册接口"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'member') # 默认注册为普通成员
    
    if not username or not password:
        return jsonify({"code": 400, "msg": "用户名和密码不能为空"}), 400

    # 检查用户名是否已存在
    if User.query.filter_by(username=username).first():
        return jsonify({"code": 400, "msg": "用户名已被注册"}), 400

    # 创建新用户
    new_user = User(username=username, role=role)
    new_user.set_password(password) # 使用刚才在 models.py 写的加密方法
    email = data.get('email', '').strip()
    if email:
        new_user.email = email

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"code": 200, "msg": "注册成功"}), 200

# 用户登录
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    # 验证用户存在且密码正确
    if user and user.check_password(password):
        # 登录成功，生成专属令牌，并把用户 ID 藏在里面
        access_token = create_access_token(identity=str(user.id))
        
        return jsonify({
            "code": 200,
            "msg": "登录成功",
            "data": {
                "access_token": access_token,
                "user_id": user.id,
                "username": user.username,
                "role": user.role
            }
        }), 200
    else:
        return jsonify({"code": 401, "msg": "用户名或密码错误"}), 401


@app.route('/api/auth/profile', methods=['GET', 'PUT'])
@jwt_required()
def profile():
    """获取或更新当前用户资料（包括邮箱）"""
    current_user_id = int(get_jwt_identity())
    user = db.session.get(User, current_user_id)
    if not user:
        return jsonify({"code": 404, "msg": "用户不存在"}), 404

    if request.method == 'GET':
        return jsonify({
            "code": 200,
            "data": {
                "id": user.id,
                "username": user.username,
                "email": user.email or "",
                "role": user.role
            }
        })

    # PUT：更新邮箱
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    if not email:
        return jsonify({"code": 400, "msg": "邮箱不能为空"}), 400
    user.email = email
    db.session.commit()
    return jsonify({"code": 200, "msg": "邮箱设置成功"})


@app.route('/api/family/add_member', methods=['POST'])
@jwt_required()
def add_family_member():
    """将已有用户加入到当前操作者的家庭组中"""
    # 1. 获取当前登录用户的 ID
    current_user_id = int(get_jwt_identity())
    current_user = db.session.get(User, current_user_id)

    # 2. 解析前端传来的目标用户名
    data = request.get_json()
    target_username = data.get('username')

    if not target_username:
        return jsonify({"code": 400, "msg": "请输入要添加的成员用户名"}), 400

    # 3. 在数据库中查找目标用户
    target_user = User.query.filter_by(username=target_username).first()

    if not target_user:
        return jsonify({"code": 404, "msg": "未找到该用户，请确认用户名是否正确"}), 404

    # 4. 逻辑校验：不能添加自己，不能抢夺别人家庭的成员
    if target_user.id == current_user.id:
        return jsonify({"code": 400, "msg": "不能将自己添加为成员"}), 400

    if target_user.parent_id:
        return jsonify({"code": 400, "msg": f"添加失败：{target_username} 已经加入其他家庭组"}), 400

    # 5. 执行绑定逻辑 (建立户主与成员的关联)
    target_user.parent_id = current_user.id
    target_user.role = 'member' # 确保被拉入的人是成员角色
    current_user.role = 'admin' # 将当前操作者自动升级为该家庭的管理员(户主)

    db.session.commit()

    return jsonify({
        "code": 200,
        "msg": f"成功将 {target_username} 加入您的家庭组！"
    }), 200


@app.route('/api/family/group', methods=['GET'])
@jwt_required()
def get_family_group():
    """获取当前用户所在的家庭组名单"""
    current_user_id = int(get_jwt_identity())
    current_user = db.session.get(User, current_user_id)

    # 1. 确定"户主"是谁
    # 如果当前用户有 parent_id，是成员，他的 parent 才是户主；否则自己就是户主
    admin_id = current_user.parent_id if current_user.parent_id else current_user.id
    admin_user = db.session.get(User, admin_id)

    # 2. 组装家庭名单（先把户主自己加进去）
    family_list = [{
        "user_id": admin_user.id,
        "username": admin_user.username,
        "role": "admin",
        "is_self": admin_user.id == current_user.id # 标记哪条数据是当前登录者自己
    }]

    # 3. 遍历户主名下的所有成员，加入列表
    for member in admin_user.family_members:
        family_list.append({
            "user_id": member.id,
            "username": member.username,
            "role": "member",
            "is_self": member.id == current_user.id
        })

    return jsonify({
        "code": 200,
        "msg": "获取家庭组成功",
        "data": {
            "family_size": len(family_list),
            "members": family_list
        }
    }), 200


# 全局处理 404 错误
@app.errorhandler(404)
def not_found(error):
    return jsonify({"status": "error", "message": "请求的资源不存在"}), 404

# 全局处理 500 错误 (代码逻辑崩溃)
@app.errorhandler(Exception)
def handle_exception(e):
    # 判断错误类型
    app.logger.error(f"系统运行崩溃: {str(e)}") # 记录到服务器日志
    return jsonify({
        "status": "error", 
        "message": "系统繁忙或后台故障，请稍后再试",
        "error_type": type(e).__name__ 
    }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)