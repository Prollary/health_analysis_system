from flask import Flask
from models import db  # 从刚才创建的文件导入

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

@app.route('/')
def index():
    return "数据库已连接，表结构已就绪。"

if __name__ == '__main__':
    app.run(debug=True)