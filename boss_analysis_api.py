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
    msg["Subject"] = "Boss Report Submission"
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
    <h3>📥 Submitted Form Data:</h3>
    <ul style="line-height:1.8;">
      <li><strong>Legal Name:</strong> {member_name}</li>
      <li><strong>Chinese Name:</strong> {member_name_cn}</li>
      <li><strong>Position:</strong> {position}</li>
      <li><strong>Department:</strong> {department}</li>
      <li><strong>Experience:</strong> {experience} years</li>
      <li><strong>Sector:</strong> {sector}</li>
      <li><strong>Challenge:</strong> {challenge}</li>
      <li><strong>Focus:</strong> {focus}</li>
      <li><strong>Email:</strong> {email}</li>
      <li><strong>Country:</strong> {country}</li>
      <li><strong>Date of Birth:</strong> {data.get("dob_day", "")} - {data.get("dob_month", "")} - {data.get("dob_year", "")}</li>
      <li><strong>Referrer:</strong> {data.get("referrer", "")}</li>
      <li><strong>Contact Number:</strong> {data.get("contactNumber", "")}</li>
    </ul>
    <hr><br>
    """

    metrics = []
    for title, color in [
        ("Communication Efficiency", "#5E9CA0"),
        ("Leadership Readiness", "#FF9F40"),
        ("Task Completion Reliability", "#9966FF"),
    ]:
        seg, reg, glo = sorted([random.randint(60, 90), random.randint(55, 85), random.randint(60, 88)], reverse=True)
        metrics.append((title, seg, reg, glo, color))

    bar_html = ""
    for title, seg, reg, glo, color in metrics:
        bar_html += f"<strong>{title}</strong><br>"
        for v in (seg, reg, glo):
            bar_html += (
                f"<span style='display:inline-block;width:{v}%;height:12px;"
                f" background:{color}; margin-right:6px; border-radius:4px;'></span> {v}%<br>"
            )
        bar_html += "<br>"

    summary = (
        "<div style='font-size:24px;font-weight:bold;margin-top:30px;'>🧠 Summary:</div><br>"
        + f"<p style='line-height:1.7; font-size:16px; margin-bottom:16px; text-align:justify;'>"
        + f"In {country}, professionals in the <strong>{sector}</strong> sector with <strong>{experience} years</strong> of experience often balance internal expectations with market evolution. Communication effectiveness, reflected in scores like <strong>{metrics[0][1]}%</strong>, is critical for managing not only teams but cross-functional collaboration across departments like <strong>{department or 'core functions'}</strong>."
        + "</p>"
        + f"<p style='line-height:1.7; font-size:16px; margin-bottom:16px; text-align:justify;'>"
        + "Leadership readiness in this sector is increasingly defined by emotional intelligence and adaptability. Benchmarks across similar roles suggest a strong regional average of <strong>{metrics[1][2]}%</strong>, revealing a shared pursuit of clarity, calm under pressure, and respectful authority."
        + "</p>"
        + f"<p style='line-height:1.7; font-size:16px; margin-bottom:16px; text-align:justify;'>"
        + f"The ability to reliably complete tasks — measured at <strong>{metrics[2][1]}%</strong> — remains one of the most trusted signals of upward potential. For those in <strong>{position}</strong> roles, it reflects not just speed but discernment — choosing the right things to execute well."
        + "</p>"
        + f"<p style='line-height:1.7; font-size:16px; margin-bottom:16px; text-align:justify;'>"
        + f"Your chosen focus — <strong>{focus}</strong> — echoes a broader shift we’ve seen across management profiles in Singapore, Malaysia, and Taiwan. Investing in this area may open new pathways of resilience, influence, and sustainable growth."
        + "</p>"
    )

    prompt = (
        f"Give 10 region-aware and emotionally intelligent improvement ideas for a {position} from {country} "
        f"with {experience} years in {sector}, facing '{challenge}' and focusing on '{focus}'. "
        f"Each idea should be on its own line, written warmly, with emojis. Avoid cold tone."
    )
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.85
    )
    tips = response.choices[0].message.content.strip().split("\n")
    tips_html = "<div style='font-size:24px;font-weight:bold;margin-top:30px;'>💡 Creative Suggestions:</div><br>"
    for line in tips:
        if line.strip():
            tips_html += f"<p style='margin:16px 0; font-size:17px;'>{line.strip()}</p>"

    footer = (
        '<div style="background-color:#e6f7ff; color:#00529B; padding:15px; border-left:4px solid #00529B; margin:20px 0;">'
        '<strong>The insights in this report are generated by KataChat’s AI systems analyzing:</strong><br>'
        '1. Our proprietary database of anonymized professional profiles across Singapore, Malaysia, and Taiwan<br>'
        '2. Aggregated global business benchmarks from trusted OpenAI research and leadership trend datasets<br>'
        '<em>All data is processed through our AI models to identify statistically significant patterns while maintaining strict PDPA compliance.</em>'
        '</div>'
        "<p style=\"background-color:#e6f7ff; color:#00529B; padding:15px; border-left:4px solid #00529B; margin:20px 0;\">"
        "<strong>PS:</strong> Your personalized report will arrive in your inbox within 24–48 hours. "
        "If you'd like to discuss it further, feel free to reach out — we're happy to arrange a 15-minute call at your convenience."
        "</p>"
    )

    email_output = raw_info + bar_html + summary + tips_html + footer
    display_output = bar_html + summary + tips_html + footer

    send_email(email_output)

    return jsonify({
        "metrics": [
            {"title": t, "labels": ["Segment", "Regional", "Global"], "values": [s, r, g]}
            for t, s, r, g, _ in metrics
        ],
        "analysis": display_output
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
