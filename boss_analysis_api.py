```python
# boss_analysis_api.py
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
    msg["Subject"] = "New Boss Submission"
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

# ── /boss_analyze Endpoint (Managers) ─────────────────────────────────────────
@app.route("/boss_analyze", methods=["POST"])
def boss_analyze():
    try:
        data = request.get_json(force=True)
        app.logger.info(f"[boss_analyze] payload: {data}")

        # extract common fields
        memberName = data.get("memberName", "")
        position   = data.get("position", "")
        department = data.get("department", "")
        experience = data.get("experience", "")
        sector     = data.get("sector", "")
        challenge  = data.get("challenge", "")
        focus      = data.get("focus", "")
        email_addr = data.get("email", "")
        country    = data.get("country", "")
        referrer   = data.get("referrer", "")
        lang       = data.get("lang", "en").lower()

        # parse DOB
        day_str  = data.get("dob_day")
        mon_str  = data.get("dob_month")
        year_str = data.get("dob_year")
        if day_str and mon_str and year_str:
            if mon_str.isdigit():
                month = int(mon_str)
            else:
                try:
                    month = datetime.strptime(mon_str, "%B").month
                except:
                    chinese_months = {"一月":1, "二月":2, "三月":3, "四月":4,
                                      "五月":5, "六月":6, "七月":7, "八月":8,
                                      "九月":9, "十月":10, "十一月":11, "十二月":12}
                    month = chinese_months.get(mon_str, 1)
            birthdate = datetime(int(year_str), month, int(day_str))
        else:
            birthdate = parser.parse(data.get("dob", ""), dayfirst=True)
        # compute age
        today = datetime.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))

        # build prompt based on lang
        if lang == "zh":
            prompt = f"""
请用简体中文生成一份详细的职场绩效报告，面向以下人员：
- 姓名：{memberName}
- 职位：{position}
- 部门：{department}
- 年限：{experience}年
- 行业：{sector}
- 地区：{country}
- 主要挑战：{challenge}
- 关注点：{focus}
要求：
1. 返回三个 JSON 格式的柱状图指标，每个包含"title","labels","values"；
2. narrative 字段提供 150-200 字分析：突出优劣势并给出三条可执行建议；
3. 返回单个 JSON 对象，键为 "metrics" 和 "analysis"。
"""
        elif lang == "tw":
            prompt = f"""
請用繁體中文生成一份詳細的職場績效報告，面向以下人員：
- 姓名：{memberName}
- 職位：{position}
- 部門：{department}
- 年限：{experience}年
- 行業：{sector}
- 地區：{country}
- 主要挑戰：{challenge}
- 關注點：{focus}
要求：
1. 返回三個 JSON 格式的柱狀圖指標，每個包含"title","labels","values"；
2. narrative 欄位提供 150-200 字分析：突出優劣勢並給出三條可執行建議；
3. 返回單個 JSON 對象，鍵為 "metrics" 和 "analysis"。
"""
        else:
            prompt = f"""
You are an organizational psychologist. Generate a detailed performance report for:
- Name: {memberName}
- Position: {position}
- Department: {department}
- Experience: {experience} years
- Sector: {sector}
- Country: {country}
- Key Challenge: {challenge}
- Focus: {focus}
Requirements:
1. Return exactly three bar-chart metrics in JSON (title, labels, values);
2. Provide a 150-200 word narrative in "analysis" with strengths, gaps, and three actionable steps;
3. Return a single JSON object with "metrics" and "analysis".
"""

        # call OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.choices[0].message.content.strip()
        # load JSON
        report = json.loads(raw)

        # send email
        # build HTML body as before using report and inline charts if needed
        send_email(html_body=build_email_html(report, data, age, lang))

        return jsonify(report)

    except Exception as e:
        app.logger.exception("Error in /boss_analyze")
        return jsonify({"error": str(e)}), 500

# helper to construct email HTML (omitted for brevity, mirror children logic)
def build_email_html(report, data, age, lang):
    # assemble HTML similar to children endpoint, using report['metrics'] and report['analysis']
    return "<html><body>...formatted report...</body></html>"

# ── Run Locally ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
```
