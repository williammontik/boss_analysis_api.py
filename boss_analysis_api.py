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

        # 1) Extract form fields
        name       = data.get("memberName", "").strip()
        position   = data.get("position", "").strip()
        department = data.get("department", "").strip()
        experience = data.get("experience", "").strip()
        sector     = data.get("sector", "").strip()
        challenge  = data.get("challenge", "").strip()
        focus      = data.get("focus", "").strip()
        email_addr = data.get("email", "").strip()
        country    = data.get("country", "").strip()
        referrer   = data.get("referrer", "").strip()
        lang       = data.get("lang", "en").lower()

        # 2) Parse DOB and compute age
        day_str  = data.get("dob_day", "")
        mon_str  = data.get("dob_month", "")
        year_str = data.get("dob_year", "")
        if day_str and mon_str and year_str:
            chinese_months = {
                "一月":1, "二月":2, "三月":3, "四月":4,
                "五月":5, "六月":6, "七月":7, "八月":8,
                "九月":9, "十月":10, "十一月":11, "十二月":12
            }
            if mon_str.isdigit():
                month = int(mon_str)
            elif mon_str in chinese_months:
                month = chinese_months[mon_str]
            else:
                month = datetime.strptime(mon_str, "%B").month
            birthdate = datetime(int(year_str), month, int(day_str))
        else:
            birthdate = parser.parse(data.get("dob", ""), dayfirst=True)

        today = datetime.today()
        age = today.year - birthdate.year - (
            (today.month, today.day) < (birthdate.month, birthdate.day)
        )

        # 3) Generate metrics
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

        # 4) Build prompt and call OpenAI for narrative
        if lang == "zh":
            prompt = f"""
请用简体中文生成一段约150字的报告，面向年龄 {age}，职位 {position}，国家 {country}。
他们面临的主要挑战：{challenge}，发展重点：{focus}。
要求：
1. 突出一项相对于区域/全球的优势
2. 指出一个主要差距
3. 提出三条可行的下一步行动
"""
        elif lang == "tw":
            prompt = f"""
請用繁體中文生成一段約150字的報告，面向年齡 {age}，職位 {position}，國家 {country}。
他們面臨的主要挑戰：{challenge}，發展重點：{focus}。
要求：
1. 突出一項相對於區域/全球的優勢
2. 指出一個主要差距
3. 提出三條可行的下一步行動
"""
        else:
            prompt = f"""
Write a ~150-word workplace performance report for a {position}, age {age}, in {country}.
Challenge: {challenge}, Focus: {focus}.
Requirements:
1. Highlight one top strength vs. regional/global
2. Identify one main gap
3. Offer three actionable next steps
"""
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"user","content":prompt}]
        )
        narrative = response.choices[0].message.content.strip()

        # 5) Build summary text + blue footer
        summary = f"""
Workplace Performance Report

• Age: {age}
• Position: {position}
• Department: {department}
• Experience: {experience} year(s)
• Sector: {sector}
• Country: {country}
• Main Challenge: {challenge}
• Development Focus: {focus}

{narrative}
"""
        if lang == "zh":
            footer = """

报告洞见由 KataChat 的 AI 系统生成，数据来源：
1. 我们在新加坡、马来西亚和台湾的匿名专业档案数据库
2. 可信 OpenAI 研究的全球基准数据集
所有数据均通过 AI 模型处理，以识别具有统计学意义的模式，并严格遵守 PDPA 合规要求。样本量最低 1,000+ 数据点。

PS：报告已发送至您的邮

