from flask import Flask
from models import db, SensorData
from flask import request, jsonify
from services import save_sensor_data

app = Flask(__name__)

# --- 数据库配置 ---
# 格式：mysql+pymysql://用户名:密码@主机地址:端口号/数据库名
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost:3306/smart_home_health'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化插件
db.init_app(app)

# 创建数据库表的脚本
with app.app_context():
    db.create_all()
    print("数据库表已成功创建！")

with app.app_context():
    db.create_all()
    # 检查是否已经有名为 id=1 的用户
    from models import User
    admin = User.query.get(1)
    if not admin:
        print("检测到无初始用户，正在创建...")
        new_user = User(id=1, username="admin", password_hash="123456")
        db.session.add(new_user)
        db.session.commit()
        print("初始用户(ID:1)创建成功！")
    else:
        print("初始用户已存在，跳过创建。")

@app.route('/')
def index():
    return "<h1>智慧家居健康系统 - 运行中</h1><p>数据正在后台源源不断地写入...</p>"

@app.route('/api/sensor/upload', methods=['POST'])
def upload_data():
    # 获取 POST 请求中的 JSON 数据
    json_data = request.get_json()
    
    if not json_data:
        return jsonify({"code": 400, "msg": "未接收到 JSON 数据"}), 400

    # 调用封装好的逻辑函数
    success, message = save_sensor_data(json_data)

    if success:
        return jsonify({"code": 200, "msg": message}), 200
    else:
        return jsonify({"code": 500, "msg": message}), 500

# 查询测试
@app.route('/test_db')
def test_db():
    # 查询数据库中最后一条记录
    last_data = SensorData.query.order_by(SensorData.id.desc()).first()
    if last_data:
        return f"最新心率: {last_data.heart_rate}, 写入时间: {last_data.timestamp}"
    return "数据库里还没有数据哦。"

if __name__ == '__main__':
    app.run(debug=True)
