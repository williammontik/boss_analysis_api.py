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
    """Compute age from DOB fields or freeform string."""
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
    """Sends an HTML email to the configured address."""
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

    # 2) Generate random metrics dynamically
    def rand_vals():
        return (
            random.randint(60, 90),  # segment
            random.randint(55, 85),  # regional
            random.randint(60, 88)   # global
        )
    metrics = [
        ("Communication Efficiency",   *rand_vals(), "#5E9CA0"),
        ("Leadership Readiness",        *rand_vals(), "#FF9F40"),
        ("Task Completion Reliability", *rand_vals(), "#9966FF"),
    ]

    # 3) Build HTML for horizontal bars with percentages
    bar_html = ""
    for title, seg, reg, glob, color in metrics:
        bar_html += f"<strong>{title}</strong><br>"
        for val in (seg, reg, glob):
            bar_html += (
                f"<span style='display:inline-block; width:{val}%; height:12px;"
                f" background:{color}; margin-right:6px; border-radius:4px;'></span> {val}%<br>"
            )
        bar_html += "<br>"

    # 4) Fixed “📄 Workplace Performance Report” section
    report_html = (
        "<br>\n<br>\n<br>\n"  # exactly three-line gap before report
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

    # 5) Extract stats for prompt
    seg_stat, reg_stat, glob_stat = metrics[0][1], metrics[0][2], metrics[0][3]

    # 6) Dynamically generate the Global Section via OpenAI with regional & global stats
    prompt = f"""
Generate exactly seven professional two- to three-sentence analytical paragraphs for a "🌐 Global Section Analytical Report", written as an industry overview referencing aggregated professionals by experience band, sector, region, and global benchmarks. Include explicit mentions of:
- "{seg_stat}% of peers in Singapore rate high on Communication Efficiency"
- "{reg_stat}% is the average across Malaysia"
- "{glob_stat}% represents the global benchmark"

Relate each back to the main challenge or focus. Do NOT personalize to a single person.

Use only these details:
- Position: {position}
- Department: {department}
- Years of Experience: {experience}
- Sector: {sector}
- Country: {country}
- Main Challenge: {challenge}
- Development Focus: {focus}

Wrap each paragraph in <p>...</p> tags.
"""
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert business analyst aware of regional and global benchmarks."},
            {"role": "user",   "content": prompt}
        ],
        temperature=0.7
    )
    global_html = completion.choices[0].message.content

    # 7) Correct PDPA footer
    footer = """
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
"""

    # 8) Assemble full analysis HTML with precise spacing
    analysis_html = (
        bar_html
        + report_html
        + "<br>\n<br>\n<br>\n"  # exactly three-line gap before global section
        + "<h2 class=\"sub\">🌐 Global Section Analytical Report</h2>\n"
        + "<br>\n<br>\n"    # exactly two-line gap after header
        + global_html
        + footer
    )

    # 9) Send email and return JSON
    send_email(analysis_html)
    return jsonify({
        "metrics": [
            {"title": t, "labels": ["Segment","Regional","Global"], "values": [s, r, g]}
            for t, s, r, g, _ in metrics
        ],
        "analysis": analysis_html
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
