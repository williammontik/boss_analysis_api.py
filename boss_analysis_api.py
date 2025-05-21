import os
import random
import smtplib
from datetime import datetime
from dateutil import parser
from email.mime.text import MIMEText

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

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
    except:
        bd = datetime.today()
    today = datetime.today()
    return today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))

def send_email(html_body: str):
    msg = MIMEText(html_body, 'html')
    msg["Subject"] = "New Boss Submission"
    msg["From"]    = SMTP_USERNAME
    msg["To"]      = SMTP_USERNAME
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as s:
        s.starttls()
        s.login(SMTP_USERNAME, SMTP_PASSWORD)
        s.send_message(msg)

@app.route("/boss_analyze", methods=["POST"])
def boss_analyze():
    data = request.get_json(force=True)

    # Extract fields
    position   = data.get("position","").strip()
    department = data.get("department","").strip()
    experience = data.get("experience","").strip()
    sector     = data.get("sector","").strip()
    challenge  = data.get("challenge","").strip()
    focus      = data.get("focus","").strip()
    country    = data.get("country","").strip()

    age = compute_age(data)

    # Fixed metrics
    metrics = [
        {"title":"Communication Efficiency","labels":["Segment","Regional","Global"],"values":[79,65,74]},
        {"title":"Leadership Readiness","labels":["Segment","Regional","Global"],"values":[63,68,76]},
        {"title":"Task Completion Reliability","labels":["Segment","Regional","Global"],"values":[82,66,84]},
    ]

    # Build widget fragment
    analysis_html = f"""<h2 class="header">🎉 AI Team Member Performance Insights:</h2>
<div class="charts-row">
  <div class="chart-item"><canvas id="c0"></canvas></div>
  <div class="chart-item"><canvas id="c1"></canvas></div>
  <div class="chart-item"><canvas id="c2"></canvas></div>
</div>
<h2 class="sub">📄 Workplace Performance Report</h2>
<div class="narrative">
• Age: {age}<br>
• Position: {position}<br>
• Department: {department}<br>
• Experience: {experience} year(s)<br>
• Sector: {sector}<br>
• Country: {country}<br>
• Main Challenge: {challenge}<br>
• Development Focus: {focus}<br>
📊 Workplace Metrics:<br>
• Communication Efficiency: Segment 79%, Regional 65%, Global 74%<br>
• Leadership Readiness: Segment 63%, Regional 68%, Global 76%<br>
• Task Completion Reliability: Segment 82%, Regional 66%, Global 84%<br>
</div>
<h2 class="sub">🌐 Global Section Analytical Report</h2>
<div class="global">
  <p>In a survey of over 2,000 {position}s across {country}, “{challenge}” was cited by 71% of peers—reflecting pressures specific to the {sector} sector.</p>
  <p>Deep dives into your development focus—{focus}—show leading organizations increasing investment by 14% year-on-year, driving an average 9% lift in core performance metrics.</p>
  <p>Looking ahead, teams embedding best practices around {focus} are projected to deliver up to a 12% uplift in outcomes. We recommend:<br>
  1) Roll out sector-specific workshops on {focus}.<br>
  2) Integrate real-time dashboards tailored to {challenge}.<br>
  3) Establish peer-mentorship pods for continuous improvement.</p>
</div>"""

    # Send the HTML via email
    send_email(analysis_html)

    # Append Chart.js script
    analysis_html += """
<script>
const pal=['#5E9CA0','#FF9F40','#9966FF'];
[[79,65,74,'Communication Efficiency'],[63,68,76,'Leadership Readiness'],[82,66,84,'Task Completion Reliability']]
.forEach(([s,r,g,title],i) => {
  new Chart(document.getElementById('c'+i).getContext('2d'), {
    type:'bar',
    data:{ labels:['Segment','Regional','Global'], datasets:[{ label:title, data:[s,r,g], backgroundColor:pal, borderColor:pal, borderWidth:1, borderRadius:6 }] },
    options:{ responsive:true, plugins:{ legend:{display:false}, title:{display:true,text:title,font:{size:18}}}, scales:{ y:{ beginAtZero:true, max:100, ticks:{ stepSize:20 }, grid:{ color:'#f0f0f0'} } } }
  });
});
</script>
"""

    return jsonify({
        "metrics": metrics,
        "analysis": analysis_html
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
