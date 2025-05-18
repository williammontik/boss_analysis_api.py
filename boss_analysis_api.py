import os
import re
import smtplib
import random
import logging
from datetime import datetime
from dateutil import parser
from email.mime.text import MIMEText
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import json

# ── Flask Setup ─────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.DEBUG)

# ── OpenAI Client ────────────────────────────────────────────────────────────
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise RuntimeError("OPENAI_API_KEY environment variable is not set.")
client = OpenAI(api_key=openai_api_key)

# ── SMTP Setup ───────────────────────────────────────────────────────────────
SMTP_SERVER   = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USERNAME = "kata.chatbot@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
if not SMTP_PASSWORD:
    app.logger.warning("SMTP_PASSWORD is not set; emails may fail.")

def send_email(html_body: str):
    """
    Sends an HTML email to kata.chatbot@gmail.com.
    """
    msg = MIMEText(html_body, 'html')
    msg["Subject"] = "New KataChatBot Submission"
    msg["From"]    = SMTP_USERNAME
    msg["To"]      = SMTP_USERNAME

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        app.logger.info("✅ HTML email sent successfully.")
    except Exception:
        app.logger.error("❌ Email sending failed.", exc_info=True)


# ── Chinese month name mapping ────────────────────────────────────────────────
CHINESE_MONTHS = {
    "一月":1, "二月":2, "三月":3, "四月":4,
    "五月":5, "六月":6, "七月":7, "八月":8,
    "九月":9, "十月":10, "十一月":11, "十二月":12
}

def safe_json_parse(raw: str):
    """
    Extract first {...} block from raw string and parse it.
    """
    start = raw.find('{')
    end = raw.rfind('}')
    if start == -1 or end == -1:
        raise ValueError("No JSON object found in response")
    return json.loads(raw[start:end+1])


# ── /analyze_name Endpoint (Children) ─────────────────────────────────────────
@app.route("/analyze_name", methods=["POST"])
def analyze_name():
    data = request.get_json(force=True)
    try:
        app.logger.info(f"[analyze_name] payload: {data}")

        # 1) Collect fields
        name         = data.get("name", "").strip()
        chinese_name = data.get("chinese_name", "").strip()
        gender       = data.get("gender", "").strip()
        phone        = data.get("phone", "").strip()
        email_addr   = data.get("email", "").strip()
        country      = data.get("country", "").strip()
        referrer     = data.get("referrer", "").strip()
        lang         = data.get("lang", "en").lower()

        # 2) Parse DOB
        day_str   = data.get("dob_day")
        mon_str   = data.get("dob_month")
        year_str  = data.get("dob_year")
        if day_str and mon_str and year_str:
            if mon_str.isdigit():
                month = int(mon_str)
            elif mon_str in CHINESE_MONTHS:
                month = CHINESE_MONTHS[mon_str]
            else:
                month = datetime.strptime(mon_str, "%B").month
            birthdate = datetime(int(year_str), month, int(day_str))
        else:
            birthdate = parser.parse(data.get("dob", ""), dayfirst=True)

        # compute age
        today = datetime.today()
        age = today.year - birthdate.year - (
            (today.month, today.day) < (birthdate.month, birthdate.day)
        )
        app.logger.debug(f"Computed birthdate={birthdate.date()}, age={age}")

        # 3) Build prompt based on lang
        if lang == "zh":
            prompt = f"""
请用简体中文生成一份学习模式统计报告，面向年龄 {age}、性别 {gender}、地区 {country} 的孩子。
要求：
1. 只给出百分比数据
2. 在文本中用 Markdown 语法给出 3 个“柱状图”示例
3. 对比区域/全球趋势
4. 突出 3 个关键发现
5. 不要个性化建议
6. 学术风格
"""
        elif lang == "tw":
            prompt = f"""
請用繁體中文生成一份學習模式統計報告，面向年齡 {age}、性別 {gender}、地區 {country} 的孩子。
要求：
1. 只給出百分比數據
2. 在文本中用 Markdown 语法给出 3 個「柱狀圖」示例
3. 比較區域／全球趨勢
4. 突出 3 個關鍵發現
5. 不要個性化建議
6. 學術風格
"""
        else:
            prompt = f"""
Generate a statistical report on learning patterns for children aged {age}, gender {gender}, in {country}.
Requirements:
1. Only factual percentages
2. Include 3 markdown bar‐charts
3. Compare regional/global
4. Highlight 3 key findings
5. No personalized advice
6. Academic style
"""

        # 4) Call OpenAI and strip HTML tags
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        analysis = re.sub(r"<[^>]+>", "", response.choices[0].message.content)

        # 5) Generate metrics
        base_improve  = random.randint(65, 80)
        base_struggle = random.randint(30, 45)
        if base_struggle >= base_improve - 5:
            base_struggle = base_improve - random.randint(10, 15)
        improved_percent  = round(base_improve / 5) * 5
        struggle_percent  = round(base_struggle / 5) * 5

        if lang == "en":
            titles = ["Learning Preferences", "Study Habits", "Math Performance"]
            labels = [
                ["Visual","Auditory","Kinesthetic"],
                ["Regular Study","Group Study","Solo Study"],
                ["Algebra","Geometry"]
            ]
        elif lang == "zh":
            titles = ["学习偏好", "学习习惯", "数学表现"]
            labels = [
                ["视觉","听觉","动手"],
                ["定期学习","小组学习","独自学习"],
                ["代数","几何"]
            ]
        else:
            titles = ["學習偏好", "學習習慣", "數學表現"]
            labels = [
                ["視覺","聽覺","動手"],
                ["定期學習","小組學習","獨自學習"],
                ["代數","幾何"]
            ]

        metrics = [
            {"title": titles[0], "labels": labels[0],
             "values": [improved_percent, struggle_percent, 100 - improved_percent - struggle_percent]},
            {"title": titles[1], "labels": labels[1], "values": [70,30,60]},
            {"title": titles[2], "labels": labels[2], "values": [improved_percent,70]}
        ]

        # 6) Build email HTML (omitted for brevity)...
        #    <same as above>

        # 7) Send HTML email
        #    send_email(email_html)

        # 8) Return JSON response
        return jsonify({"metrics": metrics, "analysis": analysis})

    except Exception as e:
        app.logger.exception("Error in /analyze_name")
        return jsonify({"error": str(e)}), 500


