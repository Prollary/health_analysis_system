# -*- mode: python ; coding: utf-8 -*-
"""
HealthAI 智慧舱 - PyInstaller 打包规格
运行方式: pyinstaller healthai.spec
输出: dist/HealthAI智慧舱/HealthAI智慧舱.exe  (单目录模式，启动更快)
"""

import os
from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

# ── 收集所有需要隐式导入的包 ────────────────────────────────
hidden_imports = [
    'webview',
    'webview.platforms.winforms',
    'clr',
    'flask',
    'flask_sqlalchemy',
    'flask_jwt_extended',
    'flask_mail',
    'sqlalchemy',
    'sqlalchemy.dialects.mysql',
    'sqlalchemy.dialects.mysql.pymysql',
    'pymysql',
    'pymysql.converters',
    'cryptography',                          # MySQL caching_sha2_password 必需
    'cryptography.hazmat.primitives',
    'cryptography.hazmat.backends',
    'sklearn',
    'sklearn.ensemble',
    'sklearn.tree',
    'sklearn.utils',
    'sklearn.utils._cython_blas',
    'joblib',
    'pandas',
    'numpy',
    'openai',
    'httpx',
    'weasyprint',
    'dotenv',
    'jwt',
    'werkzeug',
    'werkzeug.security',
    'jinja2',
    'pydantic',
    'email.mime.text',
    'email.mime.multipart',
    'threading',
]
hidden_imports += collect_submodules('sklearn')
hidden_imports += collect_submodules('weasyprint')
hidden_imports += collect_submodules('webview')

# ── 收集数据文件 ─────────────────────────────────────────────
datas = [
    ('static/dist',    'static/dist'),
    ('templates',      'templates'),
    ('health_model.pkl', '.'),
    ('.env',           '.'),
]

# 收集 weasyprint 字体/css 数据
_datas_w, _bins_w, _hi_w = collect_all('weasyprint')
datas   += _datas_w
hidden_imports += _hi_w

# 收集 pywebview 数据
_datas_v, _bins_v, _hi_v = collect_all('webview')
datas   += _datas_v
hidden_imports += _hi_v

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=_bins_w + _bins_v,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'IPython', 'notebook'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='HealthAI智慧舱',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # 不显示黑色控制台窗口
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='healthai.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='HealthAI智慧舱',
)
