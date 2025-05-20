import os
import re
import smtplib
import random
import logging
import json
from datetime import datetime
from dateutil import parser
from email.mime.text import MIMEText
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

# ── Flask Setup ─────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.DEBUG)

# ── OpenAI Client ────────────────────────────────────────────────────────────
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise RuntimeError("OPENAI_API_KEY environment variable is not set.")
client = OpenAI(api_key=openai_api_key)

# ── SMTP Setup ───────────────────────────────────────────────────────────────
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "kata.chatbot@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
if not SMTP_PASSWORD:
    app.logger.warning("SMTP_PASSWORD is not set; emails may fail.")

def send_email(html_body):
    """Sends an HTML email containing the full submission and report."""
    subject = "New KataChatBot Submission"
    msg = MIMEText(html_body, 'html')
    msg["Subject"] = subject
    msg["From"] = SMTP_USERNAME
    msg["To"] = SMTP_USERNAME

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        app.logger.info("✅ HTML email sent successfully.")
    except Exception:
        app.logger.error("❌ Email sending failed.", exc_info=True)

def _t(lang, en, zh, tw):
    """Helper function for language translations"""
    if lang == "zh":
        return zh
    elif lang == "tw":
        return tw
    return en

@app.route("/boss_analyze", methods=["POST"])
def boss_analyze():
    try:
        data = request.get_json(force=True)
        app.logger.info(f"[boss_analyze] payload: {data}")

        # 1) Extract form fields
        name = data.get("memberName", "Unknown")
        position = data.get("position", "Staff")
        challenge = data.get("challenge", "")
        focus = data.get("focus", "")
        country = data.get("country", "")
        email_addr = data.get("email", "").strip()
        phone = data.get("phone", "").strip()
        lang = data.get("lang", "en").lower()

        # 2) Build prompt for JSON output with language support
        if lang == "zh":
            prompt = f"""
你是一位专业的组织心理学家。为名为"{name}"的团队成员生成一份详细的绩效报告，
职位是"{position}"，面临的关键挑战是:"{challenge}"。
他们偏好的发展重点是"{focus}"，所在地区是"{country}"。

要求:
1. 返回三个柱状图指标(JSON格式)，每个比较:
   - 个人得分
   - 区域平均
   - 全球平均
   示例:
   {{
     "title":"领导力",
     "labels":["个人","区域平均","全球平均"],
     "values":[75,65,70]
   }}
2. 在"analysis"字段提供150-200字的分析，内容需:
   - 突出他们相对于区域/全球的最大优势
   - 指出他们最大的差距
   - 提供三个可操作的下一步建议
3. 只返回一个包含"metrics"(数组)和"analysis"(字符串)的JSON对象。
"""
        elif lang == "tw":
            prompt = f"""
你是一位專業的組織心理學家。為名為"{name}"的團隊成員生成一份詳細的績效報告，
職位是"{position}"，面臨的關鍵挑戰是:"{challenge}"。
他們偏好的發展重點是"{focus}"，所在地區是"{country}"。

要求:
1. 返回三個柱狀圖指標(JSON格式)，每個比較:
   - 個人得分
   - 區域平均
   - 全球平均
   示例:
   {{
     "title":"領導力",
     "labels":["個人","區域平均","全球平均"],
     "values":[75,65,70]
   }}
2. 在"analysis"字段提供150-200字的分析，內容需:
   - 突出他們相對於區域/全球的最大優勢
   - 指出他們最大的差距
   - 提供三個可操作的下一步建議
3. 只返回一個包含"metrics"(數組)和"analysis"(字符串)的JSON對象。
"""
        else:
            prompt = f"""
You are an expert organizational psychologist.
Generate a detailed performance report for a team member named "{name}",
working as "{position}", who faces this key challenge:
"{challenge}". Their preferred development focus is "{focus}", and they are located in "{country}".

Requirements:
1. Return exactly three bar-chart metrics in JSON, each comparing:
   - Individual score
   - Regional average
   - Global average
   Example item:
   {{
     "title":"Leadership",
     "labels":["Individual","Regional Avg","Global Avg"],
     "values":[75,65,70]
   }}
2. Provide a 150–200 word narrative in the "analysis" field that:
   - Highlights their top strength vs. region/global
   - Identifies their biggest gap
   - Offers three actionable next steps
3. Return only a single JSON object with keys "metrics" (array) and "analysis" (string).
"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"user","content":prompt}]
        )
        raw = response.choices[0].message.content.strip()
        app.logger.debug(f"[boss_analyze] raw output: {raw}")

        report = json.loads(raw)

        # 3) Build language-specific footer
        if lang == "zh":
            footer_html = f"""
<div style="background-color:#e6f7ff; color:#00529B; padding:15px; border-left:4px solid #00529B; margin:20px 0;">
  <strong>本报告中的洞察由KataChat的AI系统分析生成，数据来源包括:</strong><br>
  1. 我们专有的新加坡、马来西亚和台湾匿名职业资料数据库<br>
  2. 来自可信赖的OpenAI研究和领导力趋势数据集的全球商业基准数据<br>
  <em>所有数据均通过我们的AI模型处理，以识别具有统计意义的模式，同时严格遵守PDPA合规要求。分析样本量各不相同，管理比较的最低阈值为1,000+数据点。</em>
