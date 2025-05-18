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

def send_email(html_body: str, subject: str):
    """
    Sends an HTML email containing the submission/report.
    """
    msg = MIMEText(html_body, 'html')
    msg["Subject"] = subject
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


# ── /analyze_name Endpoint (Children) ─────────────────────────────────────────
@app.route("/analyze_name", methods=["POST"])
def analyze_name():
    data = request.get_json(force=True)
    try:
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

        # 3) Build prompt based on lang
        if lang == "zh":
            user_prompt = f"""
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
            user_prompt = f"""
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
            user_prompt = f"""
Generate a statistical report on learning patterns for children aged {age}, gender {gender}, in {country}.
Requirements:
1. Only factual percentages
2. Include 3 markdown bar‐charts
3. Compare regional/global
4. Highlight 3 key findings
5. No personalized advice
6. Academic style
"""

        # 4) Call OpenAI with system instruction to output only JSON
        messages = [
            {"role": "system", "content": "You will output exactly one JSON object with keys \"metrics\" and \"analysis\" and nothing else."},
            {"role": "user", "content": user_prompt}
        ]
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        raw = resp.choices[0].message.content.strip()
        result = json.loads(raw)  # now safe

        # 5) (Optional) send email of submission + report
        # send_email(...)

        return jsonify(result)

    except Exception as e:
        app.logger.exception("Error in /analyze_name")
        return jsonify({"error": str(e)}), 500


# ── /boss_analyze Endpoint (Managers) ─────────────────────────────────────────
@app.route("/boss_analyze", methods=["POST"])
def boss_analyze():
    try:
        data = request.get_json(force=True)

        # 1) Extract fields
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

        today = datetime.today()
        age = today.year - birthdate.year - (
            (today.month, today.day) < (birthdate.month, birthdate.day)
        )

        # 3) Build prompt based on lang
        if lang == "zh":
            user_prompt = f"""
请以专业组织心理学家视角，用简体中文为名为\"{name}\"的员工生成详细绩效报告。
要求：
1. JSON 输出三项指标，每项包含 'Segment','Regional','Global'
2. narrative 使用简体中文，150-200 字，突出优势、差距，并给出三项可行步骤
"""
        elif lang == "tw":
            user_prompt = f"""
請以專業組織心理學家視角，用繁體中文為名為\"{name}\"的員工生成詳細績效報告。
要求：
1. JSON 輸出三項指標，每項包含 'Segment','Regional','Global'
2. narrative 使用繁體中文，150-200 字，突出優勢、差距，並給出三項可行步驟
"""
        else:
            user_prompt = f"""
You are an expert organizational psychologist. Generate a detailed performance report for \"{name}\".
Requirements:
1. Return a JSON object with three metrics comparing Segment/Regional/Global.
2. Provide a 150-200 word narrative in English highlighting strengths, gaps, and three actionable steps.
"""

        # 4) Call OpenAI with system instruction to output only JSON
        messages = [
            {"role": "system", "content": "You will output exactly one JSON object with keys \"metrics\" and \"analysis\" and nothing else."},
            {"role": "user", "content": user_prompt}
        ]
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        raw = resp.choices[0].message.content.strip()
        report = json.loads(raw)  # now safe

        # 5) (Optional) send email of submission + report
        # send_email(...)

        return jsonify(report)

    except Exception as e:
        app.logger.exception("Error in /boss_analyze")
        return jsonify({"error": str(e)}), 500


# ── Run Locally ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
