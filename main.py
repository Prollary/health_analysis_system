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

# ── 启动 Flask（后台守护线程）────────────────────────────────
def start_flask():
    from app import app
    # 关闭 Flask 的 reloader，避免线程冲突
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False, threaded=True)

flask_thread = threading.Thread(target=start_flask, daemon=True)
flask_thread.start()

# 等待 Flask 就绪（最多 10 秒）
import urllib.request
for _ in range(20):
    try:
        urllib.request.urlopen('http://127.0.0.1:5000/', timeout=1)
        break
    except Exception:
        time.sleep(0.5)

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
