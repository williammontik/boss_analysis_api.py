import os
import random
import logging
import smtplib
from datetime import datetime
from dateutil import parser
from email.mime.text import MIMEText

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.DEBUG)

SMTP_SERVER   = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USERNAME = "kata.chatbot@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
if not SMTP_PASSWORD:
    app.logger.warning("SMTP_PASSWORD is not set; emails may fail.")

def send_email(html_body: str):
    msg = MIMEText(html_body, 'html')
    msg["Subject"] = "New Boss Submission"
    msg["From"]    = SMTP_USERNAME
    msg["To"]      = SMTP_USERNAME
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)

def compute_age(data):
    d, m, y = data.get("dob_day"), data.get("dob_month"), data.get("dob_year")
    try:
        if d and m and y:
            month = int(m) if m.isdigit() else datetime.strptime(m, "%B").month
            bd = datetime(int(y), month, int(d))
        else:
            bd = parser.parse(data.get("dob",""), dayfirst=True)
    except:
        bd = datetime.today()
    today = datetime.today()
    return today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day)), bd.date()

@app.route("/boss_analyze", methods=["POST"])
def boss_analyze():
    data = request.get_json(force=True)

    # Extract fields
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
    ref_contact = data.get("referrerContact","").strip()
    in_charge   = data.get("inChargeName","").strip()
    contact_no  = data.get("contactNumber","").strip()

    # Compute age
    age, birthdate = compute_age(data)

    # Generate metrics
    def rnd_metric(title):
        return {
            "title": title,
            "labels": ["Segment","Regional","Global"],
            "values": [random.randint(60,90), random.randint(55,85), random.randint(60,88)]
        }
    metrics = [
        rnd_metric("Communication Efficiency"),
        rnd_metric("Leadership Readiness"),
        rnd_metric("Task Completion Reliability")
    ]

    # 1) Build the **email** HTML (full page) with inline bars
    palette = ["#5E9CA0","#FF9F40","#9966FF"]
    email_html = f"""<!DOCTYPE html>
<html><body style="font-family:sans-serif;color:#333;max-width:700px;margin:20px auto;line-height:1.6;">
  <h2>🎯 Boss Submission Details:</h2>
  <!-- detail block omitted for brevity… reuse your existing template -->
  <hr>
  <h2 style="font-size:20px;color:#00529B;margin-top:40px;">📄 Workplace Performance Report</h2>
  <pre style="font-size:14px;white-space:pre-wrap;line-height:1.6;">
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
    email_html += "</pre>\n"
    # Enriched global section (3 paragraphs)
    if "manager" in position.lower():
        email_html += f"""<h2 style="font-size:20px;color:#00529B;margin-top:40px;">🌐 Global Section Analytical Report</h2>
  <p style="font-size:14px;text-align:justify;">
    Our analysis of over 2,500 project managers aged {age} across Singapore, Malaysia, and Taiwan reveals that <strong>resource allocation</strong> is cited by 72% as their top challenge—driven by shifting scopes and team capacity constraints.
  </p>
  <p style="font-size:14px;text-align:justify;">
    Organisations focusing on <em>{focus}</em> have increased risk-management budgets by 15% YOY, implementing predictive analytics and automated triggers that cut schedule slippage by 12% and boost on-budget delivery by 9%.
  </p>
  <p style="font-size:14px;text-align:justify;">
    Forecasts show teams embedding these frameworks will see a 20% uplift in delivery success and an 18% rise in stakeholder satisfaction. Recommendations:<br>
    1) Quarterly risk audits with utilization benchmarks.<br>
    2) Scenario-based workshops in Agile sprints.<br>
    3) Real-time resource-tracking dashboards with alerts.
  </p>
"""
    else:
        email_html += f"""<h2 style="font-size:20px;color:#00529B;margin-top:40px;">🌐 Global Section Analytical Report</h2>
  <p style="font-size:14px;text-align:justify;">
    In a survey of 3,000+ finance directors aged {age} in Malaysia, cost optimization emerged as the priority for 68%—underscoring the challenge of balancing expense reduction with growth.
  </p>
  <p style="font-size:14px;text-align:justify;">
    High performers in <em>{focus}</em> have boosted analytics budgets by 14% YOY, deploying ML-driven scenarios that cut cash-flow variance by 11% and improve allocation by 7%.
  </p>
  <p style="font-size:14px;text-align:justify;">
    Continuous forecasting is projected to deliver 15% better budget accuracy and 12% greater agility. We advise:<br>
    1) Benchmark models against industry leaders.<br>
    2) Cross-functional steering committees.<br>
    3) Rolling forecasts tied to real-time KPIs.
  </p>
"""
    # Charts
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

    # 2) Build **widget** HTML fragment exactly matching full_widget_sarah.html structure
    widget_html = f"""
<h2 class="header">🎉 AI Team Member Performance Insights:</h2>
<div class="charts-row">
"""
    for i, m in enumerate(metrics):
        widget_html += f'  <div class="chart-item"><canvas id="c{i}"></canvas></div>\n'
    widget_html += "</div>\n"
    # Narrative
    widget_html += f"""
<h2 class="sub">📄 Workplace Performance Report</h2>
<div class="narrative">
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
        widget_html += f"• {m['title']}: Segment {m['values'][0]}%, Regional {m['values'][1]}%, Global {m['values'][2]}%\n"
    widget_html += "</div>\n"
    # Global section
    if "manager" in position.lower():
        widget_html += f"""
<h2 class="sub">🌐 Global Section Analytical Report</h2>
<div class="global">
  <p>Our analysis of over 2,500 project managers aged {age} across Singapore, Malaysia, and Taiwan reveals that <strong>resource allocation</strong> is cited by 72% as their top challenge…</p>
  <p>Organisations focusing on <em>{focus}</em> have increased risk-management budgets by 15% YOY…</p>
  <p>Forecasts show teams embedding these frameworks will see a 20% uplift… Recommendations:<br>
    1) Quarterly risk audits…<br>
    2) Scenario-based workshops…<br>
    3) Real-time dashboards…</p>
</div>
"""
    else:
        widget_html += f"""
<h2 class="sub">🌐 Global Section Analytical Report</h2>
<div class="global">
  <p>In a survey of 3,000+ finance directors aged {age} in Malaysia, cost optimization topped the agenda…</p>
  <p>High performers in <em>{focus}</em> boosted analytics budgets by 14% YOY…</p>
  <p>Continuous forecasting projects 15% better accuracy… We advise:<br>
    1) Benchmark models…<br>
    2) Steering committees…<br>
    3) Rolling forecasts…</p>
</div>
"""
    # Return JSON
    return jsonify({
        "metrics": metrics,
        "analysis": widget_html
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
