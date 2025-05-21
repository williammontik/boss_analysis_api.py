# boss_analysis.py
import os
import smtplib
import random
from datetime import datetime
from dateutil import parser
from email.mime.text import MIMEText

from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)

# Setup OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# Email Setup
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "kata.chatbot@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def compute_age(data):
    try:
        d, m, y = data.get("dob_day"), data.get("dob_month"), data.get("dob_year")
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
    msg["From"] = SMTP_USERNAME
    msg["To"] = SMTP_USERNAME
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)

@app.route("/boss_analyze", methods=["POST"])
def boss_analyze():
    data = request.get_json()
    
    # Extract data
    position = data.get("position","").strip()
    department = data.get("department","").strip()
    experience = data.get("experience","").strip()
    sector = data.get("sector","").strip()
    challenge = data.get("challenge","").strip()
    focus = data.get("focus","").strip()
    country = data.get("country","").strip()
    age = compute_age(data)

    # Generate metrics
    def rand_vals():
        return (random.randint(60,90), random.randint(55,85), random.randint(60,88))
    
    metrics = [
        ("Communication Efficiency", *rand_vals(), "#5E9CA0"),
        ("Leadership Readiness", *rand_vals(), "#FF9F40"),
        ("Task Completion Reliability", *rand_vals(), "#9966FF"),
    ]

    # Build HTML elements
    bar_html = ""
    for title, seg, reg, glob, color in metrics:
        bar_html += f"<strong>{title}</strong><br>"
        for val in (seg, reg, glob):
            bar_html += f"""<span style='display:inline-block; width:{val}%; 
                           height:12px; background:{color}; margin-right:6px; 
                           border-radius:4px;'></span> {val}%<br>"""
        bar_html += "<br>"

    report_html = f"""
    <br>
    <h2 class="sub">📄 Workplace Performance Report</h2>
    • Age: {age}<br>
    • Position: {position}<br>
    • Department: {department}<br>
    • Experience: {experience} year(s)<br>
    • Sector: {sector}<br>
    • Country: {country}<br>
    • Main Challenge: {challenge}<br>
    • Development Focus: {focus}<br>
    <br><br><br>
    """

    # Generate AI content
    seg_stat, reg_stat, glob_stat = metrics[0][1], metrics[0][2], metrics[0][3]
    prompt = f"""
    Generate exactly seven professional paragraphs for a "🌐 Global Section Analytical Report".
    Include:
    - "{seg_stat}% of peers in Singapore"
    - "{reg_stat}% average in Malaysia"
    - "{glob_stat}% global benchmark"
    Relate to: {challenge} and {focus}.
    Wrap each in <p> tags.
    """
    
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role":"system","content":"Expert business analyst"},
            {"role":"user","content":prompt}
        ],
        temperature=0.7
    )
    global_html = completion.choices[0].message.content

    # Final assembly
    analysis_html = (
        bar_html 
        + report_html 
        + "<h2 style='margin:1.5em 0;'>🌐 Global Section Analytical Report</h2>"
        + global_html
        + """
        <div style="background:#e6f7ff; color:#00529B; padding:15px; 
                    border-left:4px solid #00529B; margin:20px 0;">
          <strong>Data Insights:</strong><br>
          AI analysis of professional data with PDPA compliance.
        </div>
        """
    )

    send_email(analysis_html)
    return jsonify({
        "metrics": [{"title":t,"values":[s,r,g]} for t,s,r,g,_ in metrics],
        "analysis": analysis_html
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
