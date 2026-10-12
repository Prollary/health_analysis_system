# HealthAI 智慧家居健康分析系统

> 基于 Flask + Vue 3 + AI 技术的全栈智慧家居健康管理平台，面向居家老人与家庭健康监护场景。

## 目录

- [项目简介](#项目简介)
- [功能特性](#功能特性)
- [技术架构](#技术架构)
- [系统原理](#系统原理)
- [目录结构](#目录结构)
- [快速开始](#快速开始)
- [使用说明](#使用说明)
- [API 接口](#api-接口)
- [常见问题](#常见问题)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

---

## 项目简介

HealthAI 智慧家居健康分析系统是一款面向居家养老与家庭健康管理的全栈应用。系统通过模拟或真实传感器持续采集用户的生理指标（心率、睡眠、步数、体温）与家居环境数据（室温、湿度、CO₂浓度），结合**本地机器学习模型**与**DeepSeek 大语言模型**进行多维健康分析，最终将结果以可视化大屏的形式呈现给用户，并在紧急情况下自动触发 SOS 邮件告警。

**适用场景：**

- 居家老人健康状态实时监护
- 子女（管理员）远程查看家庭成员健康数据
- 智能镜子面部情绪识别与身心健康融合分析
- 个性化饮食与运动干预方案生成

---

## 功能特性

| 功能模块 | 说明 |
|---|---|
| **实时健康仪表盘** | 心率、睡眠、步数、体温等核心指标可视化，趋势折线图 |
| **本地 AI 健康评分** | scikit-learn 模型实时计算健康分（0-100）及风险等级（低/中/高） |
| **云端 AI 深度分析** | 调用 DeepSeek 大模型，生成环境-生理联动 100 字专业简报 |
| **环境监测** | 室温、湿度、CO₂浓度实时展示，久坐缺氧预警 |
| **智能镜子情绪识别** | 上传人脸照片，DeepSeek 视觉模型识别情绪并生成身心综合报告 |
| **健康日记 NLP 解析** | 老人用口语描述身体状况，AI 自动提取症状实体并给出就医建议 |
| **AI 深度干预方案** | 基于用户画像（年龄/性别/风险等级）生成个性化饮食 + 运动方案 |
| **PDF 健康周报导出** | WeasyPrint 渲染 HTML 模板，一键导出结构化健康报告 |
| **SOS 紧急告警** | 检测到异常指标自动触发，通过 QQ 邮箱推送告警邮件 |
| **家庭多用户管理** | 管理员（子女）可查看和管理名下所有家庭成员数据 |
| **传感器数据模拟** | 内置模拟器脚本，无需硬件即可完整体验所有功能 |
| **EXE 桌面打包** | PyInstaller 打包，支持 Windows 一键启动 |

---

## 技术架构

```
┌──────────────────────────────────────────────┐
│               前端 (Vue 3 + Vite)             │
│  ECharts 图表 │ Pinia 状态管理 │ Axios 请求   │
└──────────────────────┬───────────────────────┘
                       │ HTTP / REST API
┌──────────────────────▼───────────────────────┐
│              后端 (Flask 3.x)                 │
│  JWT 鉴权 │ Flask-Mail │ Flask-SQLAlchemy     │
├──────────────────────────────────────────────┤
│  本地 AI 层                云端 AI 层          │
│  scikit-learn (RandomForest)  DeepSeek API   │
│  health_model.pkl             LLM / Vision   │
├──────────────────────────────────────────────┤
│              数据层 (MySQL)                   │
│  users │ sensor_data │ health_reports        │
│  face_analysis │ health_diaries              │
└──────────────────────────────────────────────┘
```

**后端核心依赖：**
- `Flask 3.1` — Web 框架与 RESTful API
- `Flask-SQLAlchemy 3.1` + `PyMySQL` — ORM 与 MySQL 数据库
- `Flask-JWT-Extended 4.7` — JWT 身份认证
- `Flask-Mail 0.10` — 邮件 SOS 告警
- `scikit-learn 1.7` — 本地健康评分模型
- `WeasyPrint 68` — PDF 报告生成
- `openai SDK` — 兼容 DeepSeek API 调用

**前端核心依赖：**
- `Vue 3` + `Vite` — 响应式前端框架
- `vue-echarts` — 数据可视化图表
- `Pinia` — 全局状态管理
- `Axios` — HTTP 请求封装

---

## 系统原理

### 1. 健康评分（本地 AI）

系统预训练了一个基于 scikit-learn 的分类模型（`health_model.pkl`），输入 6 维特征：

```
心率 | 睡眠时长 | 步数 | 室温 | 湿度 | CO₂浓度
```

模型输出三分类概率（健康 / 亚健康 / 高风险），并按加权公式计算连续健康分：

```
健康分 = P(健康) × 100 + P(亚健康) × 60 + P(高风险) × 20
```

### 2. 环境-生理联动分析

内置规则引擎，识别以下典型联动场景：

- **久坐缺氧预警**：步数 < 500 步 且 CO₂ > 1000 ppm → 推送开窗通风提醒
- **睡眠-室温联动**：室温 > 26℃ 且睡眠 < 6.5h → 推荐空调睡眠模式设定
- **湿度不适预警**：湿度 > 70% → 推荐开启抽湿设备

### 3. 云端 AI（DeepSeek）

通过与 DeepSeek API 的对话式交互，实现四类智能功能：

| 功能 | 技术方式 |
|---|---|
| 健康综合建议 | 将生理 + 环境数据结构化为 Prompt，调用 `deepseek-chat` |
| 健康日记解析 | Few-shot Prompt + JSON 结构化输出，提取症状实体 |
| 面部情绪识别 | 多模态 Vision 接口，Base64 图片 + 文本 Prompt |
| 深度干预方案 | 链式调用，分别生成饮食方案与运动方案（各 2048 tokens）|

### 4. 数据流

```
传感器/模拟器 → POST /api/sensor/upload
    → 存入 sensor_data 表
    → 触发本地 AI 自动评分 → 存入 health_reports 表
    → 检测 SOS 条件 → 异常则发送告警邮件
前端拉取 → GET /api/health/history → JWT 鉴权 → 返回最近 7 天数据
```

---

## 目录结构

```
health_analysis_system/
├── app.py                  # Flask 主应用，所有路由与 API 接口
├── models.py               # SQLAlchemy 数据模型（5 张表）
├── services.py             # 业务逻辑层（数据存储、历史查询、SOS 检测）
├── ai_service.py           # 本地 AI 健康评分 + 环境联动分析引擎
├── cloud_ai_service.py     # DeepSeek 云端 AI 调用封装（4 个功能）
├── pdf_service.py          # WeasyPrint PDF 健康报告导出
├── simulator.py            # 传感器数据模拟器（用户 1，默认老人）
├── simulator_user2.py      # 模拟器（用户 2，管理员）
├── simulator_user3.py      # 模拟器（用户 3，居家老人）
├── health_model.pkl        # 预训练的 scikit-learn 健康分类模型
├── requirements.txt        # Python 依赖列表
├── healthai.spec           # PyInstaller 打包配置
├── build_all.bat           # 一键打包脚本
├── utils/
│   ├── generate_data.py    # 训练数据生成脚本
│   └── train_model.py      # 模型训练脚本
├── frontend/               # Vue 3 前端项目
│   ├── src/
│   │   ├── views/
│   │   │   ├── DashboardView.vue   # 健康仪表盘
│   │   │   ├── CareView.vue        # 家庭成员监护
│   │   │   ├── EnvironmentView.vue # 家居环境监测
│   │   │   ├── MirrorView.vue      # 智能镜子情绪识别
│   │   │   ├── DiaryView.vue       # 健康日记
│   │   │   ├── ReportView.vue      # AI 报告与干预方案
│   │   │   └── LoginView.vue       # 用户登录
│   │   ├── stores/         # Pinia 状态管理
│   │   ├── router/         # Vue Router 路由配置
│   │   └── api/            # Axios 请求封装
│   └── package.json
├── static/                 # 前端构建产物（dist/）
├── templates/              # Flask HTML 模板（PDF 报告模板）
└── instance/               # SQLite/数据库实例（本地开发）
```

---

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- MySQL 8.0+
- （可选）[WeasyPrint 系统依赖](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation)

### 1. 克隆项目

```bash
git clone https://github.com/your-username/health_analysis_system.git
cd health_analysis_system
```

### 2. 配置 Python 环境

```bash
# 创建并激活虚拟环境
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate.bat       # Windows

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置数据库

在 MySQL 中创建数据库：

```sql
CREATE DATABASE smart_home_health CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

修改 [app.py](app.py) 第 40 行的数据库连接字符串：

```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://用户名:密码@localhost:3306/smart_home_health'
```

### 4. 配置环境变量

在项目根目录创建 `.env` 文件：

```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

如需启用 SOS 邮件告警，修改 [app.py](app.py) 中的邮箱配置：

```python
app.config['MAIL_USERNAME'] = 'your_email@qq.com'
app.config['MAIL_PASSWORD'] = 'your_smtp_authorization_code'
```

### 5. 构建前端

```bash
cd frontend
npm install
npm run build
cd ..
```

### 6. 启动应用

```bash
python app.py
```

应用默认运行在 `http://localhost:5000`，浏览器访问即可进入登录页。

**默认管理员账号：**
- 用户名：`admin`
- 密码：`123456`

### 7. 启动数据模拟器（可选）

无需硬件设备，通过模拟器向系统持续推送测试数据：

```bash
# 新开一个终端，激活虚拟环境后运行
python simulator.py
```

---

## 使用说明

### 仪表盘（Dashboard）

登录后进入主仪表盘，展示当前用户最新健康评分、风险等级及过去 7 天各项指标趋势折线图。点击"触发 AI 分析"按钮可调用云端 DeepSeek 生成深度健康报告。

### 家庭监护（Care）

管理员账号可在此页面切换查看名下所有家庭成员的实时健康数据，适合子女远程监护居家老人。

### 环境监测（Environment）

实时展示卧室温度、湿度、CO₂浓度，并显示环境-生理联动分析结果与预警信息。

### 智能镜子（Mirror）

上传或拍摄人脸照片，系统调用 DeepSeek 视觉模型识别情绪（高兴/悲伤/疲惫等），结合当前生理指标生成身心综合健康报告。

### 健康日记（Diary）

用自然语言描述身体感受（如"今天头有点晕，胸口闷"），AI 自动提取症状实体并给出初步就医建议，记录保存到数据库。

### AI 报告（Report）

一键生成 1000 字以上的个性化饮食方案与运动干预方案（基于用户年龄、性别、风险等级），支持导出为 PDF 健康周报。

---

## API 接口

| 方法 | 路径 | 说明 | 鉴权 |
|---|---|---|---|
| `POST` | `/api/sensor/upload` | 上传传感器数据（自动触发 AI 评分与 SOS 检测） | 无 |
| `GET` | `/api/health/history` | 获取最近 7 天健康历史数据 | JWT |
| `POST` | `/api/analyze/<user_id>` | 触发本地 + 云端双 AI 分析 | 无 |
| `POST` | `/api/auth/login` | 用户登录，返回 JWT Token | 无 |
| `POST` | `/api/diary/submit` | 提交健康日记，AI 解析症状 | JWT |
| `POST` | `/api/mirror/analyze` | 上传人脸图片，情绪识别 | JWT |
| `POST` | `/api/report/intervention` | 生成个性化饮食与运动干预方案 | JWT |
| `GET` | `/api/report/export/<user_id>` | 导出 PDF 健康报告 | JWT |
| `GET` | `/api/family/members` | 获取管理员名下家庭成员列表 | 无 |

**传感器上传数据格式示例：**

```json
{
  "user_id": 1,
  "heart_rate": 75,
  "sleep_hours": 7.5,
  "steps": 8000,
  "temperature": 36.5,
  "room_temp": 24.0,
  "humidity": 55.0,
  "co2_level": 600
}
```

---

## 常见问题

**Q: 启动时报 `ModuleNotFoundError`？**

确保已激活虚拟环境并安装所有依赖：
```bash
venv\Scripts\activate.bat
pip install -r requirements.txt
```

**Q: 数据库连接失败？**

检查 MySQL 服务是否启动，以及 `app.py` 中的数据库用户名、密码、库名是否正确。首次运行会自动创建数据表。

**Q: AI 分析功能无响应？**

确认 `.env` 文件中已填写有效的 `DEEPSEEK_API_KEY`，并检查网络能否访问 `api.deepseek.com`。

**Q: PDF 导出失败（Windows）？**

WeasyPrint 在 Windows 上需要安装 GTK 运行时，参考[官方安装文档](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows)。

**Q: 如何重新训练 AI 模型？**

```bash
python utils/generate_data.py   # 生成训练数据
python utils/train_model.py     # 训练并保存 health_model.pkl
```

**Q: 如何以 EXE 形式打包？**

确保已构建前端（`npm run build`），然后运行：
```bash
build_all.bat
```
打包产物在 `dist/HealthAI智慧舱/` 目录下。

---

## 贡献指南

欢迎通过 Issue 或 Pull Request 参与贡献。

1. Fork 本仓库
2. 基于 `master` 创建功能分支：`git checkout -b feat/your-feature`
3. 提交变更：`git commit -m "feat: 描述你的改动"`
4. 推送分支：`git push origin feat/your-feature`
5. 提交 Pull Request，并在描述中说明改动目的

**代码规范：**
- Python 遵循 PEP 8
- Vue 组件使用 `<script setup>` 语法
- API 接口统一返回 `{"code": 200, "data": ..., "msg": ...}` 格式

---

## 许可证

本项目基于 [MIT License](LICENSE) 开源，允许自由使用、修改和分发，但需保留原始版权声明。

---

> 本系统为学术研究项目，AI 分析结果仅供参考，不构成医疗诊断建议。如有健康问题请及时就医。
