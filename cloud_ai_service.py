import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# DeepSeek 客户端（兼容 OpenAI SDK）
def _client():
    return OpenAI(
        api_key=os.getenv('DEEPSEEK_API_KEY'),
        base_url='https://api.deepseek.com'
    )

def _chat(messages, model='deepseek-chat', **kwargs):
    """统一调用入口，返回字符串结果"""
    client = _client()
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        **kwargs
    )
    return resp.choices[0].message.content


# ==================== 1. 健康综合建议 ====================
def get_cloud_ai_advice(heart_rate, sleep, steps, room_temp, co2):
    """
    调用 DeepSeek 获取环境-生理联动深度分析（100字以内简报）
    """
    prompt = f"""你是智慧家居健康助手。请分析以下数据并给出100字以内的专业建议：
生理指标：心率 {heart_rate} bpm，睡眠 {sleep} h，步数 {steps} 步。
环境指标：室温 {room_temp} ℃，CO2浓度 {co2} ppm。
请结合环境对生理的影响（如高CO2对疲劳的影响、室温对睡眠质量的影响）给出专业指导。"""

    try:
        return _chat([{"role": "user", "content": prompt}])
    except Exception as e:
        return f"云端诊断服务暂时不可用 ({e})"


# ==================== 2. 健康日记 NLP 解析 ====================
def parse_health_diary(diary_text):
    """
    调用 DeepSeek 提取口语化日记中的症状实体并给出就医建议
    """
    prompt = f"""你是一位专业的全科医生。请分析以下老年人使用口语描述的健康日记：
"{diary_text}"

请执行以下两个任务：
1. 提取其中的【症状实体】（若无症状，输出"无异常"）。
2. 给出初步的【家庭就医建议】。

请严格按以下 JSON 格式返回，不要包含其他多余字符：
{{"symptoms": "症状A, 症状B", "advice": "您的建议内容..."}}"""

    try:
        result_str = _chat(
            [{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(result_str)
    except json.JSONDecodeError:
        # 若模型未严格返回 JSON，做一次容错清洗
        try:
            clean = result_str.replace('```json', '').replace('```', '').strip()
            return json.loads(clean)
        except Exception:
            return {"symptoms": "解析失败", "advice": "请重新提交日记内容"}
    except Exception as e:
        return {"symptoms": "解析失败", "advice": f"AI 服务异常: {e}"}


# ==================== 3. 智能镜子·情绪识别 ====================
def analyze_face_emotion(base64_image):
    """
    调用 DeepSeek 视觉能力分析面部情绪（替代百度人脸识别 API）
    返回格式：{"status": "success", "emotion": "高兴"}
    """
    prompt = """请分析这张人脸照片中人物的面部情绪状态。
只从以下选项中选择一个最贴切的情绪词：高兴、悲伤、愤怒、厌恶、恐惧、惊讶、平静、困惑、疲惫。
请严格按以下 JSON 格式返回，不要包含其他多余字符：
{"emotion": "情绪词"}"""

    try:
        result_str = _chat(
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }],
            model='deepseek-chat'
        )
        data = json.loads(result_str.replace('```json', '').replace('```', '').strip())
        return {"status": "success", "emotion": data.get("emotion", "平静")}
    except Exception as e:
        return {"status": "error", "message": f"情绪识别失败: {e}"}


# ==================== 4. 深度干预方案生成 ====================
def generate_detailed_intervention(user_profile, analysis_data):
    """
    根据用户画像（年龄、性别、风险等级）调用 DeepSeek 生成 1000 字以上深度干预方案
    """
    age    = user_profile.get('age', '未知')
    gender = user_profile.get('gender', '未知')
    risk   = analysis_data.get('risk_level', '中风险')
    hr     = analysis_data.get('heart_rate', '--')
    sleep  = analysis_data.get('sleep', '--')
    steps  = analysis_data.get('steps', '--')

    prompt = f"""你是一位资深的临床营养师和运动康复专家。请为以下用户定制一份详尽的【健康干预方案】。

用户画像：年龄 {age} 岁，性别 {gender}，当前健康风险等级：{risk}。
最新指标：心率 {hr} bpm，睡眠 {sleep} h，步数 {steps} 步。

请严格按以下要求生成内容：

## 【个性化饮食推荐】
- 结合用户年龄、性别、风险等级给出具体食物清单
- 每种食物说明：为什么要吃、该怎么吃、含有哪些核心营养素
- 字数不少于 500 中文字符

## 【定制化运动处方】
- 结合用户体征数据推荐适合的运动类型
- 每种运动说明：为什么做、该怎么做、具体时长与强度、对身体的好处
- 字数不少于 500 中文字符

语气专业且富有亲和力，使用 Markdown 结构化排版。"""

    try:
        return _chat(
            [{"role": "user", "content": prompt}],
            max_tokens=4096
        )
    except Exception as e:
        return f"干预方案生成失败: {e}"
