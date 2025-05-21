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

# ── SMTP configuration ───────────────────────────────────────────────────────
SMTP_SERVER   = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USERNAME = "kata.chatbot@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
if not SMTP_PASSWORD:
    app.logger.warning("SMTP_PASSWORD is not set; emails may fail.")

def compute_age(data):
    """
    Compute age from DOB fields or freeform string.
    """
    d = data.get("dob_day")
    m = data.get("dob_month")
    y = data.get("dob_year")
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
    """
    Sends an HTML email to the configured address.
    """
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
    data = request.get_json(force=True)
    # 1) Extract inputs
    position   = data.get("position","").strip()
    department = data.get("department","").strip()
    experience = data.get("experience","").strip()
    sector     = data.get("sector","").strip()
    challenge  = data.get("challenge","").strip()
    focus      = data.get("focus","").strip()
    country    = data.get("country","").strip()
    age        = compute_age(data)

    # 2) Fixed metrics
    metrics = [
        ("Communication Efficiency",   79, 65, 74, "#5E9CA0"),
        ("Leadership Readiness",        63, 68, 76, "#FF9F40"),
        ("Task Completion Reliability", 82, 66, 84, "#9966FF"),
    ]

    # 3) Build HTML for horizontal bars
    bar_html = ""
    for title, seg, reg, glob, color in metrics:
        bar_html += f"<strong>{title}</strong><br>"
        for val in (seg, reg, glob):
            bar_html += (
                f"<span style='display:inline-block;width:{val}%;height:12px;"
                f"background:{color};margin-right:6px;border-radius:4px;'></span>"
            )
        bar_html += "<br><br>"

    # 4) Build the fixed “📄 Workplace Performance Report” section
    report_html = (
        "<br>\n<br>\n<br>\n"
        "<h2 class=\"sub\">📄 Workplace Performance Report</h2>\n"
        f"• Age: {age}<br>"
        f"• Position: {position}<br>"
        f"• Department: {department}<br>"
        f"• Experience: {experience} year(s)<br>"
        f"• Sector: {sector}<br>"
        f"• Country: {country}<br>"
        f"• Main Challenge: {challenge}<br>"
        f"• Development Focus: {focus}<br>"
    )

    # 5) Dynamically generate the Global Section via OpenAI
    prompt = f"""
Generate exactly seven professional two- to three-sentence analytical paragraphs for a "🌐 Global Section Analytical Report" based on these details:
- Position: {position}
- Department: {department}
- Years of Experience: {experience}
- Sector: {sector}
- Country: {country}
- Main Challenge: {challenge}
- Development Focus: {focus}

Use third-person, data-informed tone. Wrap each paragraph in <p>...</p> tags.
"""
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert business analyst with deep domain knowledge."},
            {"role": "user",   "content": prompt}
        ],
        temperature=0.7
    )
    global_html = completion.choices[0].message.content

    # 6) PDPA footer
    footer = (
        "<div style=\"background-color:#e6f7ff; color:#00529B; padding:15px; "
        "border-left:4px solid #00529B; margin:20px 0;\">"
        "<strong>PDPA Compliance:</strong> This report complies with PDPA regs for Singapore, Malaysia, and Taiwan."
        "</div>"
    )

    # 7) Assemble full analysis HTML
    analysis_html = (
        bar_html
        + report_html
        + "<h2 class=\"sub\">🌐 Global Section Analytical Report</h2>"
        + global_html
        + footer
    )

    # 8) Send email and return JSON
    send_email(analysis_html)
    return jsonify({
        "metrics": [
            {"title": t, "labels": ["Segment","Regional","Global"], "values": [s,r,g]}
            for t,s,r,g,_ in metrics
        ],
        "analysis": analysis_html
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
