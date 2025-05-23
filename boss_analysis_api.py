# -*- coding: utf-8 -*-
import os
import random
from datetime import datetime
from dateutil import parser
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from email.mime.text import MIMEText
import smtplib

app = Flask(__name__)
CORS(app)

# ── OpenAI Client ───────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set")
client = OpenAI(api_key=OPENAI_API_KEY)

# ── SMTP config ─────────────────────────────────────────────────────────
SMTP_SERVER   = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USERNAME = "kata.chatbot@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
if not SMTP_PASSWORD:
    app.logger.warning("SMTP_PASSWORD is not set; emails may fail.")

def compute_age(data):
    d, m, y = data.get("dob_day"), data.get("dob_month"), data.get("dob_year")
    try:
        if d and m and y:
            month = int(m) if m.isdigit() else datetime.strptime(m, "%B").month
            bd = datetime(int(y), month, int(d))
        else:
            bd = parser.parse(data.get("dob",""), dayfirst=True)
    except Exception:
        bd = datetime.today()
    today = datetime.today()
    return today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))

def send_email(html_body: str):
    msg = MIMEText(html_body, 'html')
    msg["Subject"] = "Your Workplace Performance Report"
    msg["From"]    = SMTP_USERNAME
    msg["To"]      = SMTP_USERNAME
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)

@app.route("/boss_analyze", methods=["POST"])
def boss_analyze():
    data       = request.get_json(force=True)
    lang       = data.get("lang", "en").lower()
    position   = data.get("position","").strip()
    department = data.get("department","").strip()
    experience = data.get("experience","").strip()
    sector     = data.get("sector","").strip()
    challenge  = data.get("challenge","").strip()
    focus      = data.get("focus","").strip()
    country    = data.get("country","").strip()
    age        = compute_age(data)

    # 1) Generate metrics
    metrics = []
    for title, color in [
        ("Communication Efficiency",   "#5E9CA0"),
        ("Leadership Readiness",        "#FF9F40"),
        ("Task Completion Reliability", "#9966FF"),
    ]:
        seg, reg, glo = random.randint(60,90), random.randint(55,85), random.randint(60,88)
        metrics.append((title, seg, reg, glo, color))

    # 2) Build horizontal bar HTML
    bar_html = ""
    for title, seg, reg, glo, color in metrics:
        bar_html += f"<strong>{title}</strong><br>"
        for v in (seg, reg, glo):
            bar_html += (
                f"<span style='display:inline-block;width:{v}%;height:12px;"
                f" background:{color}; margin-right:6px; border-radius:4px;'></span> {v}%<br>"
            )
        bar_html += "<br>"

    # 3) Greeting
    greeting = "<p>Dear Talent Recruiter,</p>"

    # 4) Workplace Performance Report block
    report_html = (
        "<br>\n<br>\n<br>\n"
        + '<h2 class="sub">📄 Workplace Performance Report</h2>\n'
        + "<div class='narrative'>"
        + f"• Age: {age}<br>"
        + f"• Position: {position}<br>"
        + f"• Department: {department or '—'}<br>"
        + f"• Experience: {experience} year(s)<br>"
        + f"• Sector: {sector}<br>"
        + f"• Country: {country}<br>"
        + f"• Main Challenge: {challenge}<br>"
        + f"• Development Focus: {focus}<br>"
        + "</div>\n"
    )

    # 5) Global Section via OpenAI
    global_header = '<h2 class="sub">🌐 Global Section Analytical Report</h2>\n<div class="global">\n'
    prompt_global = (
        f"You are an expert business analyst. Write seven detailed paragraphs for a {position} in {country}, "
        f"{experience} years experience in {sector}. Challenge: “{challenge}”. Focus: “{focus}”."
    )
    resp_global = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role":"user","content":prompt_global}],
        temperature=0.7
    )
    global_html = resp_global.choices[0].message.content + "</div>\n"

    # 6) Creative Approaches via OpenAI
    creative_prompt = (
        f"You are an innovation consultant. For a {position} whose challenge is “{challenge}” "
        f"and focus is “{focus}”, propose 10 creative, actionable approaches, numbered 1–10."
    )
    resp_creative = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role":"user","content":creative_prompt}],
        temperature=0.8
    )
    lines = resp_creative.choices[0].message.content.split("\n")
    creative_html = "<h3>Creative Innovation Approaches</h3>\n<div class='creative'>\n"
    for ln in lines:
        if ln.strip():
            creative_html += f"<p>{ln.strip()}</p>\n"
    creative_html += "</div>\n"

    # 7) Original blue PDPA footer (unchanged)
    footer = (
        '<div style="background-color:#e6f7ff; color:#00529B; padding:15px; '
        'border-left:4px solid #00529B; margin:20px 0;">'
        '<strong>The insights in this report are generated by KataChat’s AI systems analyzing:</strong><br>'
        '1. Our proprietary database of anonymized professional profiles across Singapore, Malaysia, and Taiwan<br>'
        '2. Aggregated global business benchmarks from trusted OpenAI research and leadership trend datasets<br>'
        '<em>All data is processed through our AI models to identify statistically significant patterns while maintaining strict PDPA compliance. Sample sizes vary by analysis, with minimum thresholds of 1,000+ data points for management comparisons.</em>'
        '</div>'
        '<p style="background-color:#e6f7ff; color:#00529B; padding:15px; '
        'border-left:4px solid #00529B; margin:20px 0;">'
        '<strong>PS:</strong> This report has also been sent to your email inbox and should arrive within 24 hours. '
        'If you\'d like to discuss it further, feel free to reach out — we’re happy to arrange a 15-minute call at your convenience.'
        '</p>'
    )

    # 8) Assemble full HTML
    analysis_html = (
        greeting
        + bar_html
        + report_html
        + global_header + global_html
        + creative_html
        + footer
    )

    # 9) Send the email
    send_email(analysis_html)

    # 10) Return JSON
    return jsonify({
        "metrics": [
            {"title": t, "labels": ["Segment","Regional","Global"], "values": [s,r,g]}
            for t,s,r,g,_ in metrics
        ],
        "analysis": analysis_html
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
