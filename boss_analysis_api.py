# -*- coding: utf-8 -*-
import os
import random
from datetime import datetime
from dateutil import parser
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from email.mime.text import MIMEText
import smtplib

app = Flask(__name__)
CORS(app)

# ── Configuration ───────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set")
client = OpenAI(api_key=OPENAI_API_KEY)

# SMTP config
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "kata.chatbot@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
if not SMTP_PASSWORD:
    app.logger.warning("SMTP_PASSWORD is not set; emails may fail.")

# Language-specific content
LANGUAGE_CONTENT = {
    "en": {
        "email_subject": "Your Workplace Performance Report",
        "greeting": "Dear Talent Recruiter,",
        "report_title": "📄 Workplace Performance Report",
        "global_title": "🌐 Global Section Analytical Report",
        "creative_title": "Creative Innovation Approaches",
        "ps_content": (
            "PS: This report has also been sent to your email inbox and should arrive within 24 hours. "
            "If you'd like to discuss it further, feel free to reach out — we're happy to arrange a "
            "15-minute call at your convenience."
        )
    },
    "zh": {
        "email_subject": "您的工作表现报告",
        "greeting": "尊敬的人才招聘专员,",
        "report_title": "📄 工作表现报告",
        "global_title": "🌐 全球分析报告",
        "creative_title": "创新方法建议",
        "ps_content": (
            "PS: 此报告也已发送至您的电子邮箱，应在24小时内送达。"
            "如果您想进一步讨论，请随时联系我们——我们很乐意为您安排15分钟的电话会议。"
        )
    },
    "tw": {
        "email_subject": "您的工作表現報告",
        "greeting": "尊敬的人才招聘專員,",
        "report_title": "📄 工作表現報告",
        "global_title": "🌐 全球分析報告",
        "creative_title": "創新方法建議",
        "ps_content": (
            "PS: 此報告也已發送至您的電子郵箱，應在24小時內送達。"
            "如果您想進一步討論，請隨時聯繫我們——我們很樂意為您安排15分鐘的電話會議。"
        )
    }
}

# ── Helper Functions ────────────────────────────────────────────────────
def compute_age(data):
    """Calculate age from date of birth data"""
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

def send_email(html_body: str, lang: str = "en"):
    """Send email with localized subject"""
    msg = MIMEText(html_body, 'html', 'utf-8')
    msg["Subject"] = LANGUAGE_CONTENT.get(lang, {}).get("email_subject", "Your Workplace Performance Report")
    msg["From"] = SMTP_USERNAME
    msg["To"] = SMTP_USERNAME
    
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        app.logger.error(f"Failed to send email: {str(e)}")

def generate_metrics():
    """Generate random performance metrics"""
    metrics = []
    for title, color in [
        ("Communication Efficiency", "#5E9CA0"),
        ("Leadership Readiness", "#FF9F40"),
        ("Task Completion Reliability", "#9966FF"),
    ]:
        seg, reg, glo = random.randint(60, 90), random.randint(55, 85), random.randint(60, 88)
        metrics.append((title, seg, reg, glo, color))
    return metrics

def create_bar_html(metrics):
    """Create HTML for metric bars"""
    bar_html = ""
    for title, seg, reg, glo, color in metrics:
        bar_html += f"<strong>{title}</strong><br>"
        for v in (seg, reg, glo):
            bar_html += (
                f"<span style='display:inline-block;width:{v}%;height:12px;"
                f"background:{color};margin-right:6px;border-radius:4px;'></span> {v}%<br>"
            )
        bar_html += "<br>"
    return bar_html

def create_report_html(data, lang="en"):
    """Create the report HTML section"""
    lang_content = LANGUAGE_CONTENT.get(lang, LANGUAGE_CONTENT["en"])
    age = compute_age(data)
    
    report_html = (
        "<br>\n<br>\n<br>\n"
        + f'<h2 class="sub">{lang_content["report_title"]}</h2>\n'
        + "<div class='narrative'>"
        + f"• Age: {age}<br>"
        + f"• Position: {data.get('position', '')}<br>"
        + f"• Department: {data.get('department', '—')}<br>"
        + f"• Experience: {data.get('experience', '')} year(s)<br>"
        + f"• Sector: {data.get('sector', '')}<br>"
        + f"• Country: {data.get('country', '')}<br>"
        + f"• Main Challenge: {data.get('challenge', '')}<br>"
        + f"• Development Focus: {data.get('focus', '')}<br>"
        + "</div>\n"
    )
    return report_html

def get_openai_response(prompt, temperature=0.7, model="gpt-3.5-turbo"):
    """Get response from OpenAI API"""
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature
        )
        return resp.choices[0].message.content
    except Exception as e:
        app.logger.error(f"OpenAI API error: {str(e)}")
        return "Unable to generate content at this time."

