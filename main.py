"""
HealthAI 智慧舱 - 桌面启动入口
流程: 后台线程启动 Flask → pywebview 打开原生窗口 → 关闭窗口退出程序
"""
import sys
import os
import threading
import time
import webview

# ── PyInstaller 资源路径 ──────────────────────────────────────
def resource_path(relative):
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)

# 确保工作目录正确（打包后 cwd 可能不对）
os.chdir(resource_path('.'))

# ── 启动日志（写到 exe 同级目录）────────────────────────────
import logging as _logging
_log_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'startup.log')
_logging.basicConfig(
    filename=_log_path, level=_logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)
_logger = _logging.getLogger('main')
_flask_error = []

# ── 启动 Flask（后台守护线程）────────────────────────────────
def start_flask():
    try:
        _logger.info('Flask 线程启动')
        from app import app
        _logger.info('app.py 导入成功，开始监听 5000 端口')
        app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False, threaded=True)
    except Exception as e:
        _logger.exception(f'Flask 启动失败: {e}')
        _flask_error.append(str(e))

flask_thread = threading.Thread(target=start_flask, daemon=True)
flask_thread.start()

# 等待 Flask 就绪（最多 15 秒）
import urllib.request
flask_ready = False
for _ in range(30):
    if _flask_error:
        break
    try:
        urllib.request.urlopen('http://127.0.0.1:5000/', timeout=1)
        flask_ready = True
        _logger.info('Flask 就绪，打开窗口')
        break
    except Exception:
        time.sleep(0.5)

if not flask_ready:
    err_msg = _flask_error[0] if _flask_error else '启动超时，请查看 startup.log'
    _logger.error(f'Flask 未就绪: {err_msg}')

# ── 创建原生窗口 ─────────────────────────────────────────────
window = webview.create_window(
    title='HealthAI 智慧家居健康管理系统',
    url='http://127.0.0.1:5000/',
    width=1280,
    height=820,
    min_size=(960, 600),
    resizable=True,
)

if __name__ == '__main__':
    # gui=None 让 pywebview 自动选择平台最佳引擎
    webview.start(debug=False)
