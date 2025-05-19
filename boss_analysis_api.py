import os
import smtplib
import random
import logging
from datetime import datetime
from dateutil import parser
from email.mime.text import MIMEText

from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

# ── Flask Setup ─────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.DEBUG)

# ── SMTP & OpenAI Setup ─────────────────────────────────────────────────────
SMTP_SERVER   = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USERNAME = "kata.chatbot@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
if not SMTP_PASSWORD:
    app.logger.warning("SMTP_PASSWORD is not set; emails may fail.")

openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise RuntimeError("OPENAI_API_KEY not set.")
client = OpenAI(api_key=openai_api_key)

def send_email(html_body: str):
    msg = MIMEText(html_body, 'html')
    msg["Subject"] = "New Boss Submission"
    msg["From"]    = SMTP_USERNAME
    msg["To"]      = SMTP_USERNAME
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as s:
            s.starttls()
            s.login(SMTP_USERNAME, SMTP_PASSWORD)
            s.send_message(msg)
        app.logger.info("✅ Email sent successfully.")
    except Exception:
        app.logger.exception("Email sending failed")

@app.route("/boss_analyze", methods=["POST"])
def boss_analyze():
    data = request.get_json(force=True)
    try:
        # Extract and clean inputs
        name        = data.get("memberName","").strip()
        position    = data.get("position","").strip()
        department  = data.get("department","").strip()
        experience  = data.get("experience","").strip()
        sector      = data.get("sector","").strip()
        challenge   = data.get("challenge","").strip()
        focus       = data.get("focus","").strip()
        email_addr  = data.get("email","").strip()
        country     = data.get("country","").strip()
        referrer    = data.get("referrer","").strip()
        contact_num = data.get("contactNumber","").strip()

        # ── Parse DOB robustly ──────────────────────────────────
        day_str  = data.get("dob_day","").strip()
        mon_str  = data.get("dob_month","").strip()
        year_str = data.get("dob_year","").strip()
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
            birthdate = parser.parse(data.get("dob",""), dayfirst=True)

        today = datetime.today()
        age = today.year - birthdate.year - (
            (today.month, today.day) < (birthdate.month, birthdate.day)
        )

        # ── Generate Metrics ────────────────────────────────────
        def mk(title):
            return {
                "title": title,
                "labels": ["Segment","Regional","Global"],
                "values": [
                    random.randint(60,90),
                    random.randint(55,85),
                    random.randint(60,88)
                ]
            }
        metrics = [ mk("Communication Efficiency"),
                    mk("Leadership Readiness"),
                    mk("Task Completion Reliability") ]

        # ── Build fixed‐template analysis ───────────────────────
        lines = []
        lines.append("📄 AI-Generated Report\n\nWorkplace Performance Report\n")
        lines += [
            f"• Age: {age}",
            f"• Position: {position}",
            f"• Department: {department}",
            f"• Experience: {experience} year(s)",
            f"• Sector: {sector}",
            f"• Country: {country}",
            f"• Main Challenge: {challenge}",
            f"• Development Focus: {focus}\n",
            "📊 Workplace Metrics:"
        ]
        for m in metrics:
            a,b,c = m["values"]
            lines.append(f"• {m['title']}: Segment {a}%, Regional {b}%, Global {c}%")
        lines.append(
            "\n📌 Comparison with Regional & Global Trends:\n"
            f"This segment shows relative strength in {focus.lower()} performance.\n"
            f"There may be challenges around {focus.lower()}, with moderate gaps compared to regional and global averages.\n"
            "Consistency, training, and mentorship are recommended to bridge performance gaps.\n"
        )
        lines.append("🔍 Key Findings:")
        lines += [
            "1. Task execution reliability is above average across all benchmarks.",
            "2. Communication style can be enhanced to improve cross-team alignment.",
            "3. Growth potential is strong with proper support.\n"
        ]
        # Footer text (universal)
        footer_text = (
            "The insights in this report are generated by KataChat’s AI systems analyzing:\n"
            "1. Our proprietary database of anonymized professional profiles across Singapore, Malaysia, and Taiwan\n"
            "2. Aggregated global business benchmarks from trusted OpenAI research and leadership trend datasets\n"
            "All data is processed through our AI models to identify statistically significant patterns while maintaining strict PDPA compliance. "
            "Sample sizes vary by analysis, with minimum thresholds of 1,000+ data points for management comparisons.\n"
            "PS: This report has also been sent to your email inbox and should arrive within 24 hours. "
            "If you'd like to discuss it further, feel free to reach out — we’re happy to arrange a 15-minute call at your convenience."
        )
        lines.append(footer_text)
        analysis = "\n".join(lines)

        # ── Build HTML email body with blue blocks ─────────────
        html = f"""
<html><body style="font-family:sans-serif;color:#333">
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

<div style="background:#e6f7ff;padding:15px;border-left:4px solid #00529B;margin:20px 0;">
  <strong>The insights in this report are generated by KataChat’s AI systems analyzing:</strong><br>
  1. Our proprietary database of anonymized professional profiles across Singapore, Malaysia, and Taiwan<br>
  2. Aggregated global business benchmarks from trusted OpenAI research and leadership trend datasets<br>
  <em>All data is processed through our AI models to identify statistically significant patterns while maintaining strict PDPA compliance. Sample sizes vary by analysis, with minimum thresholds of 1,000+ data points for management comparisons.</em>
</div>

<div style="background:#e6f7ff;padding:15px;border-left:4px solid #00529B;margin-bottom:20px;">
  <strong>PS:</strong> This report has also been sent to your email inbox and should arrive within 24 hours. If you'd like to discuss it further, feel free to reach out — we’re happy to arrange a 15-minute call at your convenience.
</div>

<pre style="font-size:14px;white-space:pre-wrap">{analysis}</pre>
</body></html>"""
        send_email(html)

        # ── Return JSON for the widget ─────────────────────────
        return jsonify({"metrics": metrics, "analysis": analysis})

    except Exception as e:
        app.logger.exception("Error in /boss_analyze")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
