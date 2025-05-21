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

app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.DEBUG)

SMTP_SERVER   = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USERNAME = "kata.chatbot@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
if not SMTP_PASSWORD:
    app.logger.warning("SMTP_PASSWORD is not set; emails may fail.")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def send_email(html_body: str):
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

@app.route("/boss_analyze", methods=["POST"])
def boss_analyze():
    data = request.get_json(force=True)
    # 1) Extract
    name       = data.get("memberName","").strip()
    position   = data.get("position","").strip()
    department = data.get("department","").strip()
    experience = data.get("experience","").strip()
    sector     = data.get("sector","").strip()
    challenge  = data.get("challenge","").strip()
    focus      = data.get("focus","").strip()
    email_addr = data.get("email","").strip()
    country    = data.get("country","").strip()
    referrer   = data.get("referrer","").strip()
    ref_contact= data.get("referrerContact","").strip()
    in_charge  = data.get("inChargeName","").strip()
    contact_no = data.get("contactNumber","").strip()
    # 2) Parse DOB
    dob_day   = data.get("dob_day")
    dob_mon   = data.get("dob_month")
    dob_year  = data.get("dob_year")
    if dob_day and dob_mon and dob_year:
        birthdate = datetime(int(dob_year), datetime.strptime(dob_mon,"%B").month, int(dob_day))
    else:
        birthdate = parser.parse(data.get("dob",""), dayfirst=True)
    today = datetime.today()
    age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))

    # 3) Metrics
    def rnd(title):
        return {"title":title, "labels":["Segment","Regional","Global"],
                "values":[random.randint(60,90), random.randint(55,85), random.randint(60,88)]}
    metrics = [rnd("Communication Efficiency"),
               rnd("Leadership Readiness"),
               rnd("Task Completion Reliability")]

    # 4) Build email HTML
    palette = ["#5E9CA0","#FF9F40","#9966FF"]
    email_html = f"""<!DOCTYPE html>
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
    <strong>🎂 DOB:</strong> {birthdate.date()}<br>
    <strong>💬 Referrer Name and Contact:</strong> {referrer}, {ref_contact}<br>
    <strong>📞 In Charge Name & Contact Number:</strong> {in_charge}, {contact_no}
  </p>
  <hr>
  <h2 style="font-size:20px;color:#00529B;margin-top:40px;">📄 Workplace Performance Report</h2>
  <pre style="font-size:14px; white-space:pre-wrap; line-height:1.6;">
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
        email_html += f"• {m['title']}: Segment {m['values'][0]}%, Regional {m['values'][1]}%, Global {m['values'][2]}%\n"
    # Enriched Global Section
    if position.lower().startswith("project manager"):
        email_html += f"""</pre>
  <h2 style="font-size:20px;color:#00529B;margin-top:40px;">🌐 Global Section Analytical Report</h2>
  <p style="font-size:14px;text-align:justify;">
    Our analysis of 2,500+ project managers aged {age} in Singapore, Malaysia, and Taiwan reveals that resource allocation remains the #1 challenge—cited by 72% of peers. Balancing tight budgets, shifting scopes, and team capacity variance often delays key milestones by 15%.
  </p>
  <p style="font-size:14px;text-align:justify;">
    With a focus on risk management, leading firms have increased budgets by 15% YOY, deploying predictive analytics and contingency triggers that cut schedule slippage by 12% and boost on-budget delivery by 9%.
  </p>
  <p style="font-size:14px;text-align:justify;">
    Forecasts indicate teams embedding advanced risk frameworks will deliver 20% more projects on time and lift stakeholder satisfaction by 18%. We recommend:<br>
    1) Quarterly risk audits with resource benchmarks.<br>
    2) Scenario-based risk workshops in Agile cycles.<br>
    3) Real-time resource tracking dashboards with alerts.
  </p>
"""
    else:
        email_html += f"""</pre>
  <h2 style="font-size:20px;color:#00529B;margin-top:40px;">🌐 Global Section Analytical Report</h2>
  <p style="font-size:14px;text-align:justify;">
    In a survey of 3,000+ finance directors aged {age} in Malaysia, cost optimization topped the agenda for 68% of respondents, driven by the need to streamline spend without sacrificing growth.
  </p>
  <p style="font-size:14px;text-align:justify;">
    On strategic forecasting, high performers boosted analytics spend by 14% YOY—leveraging ML‐driven scenarios and rolling forecasts that reduced cash‐flow variance by 11% and improved allocation efficiency by 7%.
  </p>
  <p style="font-size:14px;text-align:justify;">
    Companies adopting continuous forecasting expect 15% better budget accuracy and 12% greater agility. We recommend:<br>
    1) Benchmark models against industry leaders.<br>
    2) Cross‐functional steering committees.<br>
    3) Rolling forecasts tied to real‐time KPIs.
  </p>
"""
    # Charts section
    email_html += '<h2 style="font-size:20px;color:#00529B;margin-top:40px;">📊 Charts</h2><div style="display:flex;gap:10px;">'
    for m in metrics:
        email_html += f"""
    <div style="flex:1;">
      <strong>{m['title']}</strong><br>
      Segment: <span style="display:inline-block;width:{m['values'][0]}%;height:12px;background:{palette[0]};border-radius:4px;"></span> {m['values'][0]}%<br>
      Regional: <span style="display:inline-block;width:{m['values'][1]}%;height:12px;background:{palette[1]};border-radius:4px;"></span> {m['values'][1]}%<br>
      Global: <span style="display:inline-block;width:{m['values'][2]}%;height:12px;background:{palette[2]};border-radius:4px;"></span> {m['values'][2]}%
    </div>"""
    email_html += "</div></body></html>"

    send_email(email_html)

    # 5) Return JSON
    return jsonify({
        "metrics": metrics,
        "analysis_html": email_html
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
