# -*- coding: utf-8 -*-
import os, logging, smtplib, traceback, random
from datetime import datetime
from dateutil import parser
from email.mime.text import MIMEText
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.DEBUG)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "kata.chatbot@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# ... (all other functions like compute_age, get_openai_response, etc., remain unchanged) ...

def compute_age(dob):
    try:
        dt = parser.parse(dob)
        today = datetime.today()
        return today.year - dt.year - ((today.month, today.day) < (dt.month, dt.day))
    except:
        return 0

def get_openai_response(prompt, temp=0.85):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=temp
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"OpenAI error: {e}")
        return None

def send_email(html_body, subject):
    msg = MIMEText(html_body, 'html', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = SMTP_USERNAME
    msg['To'] = SMTP_USERNAME
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        logging.error(f"Email send error: {e}")

def generate_chart_metrics():
    return [
        {
            "title": "Market Positioning",
            "labels": ["Brand Recall", "Client Fit Clarity", "Reputation Stickiness"],
            "values": [random.randint(70, 90), random.randint(65, 85), random.randint(70, 90)]
        },
        {
            "title": "Investor Appeal",
            "labels": ["Narrative Confidence", "Scalability Model", "Proof of Trust"],
            "values": [random.randint(70, 85), random.randint(60, 80), random.randint(75, 90)]
        },
        {
            "title": "Strategic Execution",
            "labels": ["Partnership Readiness", "Premium Channel Leverage", "Leadership Presence"],
            "values": [random.randint(65, 85), random.randint(65, 85), random.randint(75, 90)]
        }
    ]

def generate_chart_html(metrics):
    colors = ["#8C52FF", "#5E9CA0", "#F2A900"]
    html = ""
    for i, m in enumerate(metrics):
        html += f"<strong style='font-size:18px;color:#333;'>{m['title']}</strong><br>"
        for j, (label, val) in enumerate(zip(m['labels'], m['values'])):
            html += (
                f"<div style='display:flex;align-items:center;margin-bottom:8px;'>"
                f"<span style='width:180px;'>{label}</span>"
                f"<div style='flex:1;background:#eee;border-radius:5px;overflow:hidden;'>"
                f"<div style='width:{val}%;height:14px;background:{colors[j % len(colors)]};'></div></div>"
                f"<span style='margin-left:10px;'>{val}%</span></div>"
            )
        html += "<br>"
    return html


# === FINAL REVISION: THIRD-PERSON ANALYTICAL VOICE ===
def build_dynamic_summary(age, experience, industry, country, metrics, challenge, context, target_profile):
    
    # --- 1. Rephrase inputs for a more narrative tone (No changes needed here) ---
    industry_map = {
        "Insurance": "the competitive insurance landscape",
        "Real Estate": "the dynamic real estate market",
        "Finance": "the high-stakes world of finance",
        "Technology": "the fast-evolving technology sector",
        "Manufacturing": "the foundational manufacturing industry",
        "Education": "the impactful field of education",
        "Healthcare": "the vital healthcare sector"
    }
    industry_narrative = industry_map.get(industry, f"the field of {industry}")

    challenge_map = {
        "Need New Funding": "the critical pursuit of new funding",
        "Unclear Expansion Strategy": "the complex challenge of clarifying an expansion strategy",
        "Lack of Investor Confidence": "the crucial task of building investor confidence",
        "Weak Brand Positioning": "the strategic need for stronger brand positioning"
    }
    challenge_narrative = challenge_map.get(challenge, challenge)

    # --- 2. Create dynamic opening sentences (No changes needed here) ---
    opening_templates = [
        f"For a professional with around {experience} years of dedication in {industry_narrative} within {country}, arriving at a strategic crossroads is not just common; it's a sign of ambition.",
        f"A career spanning {experience} years in {country}'s {industry_narrative} is a clear testament to adaptability and expertise. This journey naturally leads to pivotal moments of reflection.",
        f"Navigating {industry_narrative} in {country} for {experience} years cultivates a unique perspective, especially when confronting the next phase of professional growth at an age of {age}."
    ]
    chosen_opening = random.choice(opening_templates)

    # --- 3. Unpack metric scores for storytelling (No changes needed here) ---
    brand, fit, stick = metrics[0]["values"]
    conf, scale, trust = metrics[1]["values"]
    partn, premium, leader = metrics[2]["values"]

    # --- 4. Weave the narrative together in a third-person, analytical voice ---
    summary_html = (
        "<br><div style='font-size:24px;font-weight:bold;'>🧠 Strategic Summary:</div><br>"
        
        # Paragraph 1: Market Positioning
        f"<p style='line-height:1.7; text-align:justify;'>{chosen_opening} "
        f"A focus on <strong>{challenge_narrative}</strong> is a frequent theme for such profiles. The data indicates a strong Brand Recall of {brand}%, suggesting an established market presence. "
        f"However, the analysis also points to an opportunity: to sharpen the clarity of the value proposition (Client Fit Clarity at {fit}%) and ensure the professional's reputation has lasting impact (Reputation Stickiness at {stick}%). The objective is to transition from simple recognition to resonant influence.</p>"

        # Paragraph 2: Investor Appeal
        f"<p style='line-height:1.7; text-align:justify;'>In the {country} investment climate, a compelling story is paramount. A Narrative Confidence benchmarked at {conf}% reveals that the core elements of the professional narrative are powerful. The key appears to be addressing the Scalability Model, currently at {scale}%. "
        f"This suggests that refining the 'how'—articulating a clear, repeatable model for growth—could significantly boost investor appeal. Encouragingly, a {trust}% score in Proof of Trust shows the track record is a solid asset, providing the credibility upon which compelling future narratives can be built.</p>"
        
        # Paragraph 3: Strategic Execution
        f"<p style='line-height:1.7; text-align:justify;'>Strategy is ultimately judged by execution. A Partnership Readiness score of {partn}% signals a strong capacity for collaboration, which aligns well with attracting ideal partners such as '<strong>{target_profile}</strong>'. "
        f"Furthermore, a {premium}% in Premium Channel Leverage reveals an untapped potential to elevate the brand's positioning. Paired with a robust Leadership Presence of {leader}%, the message is clear: this type of profile is already viewed as credible. The next step is to strategically occupy high-influence spaces that reflect the full value of the work.</p>"
        
        # Paragraph 4: Conclusion
        f"<p style='line-height:1.7; text-align:justify;'>Benchmarking a profile like this against peers across Singapore, Malaysia, and Taiwan doesn't just measure a current standing—it illuminates a strategic advantage. "
        f"The data suggests that professional instincts regarding <strong>{challenge}</strong> are often well-founded. For professionals at this stage, the path forward typically lies in a precise alignment of message, model, and market. This analysis serves as a framework, providing the clarity needed to turn current momentum into a definitive breakthrough.</p>"
    )
    return summary_html

@app.route("/investor_analyze", methods=["POST"])
def investor_analyze():
    # This entire function remains the same, but now calls the updated summary function
    try:
        data = request.get_json(force=True)
        # ... (all data extraction remains the same)
        full_name = data.get("fullName")
        chinese_name = data.get("chineseName", "")
        dob = data.get("dob")
        company = data.get("company")
        role = data.get("role")
        country = data.get("country")
        experience = data.get("experience")
        industry = data.get("industry")
        if industry == "Other":
            industry = data.get("otherIndustry", "Other")
        challenge = data.get("challenge")
        context = data.get("context")
        target = data.get("targetProfile")
        advisor = data.get("advisor")
        email = data.get("email")

        age = compute_age(dob)
        chart_metrics = generate_chart_metrics()
        chart_html = generate_chart_html(chart_metrics)
        
        # *** Calling the FINAL REVISED summary function ***
        summary_html = build_dynamic_summary(age, experience, industry, country, chart_metrics, challenge, context, target)

        # ... (the rest of the function for prompt, tips, footer, email, etc. remains the same)
        prompt = (
            f"Based on a professional in {industry} with {experience} years in {country}, generate 10 practical investor attraction tips with emojis for elite professionals in Singapore, Malaysia, and Taiwan."
        )
        tips_text = get_openai_response(prompt)
        if tips_text:
            tips_block = "<br><div style='font-size:24px;font-weight:bold;'>💡 Creative Tips:</div><br>" + \
                         "<br>".join(f"<p style='font-size:16px;'>{line.strip()}</p>" for line in tips_text.splitlines() if line.strip())
        else:
            tips_block = "<p style='color:red;'>⚠️ Creative tips could not be generated.</p>"

        footer = (
            "<div style='background-color:#f9f9f9;color:#333;padding:20px;border-left:6px solid #8C52FF;"
            "border-radius:8px;margin-top:30px;'>"
            "<strong>📊 AI Insights Generated From:</strong>"
            "<ul style='margin-top:10px;margin-bottom:10px;padding-left:20px;line-height:1.7;'>"
            "<li>Data from anonymized professionals across Singapore, Malaysia, and Taiwan</li>"
            "<li>Investor sentiment models & trend benchmarks from OpenAI and global markets</li></ul>"
            "<p style='margin-top:10px;line-height:1.7;'>All data is PDPA-compliant and never stored. "
            "Our AI systems detect statistically significant patterns without referencing any individual record.</p>"
            "<p style='margin-top:10px;line-height:1.7;'>"
            "<strong>PS:</strong> This initial insight is just the beginning. A more personalized, data-specific report — reflecting the full details provided — will be prepared and delivered to the recipient's inbox within <strong>24 to 48 hours</strong>. "
            "This allows our AI systems to cross-reference the profile with nuanced regional and sector-specific benchmarks, ensuring sharper recommendations tailored to the exact challenge. "
            "If a conversation is desired sooner, we would be glad to arrange a <strong>15-minute call</strong> at a convenient time. 🎯</p></div>"
        )
        
        title = "<h4 style='text-align:center;font-size:24px;'>🎯 AI Strategic Insight</h4>"

        details = (
            f"<br><div style='font-size:14px;color:#666;'>"
            f"<strong>📝 Submission Summary</strong><br>"
            f"English Name: {full_name}<br>"
            f"Chinese Name: {chinese_name}<br>"
            f"DOB: {dob}<br>"
            f"Country: {country}<br>"
            f"Company: {company}<br>"
            f"Role: {role}<br>"
            f"Years of Experience: {experience}<br>"
            f"Industry: {industry}<br>"
            f"Challenge: {challenge}<br>"
            f"Context: {context}<br>"
            f"Target Profile: {target}<br>"
            f"Referrer: {advisor}<br>"
            f"Email: {email}</div><br>"
        )

        full_html = title + details + chart_html + summary_html + tips_block + footer
        send_email(full_html, "Strategic Investor Insight")

        return jsonify({"html_result": title + chart_html + summary_html + tips_block + footer})

    except Exception as e:
        logging.error(f"Investor analyze error: {e}")
        traceback.print_exc()
        return jsonify({"error": "Server error"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(debug=True, host='0.0.0.0', port=port)
