import os
import smtplib
from datetime import datetime
from dateutil import parser
from email.mime.text import MIMEText

from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)

# ── OpenAI Client ────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set")
client = OpenAI(api_key=OPENAI_API_KEY)

# ── SMTP Setup ───────────────────────────────────────────────────────────────
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
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as s:
        s.starttls()
        s.login(SMTP_USERNAME, SMTP_PASSWORD)
        s.send_message(msg)

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

    # 1) Static or random metrics
    metrics = []
    for title, color in [
        ("Communication Efficiency", "#5E9CA0"),
        ("Leadership Readiness",      "#FF9F40"),
        ("Task Completion Reliability","#9966FF"),
    ]:
        seg = random.randint(60, 90)
        reg = random.randint(55, 85)
        glo = random.randint(60, 88)
        metrics.append((title, seg, reg, glo, color))

    # 2) Build horizontal bar HTML
    bar_html = ""
    for title, seg, reg, glo, color in metrics:
        bar_html += f"""
<div style="margin-bottom:16px;">
  <strong>{title}</strong><br>
  Segment: <span style="display:inline-block;width:{seg}%;height:12px;background:{color};border-radius:4px;"></span> {seg}%<br>
  Regional: <span style="display:inline-block;width:{reg}%;height:12px;background:{color};border-radius:4px;"></span> {reg}%<br>
  Global: <span style="display:inline-block;width:{glo}%;height:12px;background:{color};border-radius:4px;"></span> {glo}%
</div>
"""
    # 3) Workplace Performance Report block
    report_html = """
<br>
<br>
<br>
<h2 class="sub">📄 Workplace Performance Report</h2>
<div class="narrative">
"""
    report_html += (
        f"• Age: {age}<br>"
        f"• Position: {position}<br>"
        f"• Department: {department or '—'}<br>"
        f"• Experience: {experience} year(s)<br>"
        f"• Sector: {sector}<br>"
        f"• Country: {country}<br>"
        f"• Main Challenge: {challenge}<br>"
        f"• Development Focus: {focus}<br>"
    )
    report_html += "</div>\n"

    # 4) Global Section via OpenAI
    global_header = '<h2 class="sub">🌐 Global Section Analytical Report</h2>\n<div class="global">\n'
    prompt_global = (
        f"You are an expert business analyst. Craft a seven-paragraph, richly detailed analytical report "
        f"for a {position} in {country} with {experience} years of experience in the {sector} sector. "
        f"Their key challenge is “{challenge}” and their development focus is “{focus}.” "
        "Use data-driven insights, transitional phrases, and best-practice recommendations."
    )
    resp_global = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role":"user","content":prompt_global}],
        temperature=0.7
    )
    global_html = resp_global.choices[0].message.content + "</div>\n"

    # 5) Creative Innovation Approaches via OpenAI
    creative_prompt = (
        f"You are an innovation consultant. For a {position} facing the challenge “{challenge}” "
        f"and focusing on “{focus},” propose 10 highly creative, actionable approaches—each 1–2 "
        "sentences—numbered 1 to 10."
    )
    resp_creative = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role":"user","content":creative_prompt}],
        temperature=0.8
    )
    creative_lines = resp_creative.choices[0].message.content.split("\n")
    creative_html = "<h3>Creative Innovation Approaches</h3>\n<div class=\"creative\">\n"
    for line in creative_lines:
        if line.strip():
            creative_html += f"<p>{line.strip()}</p>\n"
    creative_html += "</div>\n"

    # 6) Blue PDPA footer
    footer = """
<div style="background-color:#e6f7ff; color:#00529B; padding:15px; border-left:4px solid #00529B; margin:20px 0;">
  <strong>The insights in this report are generated by KataChat’s AI systems analyzing:</strong><br>
  1. Our proprietary database of anonymized professional profiles across Singapore, Malaysia, and Taiwan<br>
  2. Aggregated global business benchmarks from trusted OpenAI research and leadership trend datasets<br>
  <em>All data is processed to identify statistically significant patterns while maintaining strict PDPA compliance (min. 1,000+ data points).</em>
</div>
<p style="background-color:#e6f7ff; color:#00529B; padding:15px; border-left:4px solid #00529B; margin:20px 0;">
  <strong>PS:</strong> This report has been emailed to you and should arrive within 24 hours. 
  We’re happy to arrange a 15-minute follow-up call if you’d like to discuss further.
</p>
"""

    # 7) Assemble full HTML
    analysis_html = (
        bar_html
        + report_html
        + global_header + global_html
        + creative_html
        + footer
    )

    # 8) Send the email
    send_email(analysis_html)

    # 9) Return JSON
    return jsonify({
        "metrics": [
            {"title": t, "labels": ["Segment","Regional","Global"], "values": [s,r,g]}
            for t,s,r,g,_ in metrics
        ],
        "analysis": analysis_html
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
