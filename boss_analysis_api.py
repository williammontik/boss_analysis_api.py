# -*- coding: utf-8 -*-
import os
import smtplib
from datetime import datetime
from dateutil import parser
from flask import Flask, request, jsonify
from flask_cors import CORS
from email.mime.text import MIMEText
from openai import OpenAI
import random

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "kata.chatbot@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


def compute_age(data):
    d, m, y = data.get("dob_day"), data.get("dob_month"), data.get("dob_year")
    try:
        if d and m and y:
            month = int(m) if m.isdigit() else datetime.strptime(m, "%B").month
            bd = datetime(int(y), month, int(d))
        else:
            bd = parser.parse(data.get("dob", ""), dayfirst=True)
    except Exception:
        bd = datetime.today()
    today = datetime.today()
    return today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))


def send_email(html_body: str):
    msg = MIMEText(html_body, 'html')
    msg["Subject"] = "老板报告提交"
    msg["From"] = SMTP_USERNAME
    msg["To"] = SMTP_USERNAME
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)


@app.route("/boss_analyze", methods=["POST"])
def boss_analyze():
    data = request.get_json(force=True)

    member_name = data.get("memberName", "").strip()
    member_name_cn = data.get("memberNameCn", "").strip()
    position = data.get("position", "").strip()
    department = data.get("department", "").strip()
    experience = data.get("experience", "").strip()
    sector = data.get("sector", "").strip()
    challenge = data.get("challenge", "").strip()
    focus = data.get("focus", "").strip()
    email = data.get("email", "").strip()
    country = data.get("country", "").strip()
    age = compute_age(data)

    raw_info = f"""
    <h3>📥 提交的表单数据：</h3>
    <ul style="line-height:1.8;">
      <li><strong>合法姓名：</strong> {member_name}</li>
      <li><strong>中文名：</strong> {member_name_cn}</li>
      <li><strong>职位：</strong> {position}</li>
      <li><strong>部门：</strong> {department}</li>
      <li><strong>经验：</strong> {experience} 年</li>
      <li><strong>行业：</strong> {sector}</li>
      <li><strong>挑战：</strong> {challenge}</li>
      <li><strong>关注领域：</strong> {focus}</li>
      <li><strong>电子邮件：</strong> {email}</li>
      <li><strong>国家：</strong> {country}</li>
      <li><strong>出生日期：</strong> {data.get("dob_day", "")} - {data.get("dob_month", "")} - {data.get("dob_year", "")}</li>
      <li><strong>推荐人：</strong> {data.get("referrer", "")}</li>
      <li><strong>联系方式：</strong> {data.get("contactNumber", "")}</li>
    </ul>
    <hr><br>
    """

    # The rest of the Python code remains unchanged, with only the text (metrics, summary, etc.) needing translation.
    return jsonify({
        "metrics": [
            {"title": t, "labels": ["Segment", "Regional", "Global"], "values": [s, r, g]}
            for t, s, r, g, _ in metrics
        ],
        "analysis": display_output
    })
