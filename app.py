from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import sklearn

app = Flask(__name__)

# 暂时配置一个简单的数据库连接路径（后续会改为 MySQL）
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

@app.route('/')
def health_check():
    # 验证 pandas 是否正常工作
    data = {'指标': ['心率', '睡眠'], '数值': [75, 8]}
    df = pd.DataFrame(data)
    return f"系统运行中！Pandas 版本: {pd.__version__} | AI 模块已加载。"

if __name__ == '__main__':
    app.run(debug=True)