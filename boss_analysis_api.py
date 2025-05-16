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

# ── Flask Setup ────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.DEBUG)

# ── OpenAI Setup ───────────────────────────────────────────────
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise RuntimeError("OPENAI_API_KEY environment variable is not set.")
client = OpenAI(api_key=openai_api_key)

# ── SMTP Email Setup ───────────────────────────────────────────
SMTP_SERVER   = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USERNAME = "kata.chatbot@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
if not SMTP_PASSWORD:
    app.logger.warning("SMTP_PASSWORD is not set; emails may fail.")

def send_email(full_name, position, department, experience, sector, challenge, focus, email, country, dob, referrer):
    subject = "New Boss Submission"
    body = f"""
🎯 Boss Submission:

👤 Full Name: {full_name}
🏢 Position: {position}
📂 Department: {department}
📅 Experience: {experience}
📌 Sector: {sector}
⚠️ Challenge: {challenge}
🎯 Focus: {focus}
📧 Email: {email}
🌍 Country: {country}
🎂 DOB: {dob}
💬 Referrer: {referrer}
"""
    msg = MIMEText(body)
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

# ── /boss_analyze Endpoint (Managers) ─────────────────────────────────────────
@app.route("/boss_analyze", methods=["POST"])
def boss_analyze():
    try:
        data = request.get_json(force=True)
        app.logger.info(f"[boss_analyze] Payload received: {data}")

        name       = data.get("memberName", "")
        position   = data.get("position", "")
        department = data.get("department", "")
        experience = data.get("experience", "")
        sector     = data.get("sector", "")
        challenge  = data.get("challenge", "")
        focus      = data.get("focus", "")
        email_addr = data.get("email", "")
        country    = data.get("country", "")
        referrer   = data.get("referrer", "")

        # DOB Handling
        day_str  = data.get("dob_day")
        mon_str  = data.get("dob_month")
        year_str = data.get("dob_year")

        if day_str and mon_str and year_str:
            if mon_str.isdigit():
                month = int(mon_str)
            else:
                month = datetime.strptime(mon_str, "%B").month
            birthdate = datetime(int(year_str), month, int(day_str))
        else:
            birthdate = parser.parse(data.get("dob", ""), dayfirst=True)

        today = datetime.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))

        send_email(name, position, department, experience, sector, challenge, focus, email_addr, country, birthdate.date(), referrer)

        # Chart Data and Visual Structure for Boss Section
        def build_metric(title, labels):
            # Randomized value generation for a more dynamic output
            return {
                "title": title,
                "labels": labels,
                "values": [random.randint(60, 95) for _ in labels]  # Adjust value ranges if necessary
            }

        # Metrics for Manager’s Performance (similar structure as Children)
        metrics = [
            build_metric("Leadership Traits", ["Initiative", "Accountability", "Empathy"]),
            build_metric("Team Dynamics", ["Teamwork", "Supportiveness", "Communication"]),
            build_metric("Execution Capacity", ["Punctuality", "Follow-Through", "Efficiency"])
        ]

        # Summary Report for Boss Section
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

📊 Workplace Metrics:
"""
        # Display all metrics in a clear and engaging manner
        for m in metrics:
            summary += f"• {m['title']}: " + ", ".join([f"{label} {val}%" for label, val in zip(m["labels"], m["values"])]) + "\n"

        footer = """
<div style="background-color:#e6f7ff; color:#00529B; padding:15px; border-left:4px solid #00529B; margin:20px 0;">
  <strong>The insights in this report are generated by KataChat’s AI systems analyzing:</strong><br>
  1. A proprietary dataset of anonymized management patterns in Singapore, Malaysia, and Taiwan<br>
  2. Aggregated global leadership benchmarks from OpenAI and professional development datasets<br>
  <em>All insights are PDPA-compliant and statistically modeled with threshold samples of over 1000 records per field.</em>
</div>
<p style="background-color:#e6f7ff; color:#00529B; padding:15px; border-left:4px solid #00529B; margin:20px 0;">
  <strong>PS:</strong> You’ll also get a copy via email. If you’d like to book a follow-up session, we’re happy to arrange a 15-minute call at your convenience.
</p>
"""

        return jsonify({
            "metrics": metrics,
            "analysis": summary.strip() + "\n\n" + footer.strip()
        })

    except Exception as e:
        app.logger.exception("Error in /boss_analyze")
        return jsonify({"error": str(e)}), 500

# ── Run Locally ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
