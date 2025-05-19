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
    Sends an HTML email containing the submission and report.
    """
    subject = "New Boss Submission"
    msg = MIMEText(html_body, 'html')
    msg["Subject"] = subject
    msg["From"]    = SMTP_USERNAME
    msg["To"]      = SMTP_USERNAME

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        app.logger.info("✅ Email sent successfully.")
    except Exception:
        app.logger.error("❌ Email sending failed.", exc_info=True)


# ── Chinese month name mapping ────────────────────────────────────────────────
CHINESE_MONTHS = {
    "一月":1, "二月":2, "三月":3, "四月":4,
    "五月":5, "六月":6, "七月":7, "八月":8,
    "九月":9, "十月":10, "十一月":11, "十二月":12
}


# ── /boss_analyze Endpoint (Managers) ─────────────────────────────────────────
@app.route("/boss_analyze", methods=["POST"])
def boss_analyze():
    data = request.get_json(force=True)
    try:
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

        # 3) Build language-specific prompt for narrative
        if lang == "zh":
            prompt = f"""
请用简体中文生成一份针对“{name}”（年龄 {age}，职位 {position}，行业 {sector}）的绩效分析，面临关键挑战：“{challenge}”。重点：
1. 150–200 字分析
2. 突出三大优势与差距
3. 提出三条可行建议
4. 学术风格
"""
        elif lang == "tw":
            prompt = f"""
請用繁體中文生成一份針對「{name}」（年齡 {age}，職位 {position}，行業 {sector}）的績效分析，面臨關鍵挑戰：「{challenge}」。重點：
1. 150–200 字分析
2. 突出三大優勢與差距
3. 提出三條可行建議
4. 學術風格
"""
        else:
            prompt = f"""
Generate a 150–200 word performance analysis for "{name}" (age {age}, position {position}, sector {sector}) who faces the key challenge: "{challenge}". Requirements:
1. Highlight three strengths vs. region/global
2. Identify the biggest performance gap
3. Offer three actionable recommendations
4. Academic style only
"""

        # 4) Call OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"user","content":prompt}]
        )
        analysis = re.sub(r"<[^>]+>", "", response.choices[0].message.content).strip()

        # 5) Generate three random metrics
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

        # 6) (Optional) Send HTML email with results
        # html_body = build_your_html(name, position, analysis, metrics, ...)
        # send_email(html_body)

        # 7) Return JSON just like children endpoint
        return jsonify({
            "metrics": metrics,
            "analysis": analysis
        })

    except Exception as e:
        app.logger.exception("Error in /boss_analyze")
        return jsonify({"error": str(e)}), 500


# ── Run Locally ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
