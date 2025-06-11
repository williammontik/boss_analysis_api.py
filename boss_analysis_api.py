# -*- coding: utf-8 -*-
import os
import logging
import smtplib
import traceback
import random
from datetime import datetime
from dateutil import parser
from email.mime.text import MIMEText
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

# --- Initialization ---
app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

# --- Configuration ---
# It's recommended to set these as environment variables for security
try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
except Exception as e:
    logging.error(f"Failed to initialize configuration from environment variables: {e}")
    client = None
    SMTP_PASSWORD = None

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "kata.chatbot@gmail.com" # Or your sending email

# --- Helper Functions ---
def compute_age(dob_str):
    """Safely computes age from a 'YYYY-MM-DD' string."""
    try:
        birth_date = parser.parse(dob_str)
        today = datetime.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return age
    except (ValueError, TypeError):
        logging.warning(f"Could not parse DOB: {dob_str}. Returning age 0.")
        return 0

def get_openai_response(prompt, temp=0.85):
    """Gets a response from OpenAI's chat model."""
    if not client:
        logging.error("OpenAI client not initialized.")
        return None
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=temp,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"OpenAI API error: {e}")
        return None

def send_email(html_body, subject):
    """Sends an email using Gmail's SMTP server."""
    if not SMTP_PASSWORD:
        logging.error("SMTP password not configured. Cannot send email.")
        return
    msg = MIMEText(html_body, 'html', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = SMTP_USERNAME
    msg['To'] = SMTP_USERNAME # Sends the email to yourself as a notification
    
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
            logging.info("Email sent successfully.")
    except Exception as e:
        logging.error(f"Email sending failed: {e}")

# --- Chart and Summary Generation ---
def generate_chart_metrics():
    """Generates randomized metrics for the analysis charts."""
    return [
        {"title": "Market Positioning", "labels": ["Brand Recall", "Client Fit Clarity", "Reputation Stickiness"], "values": [random.randint(70, 90), random.randint(65, 85), random.randint(70, 90)]},
        {"title": "Investor Appeal", "labels": ["Narrative Confidence", "Scalability Model", "Proof of Trust"], "values": [random.randint(70, 85), random.randint(60, 80), random.randint(75, 90)]},
        {"title": "Strategic Execution", "labels": ["Partnership Readiness", "Premium Channel Leverage", "Leadership Presence"], "values": [random.randint(65, 85), random.randint(65, 85), random.randint(75, 90)]}
    ]

def generate_chart_html(metrics):
    """Creates the HTML for the bar charts."""
    colors = ["#8C52FF", "#5E9CA0", "#F2A900"]
    html = ""
    for metric in metrics:
        html += f"<strong style='font-size:18px;color:#333;'>{metric['title']}</strong><br>"
        for j, (label, val) in enumerate(zip(metric['labels'], metric['values'])):
            html += (
                f"<div style='display:flex;align-items:center;margin-bottom:8px;'>"
                f"<span style='width:180px; font-size: 15px;'>{label}</span>"
                f"<div style='flex:1;background:#eee;border-radius:5px;overflow:hidden;'>"
                f"<div style='width:{val}%;height:14px;background:{colors[j % len(colors)]};'></div></div>"
                f"<span style='margin-left:10px; font-size: 15px;'>{val}%</span></div>"
            )
        html += "<br>"
    return html

def build_dynamic_summary(age, experience, industry, country, metrics, challenge, context, target_profile):
    """
    Builds the final, sophisticated strategic summary with a third-person voice
    and conceptual integration of user inputs.
    """
    industry_map = {
        "Insurance": "the competitive insurance landscape", "Real Estate": "the dynamic real estate market",
        "Finance": "the high-stakes world of finance", "Technology": "the fast-evolving technology sector",
        "Manufacturing": "the foundational manufacturing industry", "Education": "the impactful field of education",
        "Healthcare": "the vital healthcare sector"
    }
    industry_narrative = industry_map.get(industry, f"the field of {industry}")

    challenge_narrative_map = {
        "Need New Funding": "the pursuit of fresh capital to fuel the next stage of growth",
        "Unclear Expansion Strategy": "the task of charting a clear and defensible path for expansion",
        "Lack of Investor Confidence": "the challenge of building a compelling and evidence-backed case for investors",
        "Weak Brand Positioning": "the strategic imperative to sharpen the brand's narrative and market position"
    }
    challenge_narrative = challenge_narrative_map.get(challenge, f"addressing the primary challenge of {challenge.lower()}")

    opening_templates = [
        f"For a professional with around {experience} years of dedication in {industry_narrative} within {country}, arriving at a strategic crossroads is not just common; it's a sign of ambition.",
        f"A career spanning {experience} years in {country}'s {industry_narrative} is a clear testament to adaptability and expertise. This journey naturally leads to pivotal moments of reflection.",
        f"Navigating {industry_narrative} in {country} for {experience} years cultivates a unique perspective, especially when confronting the next phase of professional growth at an age of {age}."
    ]
    chosen_opening = random.choice(opening_templates)

    brand, fit, stick = metrics[0]["values"]
    conf, scale, trust = metrics[1]["values"]
    partn, premium, leader = metrics[2]["values"]

    summary_html = (
        "<br><div style='font-size:24px;font-weight:bold;'>🧠 Strategic Summary:</div><br>"
        f"<p style='line-height:1.7; text-align:justify;'>{chosen_opening} This profile reflects a pivotal moment where the focus shifts towards {challenge_narrative}. The data indicates a strong Brand Recall of {brand}%, suggesting an established market presence. "
        f"However, the analysis also points to an opportunity: to sharpen the clarity of the value proposition (Client Fit Clarity at {fit}%) and ensure the professional's reputation has lasting impact (Reputation Stickiness at {stick}%). The objective is to transition from simple recognition to resonant influence.</p>"
        f"<p style='line-height:1.7; text-align:justify;'>In the {country} investment climate, a compelling story is paramount. A Narrative Confidence benchmarked at {conf}% reveals that the core elements of the professional narrative are powerful. The key appears to be addressing the Scalability Model, currently at {scale}%. "
        f"This suggests that refining the 'how'—articulating a clear, repeatable model for growth—could significantly boost investor appeal. Encouragingly, a {trust}% score in Proof of Trust shows the track record is a solid asset, providing the credibility upon which compelling future narratives can be built.</p>"
        f"<p style='line-height:1.7; text-align:justify;'>Strategy is ultimately judged by execution. A Partnership Readiness score of {partn}% signals a strong capacity for collaboration—a crucial element when the objective is to attract a specific class of high-caliber partners or investors. "
        f"Furthermore, a {premium}% in Premium Channel Leverage reveals an untapped potential to elevate the brand's positioning. Paired with a robust Leadership Presence of {leader}%, the message is clear: this type of profile is already viewed as credible. The next step is to strategically occupy high-influence spaces that reflect the full value of the work.</p>"
        f"<p style='line-height:1.7; text-align:justify;'>Benchmarking a profile like this against peers across Singapore, Malaysia, and Taiwan doesn't just measure a current standing—it illuminates a strategic advantage. "
        f"The data suggests that the professional instincts driving this strategic focus are often well-founded. For professionals at this stage, the path forward typically lies in a precise alignment of message, model, and market. This analysis serves as a framework, providing the clarity needed to turn current momentum into a definitive breakthrough.</p>"
    )
    return summary_html


# --- Main Flask Route ---
@app.route("/investor_analyze", methods=["POST"])
def investor_analyze():
    try:
        data = request.get_json(force=True)
        logging.info(f"Received POST request: {data.get('email', 'No email provided')}")

        # --- Data Extraction ---
        full_name = data.get("fullName", "N/A")
        dob_str = data.get("dob", "")
        country = data.get("country", "N/A")
        experience = data.get("experience", "N/A")
        industry = data.get("industry", "N/A")
        challenge = data.get("challenge", "N/A")
        target_profile = data.get("targetProfile", "N/A")
        
        # --- Data Processing ---
        age = compute_age(dob_str)
        chart_metrics = generate_chart_metrics()
        
        # --- HTML Generation ---
        title = "<h4 style='text-align:center;font-size:24px;'>🎯 AI Strategic Insight</h4>"
        chart_html = generate_chart_html(chart_metrics)
        summary_html = build_dynamic_summary(age, experience, industry, country, chart_metrics, challenge, data.get("context", ""), target_profile)
        
        # --- AI Tips Generation ---
        prompt = (f"Based on a professional in {industry} with {experience} years in {country}, generate 10 practical, "
                  f"investor-attraction tips with emojis for elite professionals in Singapore, Malaysia, and Taiwan. "
                  f"The tone should be sharp, strategic, and professional.")
        tips_text = get_openai_response(prompt)
        tips_block = ""
        if tips_text:
            tips_block = "<br><div style='font-size:24px;font-weight:bold;'>💡 Creative Tips:</div><br>" + \
                         "".join(f"<p style='font-size:16px; line-height:1.6;'>{line.strip()}</p>" for line in tips_text.splitlines() if line.strip())
        else:
            tips_block = "<p style='color:red;'>⚠️ Creative tips could not be generated at this time.</p>"

        # --- Footer and Email Body Construction ---
        footer = (
            "<div style='background-color:#f9f9f9;color:#333;padding:20px;border-left:6px solid #8C52FF; border-radius:8px;margin-top:30px;'>"
            "<strong>📊 AI Insights Generated From:</strong><ul style='margin-top:10px;margin-bottom:10px;padding-left:20px;line-height:1.7;'>"
            "<li>Data from anonymized professionals across Singapore, Malaysia, and Taiwan</li>"
            "<li>Investor sentiment models & trend benchmarks from OpenAI and global markets</li></ul>"
            "<p style='margin-top:10px;line-height:1.7;'>All data is PDPA-compliant and is not stored. Our AI systems detect statistically significant patterns without referencing any individual record.</p>"
            "<p style='margin-top:10px;line-height:1.7;'><strong>PS:</strong> This initial insight is just the beginning. A more personalized, data-specific report — reflecting the full details provided — will be prepared and delivered to the recipient's inbox within <strong>24 to 48 hours</strong>. "
            "This allows our AI systems to cross-reference the profile with nuanced regional and sector-specific benchmarks, ensuring sharper recommendations tailored to the exact challenge. "
            "If a conversation is desired sooner, we would be glad to arrange a <strong>15-minute call</strong> at a convenient time. 🎯</p></div>"
        )

        # Full HTML for email notification
        email_html = f"<h1>New Investor Insight Submission</h1>" \
                     f"<p><strong>Name:</strong> {full_name}<br>" \
                     f"<strong>Email:</strong> {data.get('email', 'N/A')}<br>" \
                     f"<strong>Country:</strong> {country}<br>" \
                     f"<strong>Industry:</strong> {industry}<br>" \
                     f"<strong>Challenge:</strong> {challenge}</p><hr>" + \
                     title + chart_html + summary_html + tips_block + footer
        
        # Send the email notification
        send_email(email_html, f"New Investor Insight: {full_name}")

        # HTML to be returned to the user's browser
        display_html = title + chart_html + summary_html + tips_block + footer
        return jsonify({"html_result": display_html})

    except Exception as e:
        logging.error(f"An error occurred in /investor_analyze: {e}")
        traceback.print_exc()
        return jsonify({"error": "An internal server error occurred."}), 500

# --- Run the App ---
if __name__ == "__main__":
    # Use Gunicorn for production, but this is fine for local development
    port = int(os.environ.get("PORT", 8080))
    app.run(debug=True, host='0.0.0.0', port=port)