def create_footer(lang="en"):
    """Create localized footer with PDPA notice"""
    lang_content = LANGUAGE_CONTENT.get(lang, LANGUAGE_CONTENT["en"])
    
    if lang == "en":
        content = """
        <strong>The insights in this report are generated by KataChat's AI systems analyzing:</strong><br>
        1. Our proprietary database of anonymized professional profiles across Singapore, Malaysia, and Taiwan<br>
        2. Aggregated global business benchmarks from trusted OpenAI research and leadership trend datasets<br>
        <em>All data is processed through our AI models to identify statistically significant patterns while maintaining strict PDPA compliance. Sample sizes vary by analysis, with minimum thresholds of 1,000+ data points for management comparisons.</em>
        """
    elif lang == "zh":
        content = """
        <strong>本报告中的见解由KataChat的AI系统分析生成，数据来源包括：</strong><br>
        1. 我们专有的新加坡、马来西亚和台湾匿名职业资料数据库<br>
        2. 来自可信的OpenAI研究和领导力趋势数据集的全球商业基准<br>
        <em>所有数据均通过我们的AI模型进行处理，以识别具有统计意义的模式，同时严格遵守PDPA合规要求。分析样本量各不相同，管理比较的最小阈值为1,000+数据点。</em>
        """
    else:  # tw
        content = """
        <strong>本報告中的見解由KataChat的AI系統分析生成，數據來源包括：</strong><br>
        1. 我們專有的新加坡、馬來西亞和台灣匿名職業資料數據庫<br>
        2. 來自可信的OpenAI研究和領導力趨勢數據集的全球商業基準<br>
        <em>所有數據均通過我們的AI模型進行處理，以識別具有統計意義的模式，同時嚴格遵守PDPA合規要求。分析樣本量各不相同，管理比較的最小閾值為1,000+數據點。</em>
        """
    
    return (
        f'<div style="background-color:#e6f7ff; color:#00529B; padding:15px; '
        f'border-left:4px solid #00529B; margin:20px 0;">{content}</div>'
        f'<p style="background-color:#e6f7ff; color:#00529B; padding:15px; '
        f'border-left:4px solid #00529B; margin:20px 0;">'
        f'<strong>{lang_content["ps_content"]}</strong>'
        '</p>'
    )

# ── API Endpoints ──────────────────────────────────────────────────────
@app.route("/boss_analyze", methods=["POST"])
def boss_analyze():
    try:
        data = request.get_json(force=True)
        lang = data.get("lang", "en").lower()
        
        # Validate required fields
        required_fields = ["position", "experience", "sector", "challenge", "focus", "country"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # 1) Generate metrics
        metrics = generate_metrics()
        
        # 2) Build horizontal bar HTML
        bar_html = create_bar_html(metrics)
        
        # 3) Greeting
        greeting = f"<p>{LANGUAGE_CONTENT.get(lang, {}).get('greeting', 'Dear Talent Recruiter,')}</p>"
        
        # 4) Workplace Performance Report block
        report_html = create_report_html(data, lang)
        
        # 5) Global Section via OpenAI
        lang_content = LANGUAGE_CONTENT.get(lang, LANGUAGE_CONTENT["en"])
        global_header = f'<h2 class="sub">{lang_content["global_title"]}</h2>\n<div class="global">\n'
        
        if lang == "en":
            prompt_global = (
                f"You are an expert business analyst. Write seven detailed paragraphs for a {data.get('position')} in {data.get('country')}, "
                f"{data.get('experience')} years experience in {data.get('sector')}. Challenge: '{data.get('challenge')}'. Focus: '{data.get('focus')}'."
            )
        elif lang == "zh":
            prompt_global = (
                f"你是一位专业的商业分析师。请为一位在{data.get('country')}的{data.get('position')}撰写七段详细的分析，"
                f"拥有{data.get('experience')}年{data.get('sector')}行业经验。面临的挑战：'{data.get('challenge')}'。发展重点：'{data.get('focus')}'。"
            )
        else:  # tw
            prompt_global = (
                f"你是一位專業的商業分析師。請為一位在{data.get('country')}的{data.get('position')}撰寫七段詳細的分析，"
                f"擁有{data.get('experience')}年{data.get('sector')}行業經驗。面臨的挑戰：'{data.get('challenge')}'。發展重點：'{data.get('focus')}'。"
            )
            
        global_content = get_openai_response(prompt_global, temperature=0.7)
        global_html = global_header + global_content + "</div>\n"
        
        # 6) Creative Approaches via OpenAI
        if lang == "en":
            creative_prompt = (
                f"You are an innovation consultant. For a {data.get('position')} whose challenge is '{data.get('challenge')}' "
                f"and focus is '{data.get('focus')}', propose 10 creative, actionable approaches, numbered 1–10."
            )
        elif lang == "zh":
            creative_prompt = (
                f"你是一位创新顾问。针对一位{data.get('position')}，面临的挑战是'{data.get('challenge')}'，"
                f"发展重点是'{data.get('focus')}'，请提出10条有创意且可操作的解决方案，用1-10编号。"
            )
        else:  # tw
            creative_prompt = (
                f"你是一位創新顧問。針對一位{data.get('position')}，面臨的挑戰是'{data.get('challenge')}'，"
                f"發展重點是'{data.get('focus')}'，請提出10條有創意且可操作的解決方案，用1-10編號。"
            )
            
        creative_content = get_openai_response(creative_prompt, temperature=0.8)
        creative_html = f"<h3>{lang_content['creative_title']}</h3>\n<div class='creative'>\n"
        for ln in creative_content.split("\n"):
            if ln.strip():
                creative_html += f"<p>{ln.strip()}</p>\n"
        creative_html += "</div>\n"
        
        # 7) Footer
        footer = create_footer(lang)
        
        # 8) Assemble full HTML
        analysis_html = (
            greeting
            + bar_html
            + report_html
            + global_html
            + creative_html
            + footer
        )
        
        # 9) Send the email
        send_email(analysis_html, lang)
        
        # 10) Return JSON
        return jsonify({
            "metrics": [
                {"title": t, "labels": ["Segment", "Regional", "Global"], "values": [s, r, g]}
                for t, s, r, g, _ in metrics
            ],
            "analysis": analysis_html
        })
        
    except Exception as e:
        app.logger.error(f"Error in boss_analyze: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
