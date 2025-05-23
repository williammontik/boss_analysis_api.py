# -*- coding: utf-8 -*-
import os
import random
import traceback
from datetime import datetime
from dateutil import parser
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from email.mime.text import MIMEText
import smtplib

app = Flask(__name__)
CORS(app)
app.logger.setLevel("DEBUG")

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
    try:
        d, m, y = data.get("dob_day"), data.get("dob_month"), data.get("dob_year")
        if d and m and y:
            month = int(m) if m.isdigit() else datetime.strptime(m, "%B").month
            bd = datetime(int(y), month, int(d))
        else:
            bd = parser.parse(data.get("dob",""), dayfirst=True)
        today = datetime.today()
        return today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
    except Exception as e:
        app.logger.error("Error computing age: %s", e)
        return 0

def send_email(html_body: str):
    try:
        msg = MIMEText(html_body, 'html')
        msg["Subject"] = "Your Workplace Performance Report"
        msg["From"]    = SMTP_USERNAME
        msg["To"]      = SMTP_USERNAME
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        app.logger.info("✅ Email sent")
    except Exception as e:
        app.logger.error("❌ Failed to send email: %s", e)

@app.route("/boss_analyze", methods=["POST"])
def boss_analyze():
    app.logger.info("→ /boss_analyze called")
    try:
        data = request.get_json(force=True)
        app.logger.debug("Payload: %s", data)
    except Exception as e:
        app.logger.error("❌ JSON parse error: %s", e)
        return jsonify(error="Invalid JSON"), 400

    # 1) Extract & log
    position   = (data.get("position") or "").strip()
    challenge  = (data.get("challenge") or "").strip()
    focus      = (data.get("focus") or "").strip()
    app.logger.info("Position=%s, Challenge=%s, Focus=%s",
                    position, challenge, focus)

    # 2) Compute age
    age = compute_age(data)
    app.logger.info("Computed age: %s", age)

    # 3) Generate metrics
    metrics = []
    for title, color in [
        ("Communication Efficiency", "#5E9CA0"),
        ("Leadership Readiness",      "#FF9F40"),
        ("Task Completion Reliability","#9966FF"),
    ]:
        seg, reg, glo = random.randint(60,90), random.randint(55,85), random.randint(60,88)
        metrics.append((title, seg, reg, glo, color))
        app.logger.debug("Metric %s → %s,%s,%s", title, seg, reg, glo)

    # 4) Build bar_html
    bar_html = ""
    for title, seg, reg, glo, color in metrics:
        bar_html += f"<strong>{title}</strong><br>"
        for v in (seg, reg, glo):
            bar_html += (
                f"<span style='display:inline-block;width:{v}%;height:12px;"
                f"background:{color};margin-right:6px;border-radius:4px;'></span> {v}%<br>"
            )
        bar_html += "<br>"

    # 5) Bullet summary
    report_html = "<br>\n<br>\n<br>\n<h2 class='sub'>📄 Workplace Performance Report</h2>\n<div class='narrative'>"
    for label, val in [
        ("Age", age), ("Position", position), ("Key Challenge", challenge), ("Preferred Focus", focus)
    ]:
        report_html += f"• {label}: {val}<br>"
    report_html += "</div>\n"

    # 6) Global section
    global_header = "<h2 class='sub'>🌐 Global Section Analytical Report</h2>\n<div class='global'>\n"
    prompt_global = (
        f"You are an expert business analyst. Write a 7-paragraph analytical report for a {position}, "
        f"age {age}, focused on “{focus}” and challenged by “{challenge}”."
    )
    app.logger.debug("Global prompt: %s", prompt_global)
    try:
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"user","content":prompt_global}],
            temperature=0.7
        )
        global_html = resp.choices[0].message.content + "</div>\n"
        app.logger.info("✅ Global section generated")
    except Exception as e:
        app.logger.error("❌ OpenAI global call failed: %s", e)
        global_html = "<p>Error generating global analysis.</p></div>\n"

    # 7) Creative approaches
    creative_header = "<h3>Creative Innovation Approaches</h3>\n<div class='creative'>\n"
    creative_prompt = (
        f"For a {position} whose challenge is “{challenge}” and focus is “{focus}”, "
        "list 10 creative, actionable approaches, numbered 1-10."
    )
    app.logger.debug("Creative prompt: %s", creative_prompt)
    try:
        resp2 = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"user","content":creative_prompt}],
            temperature=0.8
        )
        lines = resp2.choices[0].message.content.split("\n")
        creative_html = creative_header + "".join(f"<p>{ln}</p>\n" for ln in lines if ln.strip()) + "</div>\n"
        app.logger.info("✅ Creative section generated")
    except Exception as e:
        app.logger.error("❌ OpenAI creative call failed: %s", e)
        creative_html = "<p>Error generating creative approaches.</p></div>\n"

    # 8) Footer
    footer = """
<div style="background-color:#e6f7ff;color:#00529B;...">…PDPA footer…</div>
"""

    # 9) Assemble
    full_html = bar_html + report_html + global_header + global_html + creative_html + footer
    app.logger.debug("Final HTML length: %d", len(full_html))

    # 10) Send email
    send_email(full_html)

    # 11) Return JSON
    return jsonify(
        metrics=[{"title":t,"labels":["Segment","Regional","Global"],"values":[s,r,g]} 
                 for t,s,r,g,_ in metrics],
        analysis=full_html
    )

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT",5000)))
