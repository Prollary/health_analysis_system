import os
import requests
import json
import qianfan
from dotenv import load_dotenv

load_dotenv()  # 加载.env

# 基于环境和人体数据的大模型分析
def get_cloud_ai_advice(heart_rate, sleep, steps, room_temp, co2):
    """
    调用百度文心一言获取深度分析
    """
    # 自动读取环境变量 QIANFAN_AK 和 QIANFAN_SK
    chat_comp = qianfan.ChatCompletion()
    
    prompt = f"""
    你是智慧家居健康助手。请分析以下数据并给出100字以内的建议：
    1. 生理：心率{heart_rate}bpm, 睡眠{sleep}h, 步数{steps}。
    2. 环境：室温{room_temp}℃, CO2浓度{co2}ppm。
    请结合环境对生理的影响（如高CO2对疲劳的影响）给出专业指导。
    """
    
    try:
        resp = chat_comp.do(model="ERNIE-Speed-8K", messages=[{"role": "user", "content": prompt}])
        return resp.body['result']
    except Exception as e:
        return f"云端诊断服务暂时不可用 ({str(e)})"


# 基于千帆大模型的健康日记 NLP 解析
def parse_health_diary(diary_text):
    """提取大白话日记中的症状并给出建议"""
    # Qianfan SDK 会自动读取环境变量中的 QIANFAN_AK 和 QIANFAN_SK
    chat_comp = qianfan.ChatCompletion()
    
    prompt = f"""
    你是一个专业的全科医生。请分析以下老年人使用口语描述的健康日记：
    "{diary_text}"
    请执行以下两个任务：
    1. 提取其中的【症状实体】（如果没有症状，输出“无异常”）。
    2. 给出初步的【家庭就医建议】。
    
    请严格按照以下 JSON 格式返回，不要包含其他多余字符：
    {{"symptoms": "症状A, 症状B", "advice": "您的建议内容..."}}
    """
    
    try:
        resp = chat_comp.do(model="ERNIE-Bot-4", messages=[{"role": "user", "content": prompt}])
        result_str = resp.body['result']
        # 清理可能带有的 markdown 标记并解析 JSON
        clean_json_str = result_str.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json_str)
    except Exception as e:
        return {"symptoms": "解析失败", "advice": f"云端 NLP 服务异常: {str(e)}"}


# 百度人脸识别与疲劳度评估
def get_vision_access_token():
    """获取百度视觉 API 的 Access Token"""
    ak = os.getenv('BAIDU_VISION_AK')
    sk = os.getenv('BAIDU_VISION_SK')
    url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={ak}&client_secret={sk}"
    response = requests.post(url).json()
    return response.get("access_token")

def analyze_face_emotion(base64_image):
    """
    调用百度人脸识别 API，返回面部情绪
    """
    token = get_vision_access_token()
    if not token:
        return {"status": "error", "message": "无法获取百度 API Token"}

    url = f"https://aip.baidubce.com/rest/2.0/face/v3/detect?access_token={token}"
    payload = {
        "image": base64_image,
        "image_type": "BASE64",
        "face_field": "emotion,age,expression" # 请求返回情绪、年龄、表情数据
    }
    headers = {'Content-Type': 'application/json'}
    
    response = requests.post(url, headers=headers, data=json.dumps(payload)).json()
    
    if response.get("error_code") == 0:
        face_list = response["result"]["face_list"][0]
        # 百度情绪映射字典 (简化版)
        emotion_map = {
            "angry": "愤怒", "disgust": "厌恶", "fear": "恐惧", 
            "happy": "高兴", "sad": "悲伤", "surprise": "惊讶", "neutral": "平静", "pouty": "撅嘴", "grimace": "鬼脸"
        }
        en_emotion = face_list["emotion"]["type"]
        return {"status": "success", "emotion": emotion_map.get(en_emotion, en_emotion)}
    else:
        return {"status": "error", "message": response.get("error_msg")}



def generate_detailed_intervention(user_profile, analysis_data):
    """
    根据用户画像（年龄、性别、风险等级）生成 1000 字以上的深度干预方案
    """
    chat_comp = qianfan.ChatCompletion()
    
    prompt = f"""
    你是一位资深的临床营养师和运动康复专家。请为以下用户定制一份详尽的【健康干预方案】。
    
    用户画像：年龄{user_profile['age']}岁，性别{user_profile['gender']}，当前健康风险等级：{analysis_data['risk_level']}。
    最新指标：心率{analysis_data['heart_rate']}bpm，睡眠{analysis_data['sleep']}h，步数{analysis_data['steps']}。
    
    请严格按以下要求生成内容：
    1. 【个性化饮食推荐】：要求内容包含“为什么要吃这个食物”、“该怎么吃”、“含有哪些核心营养素”。纯文本的排版美观，详细列出3-5条，，不得重复，不得出现输入的话，输出的内容要求是全新的，不少于 500 中文字符，最好以表格美化形式表现。
    2. 【定制化运动处方】：要求内容包含“为什么做这个运动”、“该怎么做”、“对身体的具体好处”。纯文本的排版美观，详细列出3-5条，不得重复，不得出现输入的话，输出的内容要求是全新的，不少于 500 中文字符，最好以表格美化形式表现。
    3. 语气要专业且富有亲和力，使用结构化的 Markdown 标题。
    4. 最开始生成的体检表格要求排版美观，专业。
    """
    
    try:
        resp = chat_comp.do(model="ERNIE-Bot-4", messages=[{"role": "user", "content": prompt}])
        return resp.body['result']
    except Exception as e:
        return f"干预方案生成失败: {str(e)}"