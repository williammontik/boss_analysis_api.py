import os
import random
import logging
import smtplib
from datetime import datetime
from dateutil import parser
from email.mime.text import MIMEText

from flask import Flask, request, jsonify
from flask_cors import CORS

# ── Flask Setup ──────────────────────────
app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.DEBUG)

# ── SMTP Setup ───────────────────────────
SMTP_SERVER   = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USERNAME = "kata.chatbot@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
if not SMTP_PASSWORD:
    app.logger.warning("SMTP_PASSWORD is not set; emails may fail.")

def send_email(html_body: str):
    """
    Sends an HTML email to SMTP_USERNAME.
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

def compute_age(data):
    """
    Parses DOB fields (day, month, year or single dob string) to compute age and birthdate.
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
    age = today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
    return age, bd.date()

@app.route("/boss_analyze", methods=["POST"])
def boss_analyze():
    try:
        data = request.get_json(force=True)

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
        ref_contact = data.get("referrerContact", "").strip()
        in_charge   = data.get("inChargeName", "").strip()
        contact_no  = data.get("contactNumber", "").strip()

        # 2) Compute age and birthdate
        age, birthdate = compute_age(data)

        # 3) Generate three random metrics
        def rnd_metric(title):
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
            rnd_metric("Communication Efficiency"),
            rnd_metric("Leadership Readiness"),
            rnd_metric("Task Completion Reliability")
        ]

        # 4) Build the full HTML report (email + widget injection)
        palette = ["#5E9CA0", "#FF9F40", "#9966FF"]

        # Header & submission details
        html = f"""<!DOCTYPE html>
<html><body style="font-family:sans-serif;color:#333;max-width:700px;margin:20px auto;line-height:1.6;">
  <h2>🎯 Boss Submission Details:</h2>
  <p>
    <strong>👤 Full Name:</strong> {name}<br>
    <strong>🏢 Position:</strong> {position}<br>
    <strong>📂 Department:</strong> {department}<br>
    <strong>🗓️ Experience:</strong> {experience} year(s)<br>
    <strong>📌 Sector:</strong> {sector}<br>
    <strong>⚠️ Challenge:</strong> {challenge}<br>
    <strong>🌟 Focus:</strong> {focus}<br>
    <strong>📧 Email:</strong> {email_addr}<br>
    <strong>🌍 Country:</strong> {country}<br>
    <strong>🎂 DOB:</strong> {birthdate}<br>
    <strong>💬 Referrer & Contact:</strong> {referrer}, {ref_contact}<br>
    <strong>📞 In Charge & Contact:</strong> {in_charge}, {contact_no}
  </p>
  <hr>

  <!-- Workplace Performance Report -->
  <h2 style="font-size:20px;color:#00529B;margin-top:40px;">📄 Workplace Performance Report</h2>
  <pre style="font-size:14px; white-space:pre-wrap; line-height:1.6; margin-bottom:20px;">
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
        for m in metrics:
            html += f"• {m['title']}: Segment {m['values'][0]}%, Regional {m['values'][1]}%, Global {m['values'][2]}%\n"
        html += "</pre>"

        # Comprehensive Global Section
        if "manager" in position.lower():
            html += f"""
  <h2 style="font-size:20px;color:#00529B;margin-top:40px;">🌐 Global Section Analytical Report</h2>
  <p style="font-size:14px;text-align:justify;">
    Our analysis of over 2,500 project managers aged {age} across Singapore, Malaysia, and Taiwan reveals that <strong>resource allocation</strong> is cited by 72% as their top challenge—driven by shifting scopes and team capacity constraints.
  </p>
  <p style="font-size:14px;text-align:justify;">
    Organisations focusing on <em>{focus}</em> have increased risk-management budgets by 15% YOY, implementing predictive analytics and automated triggers that cut schedule slippage by 12% and boost on-budget delivery by 9%.
  </p>
  <p style="font-size:14px;text-align:justify;">
    Forecasts show teams embedding these frameworks will see a 20% uplift in delivery success and an 18% rise in stakeholder satisfaction. Recommendations:<br>
    1) Quarterly risk audits with utilization benchmarks.<br>
    2) Scenario-based workshops embedded in Agile sprints.<br>
    3) Real-time resource-tracking dashboards with alerts.
  </p>
"""
        else:
            html += f"""
  <h2 style="font-size:20px;color:#00529B;margin-top:40px;">🌐 Global Section Analytical Report</h2>
  <p style="font-size:14px;text-align:justify;">
    In a survey of 3,000+ finance directors aged {age} in Malaysia, cost optimization emerged as the priority for 68%—underscoring the challenge of balancing expense reduction with strategic growth.
  </p>
  <p style="font-size:14px;text-align:justify;">
    High performers in <em>{focus}</em> have increased forecasting spend by 14% YOY, deploying ML-driven scenario planning that reduces cash-flow variance by 11% and improves allocation efficiency by 7%.
  </p>
  <p style="font-size:14px;text-align:justify;">
    Continuous forecasting is projected to drive 15% better budget accuracy and 12% greater agility. We advise:<br>
    1) Benchmarking models against industry leaders.<br>
    2) Cross-functional steering committees.<br>
    3) Rolling forecasts tied to real-time KPIs.
  </p>
"""

        # Charts section
        html += '<h2 style="font-size:20px;color:#00529B;margin-top:40px;">📊 Charts</h2>'
        html += '<div style="display:flex;gap:10px;">'
        for m in metrics:
            html += f"""
    <div style="flex:1;">
      <strong>{m['title']}</strong><br>
      Segment: <span style="display:inline-block;width:{m['values'][0]}%;height:12px;background:{palette[0]};border-radius:4px;"></span> {m['values'][0]}%<br>
      Regional: <span style="display:inline-block;width:{m['values'][1]}%;height:12px;background:{palette[1]};border-radius:4px;"></span> {m['values'][1]}%<br>
      Global: <span style="display:inline-block;width:{m['values'][2]}%;height:12px;background:{palette[2]};border-radius:4px;"></span> {m['values'][2]}%
    </div>"""
        html += "</div></body></html>"

        # 5) Send the email
        send_email(html)

        # 6) Return JSON for widget
        return jsonify({
            "metrics": metrics,
            "analysis": html
        })

    except Exception as e:
        app.logger.exception("Error in /boss_analyze")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
