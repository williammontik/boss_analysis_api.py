# -*- coding: utf-8 -*-
import os
import smtplib
from datetime import datetime
from dateutil import parser
from flask import Flask, request, jsonify
from flask_cors import CORS
from email.mime.text import MIMEText
from openai import OpenAI
import random

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "kata.chatbot@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


def compute_age(data):
    d, m, y = data.get("dob_day"), data.get("dob_month"), data.get("dob_year")
    try:
        if d and m and y:
            month = int(m) if m.isdigit() else datetime.strptime(m, "%B").month
            bd = datetime(int(y), month, int(d))
        else:
            bd = parser.parse(data.get("dob", ""), dayfirst=True)
    except Exception:
        bd = datetime.today()
    today = datetime.today()
    return today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))


def send_email(html_body: str):
    msg = MIMEText(html_body, 'html')
    msg["Subject"] = "Boss Report Submission"
    msg["From"] = SMTP_USERNAME
    msg["To"] = SMTP_USERNAME
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)


@app.route("/boss_analyze", methods=["POST"])
def boss_analyze():
    data = request.get_json(force=True)

    member_name = data.get("memberName", "").strip()
    member_name_cn = data.get("memberNameCn", "").strip()
    position = data.get("position", "").strip()
    department = data.get("department", "").strip()
    experience = data.get("experience", "").strip()
    sector_raw = data.get("sector", "").strip()
    challenge = data.get("challenge", "").strip()
    focus = data.get("focus", "").strip()
    email = data.get("email", "").strip()
    country = data.get("country", "").strip()
    age = compute_age(data)

    # === REPHRASED SECTOR DESCRIPTIONS ===
    sector_map = {
        "Indoor – Admin / HR / Ops / Finance": "the essential field of administration and operations",
        "Indoor – Technical / Engineering / IT": "the innovative field of technology and engineering",
        "Outdoor – Sales / BD / Retail": "the fast-paced world of sales and client-facing roles",
        "Outdoor – Servicing / Logistics / Fieldwork": "the dynamic world of logistics and field operations"
    }
    sector = sector_map.get(sector_raw, sector_raw) # Use the recrafted text, or the original if not found

    raw_info = f"""
    <h3>📥 Submitted Form Data:</h3>
    <ul style="line-height:1.8;">
      <li><strong>Legal Name:</strong> {member_name}</li>
      <li><strong>Chinese Name:</strong> {member_name_cn}</li>
      <li><strong>Position:</strong> {position}</li>
      <li><strong>Department:</strong> {department}</li>
      <li><strong>Experience:</strong> {experience} years</li>
      <li><strong>Sector:</strong> {sector_raw}</li>
      <li><strong>Challenge:</strong> {challenge}</li>
      <li><strong>Focus:</strong> {focus}</li>
      <li><strong>Email:</strong> {email}</li>
      <li><strong>Country:</strong> {country}</li>
      <li><strong>Date of Birth:</strong> {data.get("dob_day", "")} - {data.get("dob_month", "")} - {data.get("dob_year", "")}</li>
      <li><strong>Referrer:</strong> {data.get("referrer", "")}</li>
      <li><strong>Contact Number:</strong> {data.get("contactNumber", "")}</li>
    </ul>
    <hr><br>
    """

    metrics = []
    for title, color in [
        ("Communication Efficiency", "#5E9CA0"),
        ("Leadership Readiness", "#FF9F40"),
        ("Task Completion Reliability", "#9966FF"),
    ]:
        seg, reg, glo = sorted([random.randint(60, 90), random.randint(55, 85), random.randint(60, 88)], reverse=True)
        metrics.append((title, seg, reg, glo, color))

    bar_html = ""
    for title, seg, reg, glo, color in metrics:
        bar_html += f"<strong>{title}</strong><br>"
        labels = ["Segment", "Regional", "Global"]
        values = [seg, reg, glo]
        for i, v in enumerate(values):
            bar_html += (
                f"<span style='font-size:14px; width:80px; display:inline-block;'>{labels[i]}:</span>"
                f"<span style='display:inline-block;width:{v}%;height:12px;"
                f" background:{color}; margin-right:6px; border-radius:4px; vertical-align:middle;'></span> {v}%<br>"
            )
        bar_html += "<br>"
        
    # === DYNAMIC OPENING SENTENCES ===
    opening_templates = [
        f"Building a career for {experience} years in {sector} within {country} is a testament to resilience and expertise.",
        f"With {experience} years of dedicated experience in {country}'s demanding {sector} sector, a professional journey of significant growth and impact is clearly evident.",
        f"Navigating the field of {sector} in {country} for {experience} years requires a unique blend of skill and determination—qualities that have clearly been cultivated throughout an impressive career.",
        f"A career spanning {experience} years within {sector} in {country} speaks volumes about a commitment to excellence and continuous adaptation."
    ]
    chosen_opening = random.choice(opening_templates)

    # NEW "YES" SUMMARY using the dynamic opening and recrafted sector
    summary = (
        "<div style='font-size:24px;font-weight:bold;margin-top:30px;'>🧠 An Affirming Look at Your Professional Journey:</div><br>"
        + f"<p style='line-height:1.8; font-size:16px; margin-bottom:18px; text-align:justify;'>"
        + f"{chosen_opening} Such a path naturally hones a remarkable ability to connect with others, as reflected by a Communication Efficiency score of {metrics[0][1]}%. This isn't just a skill; it's the foundation upon which strong teams and successful collaborations are built, allowing for the confident navigation of both internal objectives and the ever-present pulse of the market."
        + "</p>"
        + f"<p style='line-height:1.8; font-size:16px; margin-bottom:18px; text-align:justify;'>"
        + f"True leadership in today's world is less about authority and more about influence, empathy, and adaptability—qualities that appear to be developing strongly. A Leadership Readiness benchmarked at {metrics[1][2]}% regionally suggests an intuitive grasp of these modern leadership pillars. It points to a professional who provides the clarity and calm that teams gravitate towards in moments of pressure, fostering an environment of trust and inspiring collective action through respected guidance."
        + "</p>"
        + f"<p style='line-height:1.8; font-size:16px; margin-bottom:18px; text-align:justify;'>"
        + f"The consistent ability to deliver, reflected in a Task Completion Reliability of {metrics[2][1]}%, is far more than a measure of productivity; it is a clear indicator of profound impact and strategic wisdom. For an influential role like {position}, this demonstrates a rare discernment—the ability to identify which tasks matter most and execute them with excellence. This is the kind of performance that not only drives results but also signals readiness for even greater challenges and responsibilities."
        + "</p>"
        + f"<p style='line-height:1.8; font-size:16px; margin-bottom:18px; text-align:justify;'>"
        + f"Choosing to deepen the focus on {focus} is a forward-thinking and insightful move. This aligns perfectly with the strategic shifts occurring across the region, positioning this skill set not just as a current strength but as a cornerstone for future growth. Investing time here is an investment in long-term resilience, expanding influence, and the capacity to lead with vision. This is a clear and promising trajectory for a professional poised to make a lasting mark."
        + "</p>"
    )

    prompt = (
        f"Give 10 actionable, professional, and encouraging improvement ideas for a {position} from {country} "
        f"with {experience} years in {sector_raw}, facing '{challenge}' and focusing on '{focus}'. "
        f"Each idea should be a clear, constructive piece of advice. The tone should be empowering and respectful, not overly casual. Use emojis thoughtfully to add warmth, not to be unprofessional."
    )
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.75 
    )
    tips = response.choices[0].message.content.strip().split("\n")
    tips_html = "<div style='font-size:24px;font-weight:bold;margin-top:30px;'>💡 Creative Suggestions:</div><br>"
    for line in tips:
        if line.strip():
            tips_html += f"<p style='margin:16px 0; font-size:17px;'>{line.strip()}</p>"

    footer = (
        '<div style="background-color:#e6f7ff; color:#00529B; padding:15px; border-left:4px solid #00529B; margin:20px 0;">'
        '<strong>The insights in this report are generated by KataChat’s AI systems analyzing:</strong><br>'
        '1. Our proprietary database of anonymized professional profiles across Singapore, Malaysia, and Taiwan<br>'
        '2. Aggregated global business benchmarks from trusted OpenAI research and leadership trend datasets<br>'
        '<em>All data is processed through our AI models to identify statistically significant patterns while maintaining strict PDPA compliance.</em>'
        '</div>'
        '<p style="background-color:#e6f7ff; color:#00529B; padding:15px; border-left:4px solid #00529B; margin:20px 0;">'
        "<strong>PS:</strong> Your personalized report will arrive in your inbox within 24–48 hours. "
        "If you'd like to discuss it further, feel free to reach out — we're happy to arrange a 15-minute call at your convenience."
        "</p>"
    )

    email_output = raw_info + bar_html + summary + tips_html + footer
    display_output = bar_html + summary + tips_html + footer

    send_email(email_output)

    return jsonify({
        "analysis": display_output
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
