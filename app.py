import joblib
from flask import Flask, request, jsonify, render_template
from models import db, User, SensorData, HealthReport
from services import save_sensor_data, get_health_history
from ai_service import calculate_health_score
from flask import jsonify
import logging
from logging.handlers import RotatingFileHandler
from cloud_ai_service import get_cloud_ai_advice
import pandas as pd

app = Flask(__name__)

# 配置日志：记录到 app.log
file_handler = RotatingFileHandler('app.log', maxBytes=1024 * 1024, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)

# 1. 基础与数据库配置
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost:3306/smart_home_health'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 2. 加载 AI 模型
try:
    health_model = joblib.load('health_model.pkl')
    print("✅ AI 模型加载成功，系统已就绪。")
except Exception as e:
    print(f"❌ 模型加载失败: {e}")
    health_model = None

# 3. 数据库与初始数据加载
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

# 4. 路由与 API 接口
@app.route('/')
def index():
    return "<h1>智慧家居健康系统 - 运行中</h1><p>数据正在后台源源不断地写入...</p>"

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
        return jsonify({"code": 200, "msg": message}), 200
    return jsonify({"code": 500, "msg": message}), 500

@app.route('/api/health/history')
def health_history_api():
    """获取用户历史数据，供前端 ECharts 渲染使用"""
    user_id = 1 # 测试阶段写死，后期从登录 Session 获取
    result = get_health_history(user_id, days=7)
    
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
    app.run(debug=True)