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

app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.DEBUG)

openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise RuntimeError("OPENAI_API_KEY environment variable is not set.")
client = OpenAI(api_key=openai_api_key)

SMTP_SERVER   = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USERNAME = "kata.chatbot@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
if not SMTP_PASSWORD:
    app.logger.warning("SMTP_PASSWORD is not set; emails may fail.")

def send_email(html_body):
    """Sends HTML email to kata.chatbot@gmail.com."""
    msg = MIMEText(html_body, 'html')
    msg["Subject"] = "New KataChatBot Boss Submission"
    msg["From"]    = SMTP_USERNAME
    msg["To"]      = SMTP_USERNAME
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        app.logger.info("✅ Boss HTML email sent successfully.")
    except Exception:
        app.logger.error("❌ Boss email sending failed.", exc_info=True)

@app.route("/boss_analyze", methods=["POST"])
def boss_analyze():
    data = request.get_json(force=True)
    try:
        app.logger.info(f"[boss_analyze] payload: {data}")

        # 1) Extract form fields
        member_name    = data.get("memberName","")
        position       = data.get("position","")
        department     = data.get("department","")
        experience     = data.get("experience","")
        sector         = data.get("sector","")
        challenge      = data.get("challenge","")
        focus          = data.get("focus","")
        email_addr     = data.get("email","")
        country        = data.get("country","")
        dob_day        = data.get("dob_day","")
        dob_month      = data.get("dob_month","")
        dob_year       = data.get("dob_year","")
        referrer       = data.get("referrer","")
        contact_number = data.get("contactNumber","")

        # 2) Build prompt
        prompt = f"""
You are an expert organizational psychologist.
Generate a detailed performance report for a team member named "{member_name}",
working as "{position}", who faces this key challenge:
"{challenge}". Their preferred development focus is "{focus}", and they are located in "{country}".

Requirements:
1. Return exactly three bar-chart metrics in JSON.
2. Provide a 150–200 word narrative in the "analysis" field.
"""

        # 3) Call OpenAI
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"user","content":prompt}]
        )
        report = re.sub(r"<[^>]+>","", resp.choices[0].message.content.strip())
        # assume JSON parse here:
        result = __import__('json').loads(report)
        metrics = result["metrics"]
        analysis = result["analysis"]

        # 4) Build HTML email with submission + inline CSS bar charts + narrative
        html = f"""
        <html><body style="font-family:sans-serif; color:#333;">
          <h2>🧑‍💼 New Boss Section Submission:</h2>
          <p>
            <strong>👤 Name:</strong> {member_name}<br>
            <strong>🏢 Position:</strong> {position}<br>
            <strong>📂 Department:</strong> {department}<br>
            <strong>🗓️ Experience:</strong> {experience}<br>
            <strong>📌 Sector:</strong> {sector}<br>
            <strong>⚠️ Challenge:</strong> {challenge}<br>
            <strong>🌟 Focus:</strong> {focus}<br>
            <strong>📧 Email:</strong> {email_addr}<br>
            <strong>🌍 Country:</strong> {country}<br>
            <strong>🎂 DOB:</strong> {dob_day} {dob_month} {dob_year}<br>
            <strong>💬 Referrer:</strong> {referrer}<br>
            <strong>📞 In‐Charge Contact:</strong> {contact_number}
          </p>
          <hr>
          <h2>📄 AI‐Generated Performance Report</h2>
          <div style="font-size:14px; white-space:pre-wrap; margin-bottom:20px;">
            {analysis}
          </div>
          <h2>📊 Charts</h2>
          <div style="font-size:14px; max-width:600px;">
        """
        # inline CSS bars
        palette = ["#5E9CA0","#FF9F40","#9966FF"]
        for m in metrics:
            html += f"<strong>{m['title']}</strong><br>"
            for idx,(lbl,val) in enumerate(zip(m["labels"],m["values"])):
                c = palette[idx%len(palette)]
                html += (
                  f"<div style='margin:4px 0;'>{lbl}: "
                  f"<span style='display:inline-block; width:{val}%; height:12px; background:{c}; border-radius:4px;'></span> {val}%</div>"
                )
            html += "<br>"
        html += "</div></body></html>"

        # 5) Send email
        send_email(html)

        # 6) Return JSON to front-end
        return jsonify(metrics=metrics, analysis=analysis)

    except Exception as e:
        app.logger.exception("Error in /boss_analyze")
        return jsonify(error=str(e)), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
