from flask import Flask, render_template

# 初始化 Flask 实例
app = Flask(__name__)

# 定义路由：当访问网站首页 (/) 时执行函数
@app.route('/')
def index():
    # 目前先返回一串文字，后期我们会通过 render_template 返回 HTML 页面
    return "<h1>智慧家居健康分析系统</h1><p>后端基础架构已启动！</p>"

# 启动服务器
if __name__ == '__main__':
    # debug=True 表示开启调试模式，修改代码后服务器会自动重启
    app.run(host='127.0.0.1', port=5000, debug=True)