# ── /boss_analyze Endpoint (Managers) ─────────────────────────────────────────
@app.route("/boss_analyze", methods=["POST"])
def boss_analyze():
    try:
        data = request.get_json(force=True)
        app.logger.info(f"[boss_analyze] payload: {data}")

        # 1) Extract form fields
        name        = data.get("memberName", "").strip()
        position    = data.get("position", "").strip()
        department  = data.get("department", "").strip()
        experience  = data.get("experience", "").strip()
        sector      = data.get("sector", "").strip()
        challenge   = data.get("challenge", "").strip()
        focus       = data.get("focus", "").strip()
        email_addr  = data.get("email", "").strip()
        country     = data.get("country", "").strip()
        referrer    = data.get("referrer", "").strip()
        contact_num = data.get("contactNumber", "").strip()
        lang        = data.get("lang", "en").lower()

        # 2) Parse DOB & compute age
        day_str  = data.get("dob_day")
        mon_str  = data.get("dob_month")
        year_str = data.get("dob_year")
        if day_str and mon_str and year_str:
            if mon_str.isdigit():
                month = int(mon_str)
            elif mon_str in CHINESE_MONTHS:
                month = CHINESE_MONTHS[mon_str]
            else:
                month = datetime.strptime(mon_str, "%B").month
            birthdate = datetime(int(year_str), month, int(day_str))
        else:
            birthdate = parser.parse(data.get("dob", ""), dayfirst=True)

        today = datetime.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))

        # 3) Generate three random metrics
        def random_metric(title):
            return {
                "title": title,
                "labels": ["Segment", "Regional", "Global"],
                "values": [
                    random.randint(60, 90),
                    random.randint(55, 85),
                    random.randint(60, 88)
                ]
            }
        metrics = [
            random_metric("Communication Efficiency"),
            random_metric("Leadership Readiness"),
            random_metric("Task Completion Reliability")
        ]

        # 4) Build language-specific prompt
        if lang == "zh":
            prompt = f"""
请以专业组织心理学家视角，用简体中文为名为\"{name}\"的员工生成详细绩效报告。
要求：
1. JSON 输出三项指标，每项包含 'Segment','Regional','Global'
2. narrative 使用简体中文，150-200 字，突出优势、差距，并给出三项可行步骤
"""
        elif lang == "tw":
            prompt = f"""
請以專業組織心理學家視角，用繁體中文為名為\"{name}\"的員工生成詳細績效報告。
要求：
1. JSON 輸出三項指標，每項包含 'Segment','Regional','Global'
2. narrative 使用繁體中文，150-200 字，突出優勢、差距，並給出三項可行步驟
"""
        else:
            prompt = f"""
You are an expert organizational psychologist. Generate a detailed performance report for \"{name}\".
Requirements:
1. Return JSON with three metrics comparing Segment/Regional/Global.
2. Provide a 150-200 word narrative in English highlighting strengths, gaps, and three actionable steps.
"""

        # 5) Call OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.choices[0].message.content.strip()
        report = safe_json_parse(raw)   # <--- use safe parser here

        # 6) Return JSON directly
        return jsonify(report)

    except Exception as e:
        app.logger.exception("Error in /boss_analyze")
        return jsonify({"error": str(e)}), 500


# ── Run Locally ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
