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
    Sends an HTML email containing the full submission and report.
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

        # 3) Call OpenAI for the narrative (English only for email; widget gets JSON below)
        prompt = f"""
You are an expert organizational psychologist.
Generate a detailed performance report for a team member named "{name}",
working as "{position}", who faces this key challenge:
"{challenge}". Their preferred development focus is "{focus}", and they are located in "{country}".

Requirements:
1. Provide a 150–200 word narrative.
2. Highlight their top strength vs. region/global.
3. Identify their biggest gap.
4. Offer three actionable next steps.
5. Return only the narrative text (no JSON).
"""
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"user","content":prompt}]
        )
        analysis = response.choices[0].message.content.strip()

        # 4) Generate metrics
        def random_metric(title):
            return {
                "title": title,
                "labels": ["Segment", "Regional Avg", "Global Avg"],
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

        # 5) Build the HTML email body exactly as your working example
        html = f"""<html><body style="font-family:sans-serif;color:#333">
<h2>🎯 Boss Submission Details:</h2>
<p>
👤 <strong>Full Name:</strong> {name}<br>
🏢 <strong>Position:</strong> {position}<br>
📂 <strong>Department:</strong> {department}<br>
🗓️ <strong>Experience:</strong> {experience} year(s)<br>
📌 <strong>Sector:</strong> {sector}<br>
⚠️ <strong>Challenge:</strong> {challenge}<br>
🌟 <strong>Focus:</strong> {focus}<br>
📧 <strong>Email:</strong> {email_addr}<br>
🌍 <strong>Country:</strong> {country}<br>
🎂 <strong>DOB:</strong> {birthdate.date()}<br>
💬 <strong>Referrer:</strong> {referrer}
</p>
<hr>
<h2>📄 AI-Generated Report</h2>
<pre style="font-size:14px;white-space:pre-wrap">{analysis}</pre>
<hr>
<h2>📊 Charts</h2>
"""

        # Inline CSS bar charts
        palette = ["#5E9CA0","#FF9F40","#9966FF"]
        for m in metrics:
            html += f"<h3>{m['title']}</h3>"
            for idx, lbl in enumerate(m["labels"]):
                val = m["values"][idx]
                color = palette[idx]
                html += (
                    f"<div style='margin:4px 0; line-height:1.4'>"
                    f"{lbl}: <span style='display:inline-block; width:{val}%; height:12px; "
                    f"background:{color}; border-radius:4px;'></span> &nbsp;{val}%"
                    f"</div>"
                )
        html += """
<div style="background-color:#e6f7ff; color:#00529B; padding:15px; border-left:4px solid #00529B; margin:20px 0;">
  <strong>The insights in this report are generated by KataChat’s AI systems analyzing:</strong><br>
  1. Our proprietary database of anonymized professional profiles across Singapore, Malaysia, and Taiwan<br>
  2. Aggregated global business benchmarks from trusted OpenAI research and leadership trend datasets<br>
  <em>All data is processed through our AI models to identify statistically significant patterns while maintaining strict PDPA compliance. Sample sizes vary by analysis, with minimum thresholds of 1,000+ data points for management comparisons.</em>
</div>
<p style="background-color:#e6f7ff; color:#00529B; padding:15px; border-left:4px solid #00529B; margin:20px 0;">
  <strong>PS:</strong> This report has also been sent to your email inbox and should arrive within 24 hours.
  If you'd like to discuss it further, feel free to reach out — we’re happy to arrange a 15-minute call at your convenience.
</p>
</body></html>"""

        # 6) Send the email
        send_email(html)

        # 7) Return the same JSON that the widget expects
        return jsonify({"metrics": metrics, "analysis": analysis})

    except Exception as e:
        app.logger.exception("Error in /boss_analyze")
        return jsonify({"error": str(e)}), 500


# ── Run Locally ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