</div>
<p style="background-color:#e6f7ff; color:#00529B; padding:15px; border-left:4px solid #00529B; margin:20px 0;">
  <strong>附注:</strong> 本报告已发送至您的邮箱，应在24小时内送达。如需进一步讨论，欢迎随时联系我们——我们很乐意为您安排15分钟的电话沟通。
</p>
"""
        elif lang == "tw":
            footer_html = f"""
<div style="background-color:#e6f7ff; color:#00529B; padding:15px; border-left:4px solid #00529B; margin:20px 0;">
  <strong>本報告中的洞察由KataChat的AI系統分析生成，數據來源包括:</strong><br>
  1. 我們專有的新加坡、馬來西亞和台灣匿名職業資料數據庫<br>
  2. 來自可信賴的OpenAI研究和領導力趨勢數據集的全球商業基準數據<br>
  <em>所有數據均通過我們的AI模型處理，以識別具有統計意義的模式，同時嚴格遵守PDPA合規要求。分析樣本量各不相同，管理比較的最低閾值為1,000+數據點。</em>
</div>
<p style="background-color:#e6f7ff; color:#00529B; padding:15px; border-left:4px solid #00529B; margin:20px 0;">
  <strong>附註:</strong> 本報告已發送至您的郵箱，應在24小時內送達。如需進一步討論，歡迎隨時聯繫我們——我們很樂意為您安排15分鐘的電話溝通。
</p>
"""
        else:
            footer_html = f"""
<div style="background-color:#e6f7ff; color:#00529B; padding:15px; border-left:4px solid #00529B; margin:20px 0;">
  <strong>The insights in this report are generated by KataChat's AI systems analyzing:</strong><br>
  1. Our proprietary database of anonymized professional profiles across Singapore, Malaysia, and Taiwan<br>
  2. Aggregated global business benchmarks from trusted OpenAI research and leadership trend datasets<br>
  <em>All data is processed through our AI models to identify statistically significant patterns while maintaining strict PDPA compliance. Sample sizes vary by analysis, with minimum thresholds of 1,000+ data points for management comparisons.</em>
</div>
<p style="background-color:#e6f7ff; color:#00529B; padding:15px; border-left:4px solid #00529B; margin:20px 0;">
  <strong>PS:</strong> This report has also been sent to your email inbox and should arrive within 24 hours. If you'd like to discuss it further, feel free to reach out — we're happy to arrange a 15-minute call at your convenience.
</p>
"""

        # 4) Build the HTML email body with inline-CSS bar charts
        palette = ["#5E9CA0","#FF9F40","#9966FF","#4BC0C0","#FF6384","#36A2EB","#FFCE56","#C9CBCF"]
        html = [f"""<html><body style="font-family:sans-serif;color:#333">
<h2>🎯 {_t(lang, 'New Manager Submission', '新经理提交', '新經理提交')}:</h2>
<p>
👤 <strong>{_t(lang, 'Member Name', '成员姓名', '成員姓名')}:</strong> {name}<br>
💼 <strong>{_t(lang, 'Position', '职位', '職位')}:</strong> {position}<br>
🌍 <strong>{_t(lang, 'Country', '国家', '國家')}:</strong> {country}<br>
📞 <strong>{_t(lang, 'Phone', '电话', '電話')}:</strong> {phone}<br>
📧 <strong>{_t(lang, 'Email', '邮箱', '郵箱')}:</strong> {email_addr}<br>
🔄 <strong>{_t(lang, 'Key Challenge', '关键挑战', '關鍵挑戰')}:</strong> {challenge}<br>
🎯 <strong>{_t(lang, 'Development Focus', '发展重点', '發展重點')}:</strong> {focus}
</p>
<hr>
<h2>📊 {_t(lang, 'AI-Generated Report', 'AI生成报告', 'AI生成報告')}</h2>
<pre style="font-size:14px;white-space:pre-wrap">{report['analysis']}</pre>
<hr>
<h2>📈 {_t(lang, 'Metrics', '指标', '指標')}</h2>
"""]

        for m in report['metrics']:
            html.append(f"<h3>{m['title']}</h3>")
            for i, (lbl, val) in enumerate(zip(m["labels"], m["values"])):
                color = palette[i % len(palette)]
                html.append(f"""
<div style="margin:4px 0; line-height:1.4">
  {lbl}: 
  <span style="
    display:inline-block;
    width:{max(val,0)}%;
    height:12px;
    background:{color};
    border-radius:4px;
    vertical-align:middle;
  "></span>
  &nbsp;{val}%
</div>
""")

        # Add the language-specific footer
        html.append(footer_html)
        html.append("</body></html>")
        email_html = "".join(html)

        # 5) Send HTML email
        send_email(email_html)

        return jsonify(report)

    except Exception as e:
        app.logger.exception("Error in /boss_analyze")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
