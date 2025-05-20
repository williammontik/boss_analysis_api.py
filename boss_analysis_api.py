import os, re, smtplib, random, logging, json
from datetime import datetime
from dateutil import parser
from email.mime.text import MIMEText
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.DEBUG)

# OpenAI setup
key = os.getenv("OPENAI_API_KEY")
if not key:
    raise RuntimeError("OPENAI_API_KEY not set")
client = OpenAI(api_key=key)

# SMTP setup
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT   = 587
SMTP_USER   = "kata.chatbot@gmail.com"
SMTP_PASS   = os.getenv("SMTP_PASSWORD")

def send_email(html):
    msg = MIMEText(html, 'html')
    msg["Subject"] = "New Boss Submission"
    msg["From"]    = SMTP_USER
    msg["To"]      = SMTP_USER
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
    except Exception:
        app.logger.error("Email failed", exc_info=True)

@app.route("/boss_analyze", methods=["POST"])
def boss_analyze():
    data = request.get_json(force=True)
    lang = data.get("lang", "en").lower()   # must be "zh"

    # parse DOB & compute age (same as children code)…
    # … omitted here …

    # build prompt exactly like children /en-analyze
    if lang == "zh":
        prompt = f"""
请用简体中文生成一份详细的职场绩效报告，面向以下人员：
- 姓名：{data.get('memberName')}
- 职位：{data.get('position')}
- 部门：{data.get('department')}
- 年限：{data.get('experience')}年
- 行业：{data.get('sector')}
- 地区：{data.get('country')}
- 主要挑战：{data.get('challenge')}
- 关注点：{data.get('focus')}
要求：
1. 只给出百分比数据
2. 用 Markdown 语法给出 3 个“柱状图”示例
3. 对比区域/全球趋势
4. 突出 3 个关键发现
5. 不要个性化建议
6. 学术风格
"""
    elif lang == "tw":
        # Traditional Chinese prompt (same style)
        prompt = "…繁體中文版本…"
    else:
        # English prompt
        prompt = "…English version…"

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role":"user","content":prompt}]
    )
    raw = response.choices[0].message.content
    analysis = re.sub(r"<[^>]+>", "", raw).strip()

    # generate random metrics (same as children)
    metrics = [
        {
            "title": "Communication Efficiency",
            "labels": ["Individual","Regional Avg","Global Avg"],
            "values": [random.randint(60,90), random.randint(55,85), random.randint(60,88)]
        },
        # … two more …
    ]

    # build & send email HTML (mirror children build_email_html)
    html_body = build_email_html(metrics, analysis, data, age, lang)
    send_email(html_body)

    return jsonify(metrics=metrics, analysis=analysis)

# … include build_email_html exactly as in children code but with Chinese footer …

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
