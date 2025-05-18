import os
import smtplib
import logging
from email.mime.text import MIMEText
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.DEBUG)

SMTP_SERVER   = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USERNAME = "kata.chatbot@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
if not SMTP_PASSWORD:
    app.logger.warning("SMTP_PASSWORD is not set; emails may fail.")

def send_email(full_name, position, department, experience, sector,
               challenge, focus, email_addr, country,
               dob_formatted, referrer, contact_number,
               report_analysis, metrics):
    """
    Sends a multipart HTML email containing both submission data,
    the AI narrative, and inline-CSS bar charts.
    """
    # Build HTML body
    html = f"""
    <html><body style="font-family:sans-serif; color:#333;">
      <h2>🧑‍💼 New Boss Section Submission:</h2>
      <p>
        <strong>👤 Name:</strong> {full_name}<br>
        <strong>🏢 Position:</strong> {position}<br>
        <strong>📂 Department:</strong> {department}<br>
        <strong>🗓️ Experience:</strong> {experience}<br>
        <strong>📌 Sector:</strong> {sector}<br>
        <strong>⚠️ Challenge:</strong> {challenge}<br>
        <strong>🌟 Focus:</strong> {focus}<br>
        <strong>📧 Email:</strong> {email_addr}<br>
        <strong>🌍 Country:</strong> {country}<br>
        <strong>🎂 DOB:</strong> {dob_formatted}<br>
        <strong>💬 Referrer:</strong> {referrer}<br>
        <strong>📞 In‐Charge Contact:</strong> {contact_number}
      </p>
      <hr>
      <h2>📄 AI‐Generated Performance Report</h2>
      <div style="font-size:14px; white-space:pre-wrap; margin-bottom:20px;">
        {report_analysis}
      </div>
      <h2>📊 Charts</h2>
      <div style="font-size:14px; max-width:600px;">
    """

    # Inline‐CSS bar charts (palette matches your front end)
    palette = ["#5E9CA0","#FF9F40","#9966FF"]
    for m in metrics:
        html += f"<strong>{m['title']}</strong><br>"
        for idx, lbl in enumerate(m["labels"]):
            val = m["values"][idx]
            color = palette[idx % len(palette)]
            html += (
              f"<div style='margin:4px 0;'>"
              f"{lbl}: "
              f"<span style='display:inline-block; width:{val}%; height:12px; background:{color}; border-radius:4px;'></span> {val}%"
              f"</div>"
            )
        html += "<br>"

    html += "</div></body></html>"

    msg = MIMEText(html, 'html')
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
    try:
        data = request.get_json(force=True)
        app.logger.info(f"[boss_analyze] payload: {data}")

        # Extract fields
        member_name    = data.get("memberName", "")
        position       = data.get("position", "")
        department     = data.get("department", "")
        experience     = data.get("experience", "")
        sector         = data.get("sector", "")
        challenge      = data.get("challenge", "")
        focus          = data.get("focus", "")
        email_addr     = data.get("email", "")
        country        = data.get("country", "")
        dob_day        = data.get("dob_day", "")
        dob_month      = data.get("dob_month", "")
        dob_year       = data.get("dob_year", "")
        referrer       = data.get("referrer", "")
        contact_number = data.get("contactNumber", "")

        # Format DOB string
        dob_formatted = f"{dob_day} {dob_month} {dob_year}"

        # -- Existing AI / logic placeholder --
        # (keep your existing prompt → OpenAI → parse logic if you have it;
        #  otherwise you can stick with dummy metrics/analysis as before)

        # For illustration, using your original dummy metrics + analysis:
        metrics = [
            {
                "title": "Leadership Execution",
                "labels": ["Teamwork", "Responsibility", "Problem Solving"],
                "values": [72, 85, 67]
            },
            {
                "title": "Communication Effectiveness",
                "labels": ["Clarity", "Feedback", "Openness"],
                "values": [78, 69, 83]
            },
            {
                "title": "Growth Potential",
                "labels": ["Initiative", "Adaptability", "Vision"],
                "values": [88, 74, 91]
            }
        ]
        report_analysis = (
            "• Leadership is strong; focus on Problem Solving improvements.\n"
            "• Communication Clarity is high; look to bolster Feedback.\n"
            "• Growth Potential is excellent in Adaptability and Vision.\n"
        )

        # Send the enhanced email
        send_email(
            member_name, position, department, experience, sector,
            challenge, focus, email_addr, country,
            dob_formatted, referrer, contact_number,
            report_analysis, metrics
        )

        # Return exactly the same JSON your widget expects
        return jsonify({"metrics": metrics, "analysis": report_analysis})

    except Exception as e:
        app.logger.exception("Error in /boss_analyze")
        return jsonify(error=str(e)), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
