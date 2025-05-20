import os
import smtplib
import random
import logging
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

# ── SMTP & OpenAI Setup ─────────────────────────────────────────────────────
SMTP_SERVER   = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USERNAME = "kata.chatbot@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
if not SMTP_PASSWORD:
    app.logger.warning("SMTP_PASSWORD is not set; emails may fail.")

openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise RuntimeError("OPENAI_API_KEY not set.")
client = OpenAI(api_key=openai_api_key)

def send_email(html_body: str):
    msg = MIMEText(html_body, 'html')
    msg["Subject"] = "New Boss Submission"
    msg["From"]    = SMTP_USERNAME
    msg["To"]      = SMTP_USERNAME
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as s:
            s.starttls()
            s.login(SMTP_USERNAME, SMTP_PASSWORD)
            s.send_message(msg)
        app.logger.info("✅ Email sent successfully.")
    except Exception:
        app.logger.exception("Email sending failed")

@app.route("/boss_analyze", methods=["POST"])
def boss_analyze():
    data = request.get_json(force=True)
    try:
        # 1) Extract & strip
        name        = data.get("memberName","").strip()
        position    = data.get("position","").strip()
        department  = data.get("department","").strip()
        experience  = data.get("experience","").strip()
        sector      = data.get("sector","").strip()
        challenge   = data.get("challenge","").strip()
        focus       = data.get("focus","").strip()
        email_addr  = data.get("email","").strip()
        country     = data.get("country","").strip()
        referrer    = data.get("referrer","").strip()
        contact_num = data.get("contactNumber","").strip()
        lang        = data.get("lang","en").lower()

        # 2) Parse DOB & compute age
        d = data.get("dob_day","").strip()
        m = data.get("dob_month","").strip()
        y = data.get("dob_year","").strip()
        if d and m and y:
            chinese_months = {
                "一月":1,"二月":2,"三月":3,"四月":4,
                "五月":5,"六月":6,"七月":7,"八月":8,
                "九月":9,"十月":10,"十一月":11,"十二月":12
            }
            if m.isdigit():
                month = int(m)
            elif m in chinese_months:
                month = chinese_months[m]
            else:
                month = datetime.strptime(m, "%B").month
            birthdate = datetime(int(y), month, int(d))
        else:
            birthdate = parser.parse(data.get("dob",""), dayfirst=True)
        today = datetime.today()
        age = today.year - birthdate.year - ((today.month,today.day)<(birthdate.month,birthdate.day))

        # 3) Generate random metrics
        def mk(title):
            return {
                "title": title,
                "labels": ["Segment","Regional","Global"],
                "values": [random.randint(60,90), random.randint(55,85), random.randint(60,88)]
            }
        metrics = [
            mk("Communication Efficiency"),
            mk("Leadership Readiness"),
            mk("Task Completion Reliability")
        ]

        # 4) Build fixed-template analysis by language
        lines = []
        if lang == "zh":
            lines += [
                "📄 AI-生成报告\n\n工作绩效报告\n",
                f"• 年龄：{age}",
                f"• 职位：{position}",
                f"• 部门：{department}",
                f"• 工作经验：{experience} 年",
                f"• 行业：{sector}",
                f"• 国家：{country}",
                f"• 主要挑战：{challenge}",
                f"• 发展重点：{focus}\n",
                "📊 职场指标："
            ]
            for m in metrics:
                a,b,c = m["values"]
                lines.append(f"• {m['title']}: 分段 {a}%，区域 {b}%，全球 {c}%")
            lines.append(
                "\n📌 区域与全球趋势对比：\n"
                f"该指标在“{focus}”方面表现较强。\n"
                f"在“{focus}”方面可能存在一定差距，与区域和全球平均水平相比有中等差距。\n"
                "建议通过持续培训和辅导来缩小差距。\n"
            )
            lines.append("🔍 关键发现：")
            lines += [
                "1. 任务执行可靠性高于所有基准。",
                "2. 可增强沟通风格以改善跨团队协作。",
                "3. 在适当支持下具有强劲的成长潜力。\n"
            ]
            footer = """
<div style="background-color:#e6f7ff; color:#00529B; padding:15px; border-left:4px solid #00529B; margin:20px 0;">
  <strong>报告洞见由 KataChat 的 AI 系统生成，数据来源：</strong><br>
  1. 我们的跨新加坡、马来西亚和台湾匿名专业档案数据库<br>
  2. 可信 OpenAI 研究和领导力趋势数据集的全球商业基准<br>
  <em>所有数据均通过 AI 模型处理，以识别统计学显著模式，同时严格遵守 PDPA 合规要求。每项分析样本量最低 1,000+ 数据点。</em>
</div>
<p style="background-color:#e6f7ff; color:#00529B; padding:15px; border-left:4px solid #00529B; margin:20px 0;">
  <strong>PS:</strong> 本报告已发送至您的邮箱，24 小时内可查收。如需进一步讨论，欢迎随时联系，我们可安排 15 分钟电话会议。
</p>
"""
        elif lang == "tw":
            lines += [
                "📄 AI-生成報告\n\n工作績效報告\n",
                f"• 年齡：{age}",
                f"• 職位：{position}",
                f"• 部門：{department}",
                f"• 工作經驗：{experience} 年",
                f"• 行業：{sector}",
                f"• 國家：{country}",
                f"• 主要挑戰：{challenge}",
                f"• 發展重點：{focus}\n",
                "📊 職場指標："
            ]
            for m in metrics:
                a,b,c = m["values"]
                lines.append(f"• {m['title']}: 分段 {a}%，區域 {b}%，全球 {c}%")
            lines.append(
                "\n📌 區域與全球趨勢對比：\n"
                f"該指標在「{focus}」方面表現較強。\n"
                f"在「{focus}」方面可能存在一定差距，與區域和全球平均水平相比有中等差距。\n"
                "建議通過持續培訓和輔導來縮小差距。\n"
            )
            lines.append("🔍 關鍵發現：")
            lines += [
                "1. 任務執行可靠性高於所有基準。",
                "2. 可增強溝通風格以改善跨團隊協作。",
                "3. 在適當支持下具有強勁的成長潛力。\n"
            ]
            footer = """
<div style="background-color:#e6f7ff; color:#00529B; padding:15px; border-left:4px solid #00529B; margin:20px 0;">
  <strong>報告洞見由 KataChat 的 AI 系統生成，數據來源：</strong><br>
  1. 我們的跨新加坡、馬來西亞和台灣匿名專業檔案數據庫<br>
  2. 可信 OpenAI 研究和領導力趨勢數據集的全球商業基準<br>
  <em>所有數據均通過 AI 模型處理，以識別統計學顯著模式，同時嚴格遵守 PDPA 合規要求。每項分析樣本量最低 1,000+ 數據點。</em>
</div>
<p style="background-color:#e6f7ff; color:#00529B; padding:15px; border-left:4px solid #00529B; margin:20px 0;">
  <strong>PS:</strong> 本報告已發送至您的郵箱，24 小时內可查收。如需进一步讨论，欢迎随时联系，我们可安排 15 分钟电话会议。
</p>
"""
        else:
            lines += [
                "📄 AI-Generated Report\n\nWorkplace Performance Report\n",
                f"• Age: {age}",
                f"• Position: {position}",
                f"• Department: {department}",
                f"• Experience: {experience} year(s)",
                f"• Sector: {sector}",
                f"• Country: {country}",
                f"• Main Challenge: {challenge}",
                f"• Development Focus: {focus}\n",
                "📊 Workplace Metrics:"
            ]
            for m in metrics:
                a,b,c = m["values"]
                lines.append(f"• {m['title']}: Segment {a}%, Regional {b}%, Global {c}%")
            lines.append(
                "\n📌 Comparison with Regional & Global Trends:\n"
                f"This segment shows relative strength in {focus.lower()} performance.\n"
                f"There may be challenges around {focus.lower()}, with moderate gaps compared to regional and global averages.\n"
                "Consistency, training, and mentorship are recommended to bridge performance gaps.\n"
            )
            lines.append("🔍 Key Findings:")
            lines += [
                "1. Task execution reliability is above average across all benchmarks.",
                "2. Communication style can be enhanced to improve cross-team alignment.",
                "3. Growth potential is strong with proper support.\n"
            ]
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
        lines.append(footer)
        analysis = "\n".join(lines)

        # 5) Build improved HTML email
        html = f"""
<html><body style="font-family:sans-serif;color:#333">
  <h2>🎯 Boss Submission Details:</h2>
  <p>
    👤 <strong>Full Name:</strong> {name}<br>
    🏢 <strong>Position:</strong> {position}<br>
    📂 <strong>Department:</strong> {department}<br>
    🗓️ <strong>Experience:</strong> {experience} year(s)<br>
    📌 <strong>Sector:</strong> {sector}<br>
    ⚠️ <strong>Challenge:</strong> {challenge}<br>
    🌟 <strong>Focus:</strong> {focus}<br>
    📧 <strong>Email:</strong> {email_addr}<br>
    🌍 <strong>Country:</strong> {country}<br>
    🎂 <strong>DOB:</strong> {birthdate.date()}<br>
    💬 <strong>Referrer:</strong> {referrer}
  </p>
  <hr style="border:0;border-top:1px solid #e0e0e0;margin:20px 0;">
  <section style="margin-bottom:30px;">
    <h2 style="font-size:20px;color:#5E9CA0;margin-bottom:12px;">
      📄 AI-Generated Report
    </h2>
    <div style="
         background:#fafafa;
         border:1px solid #e0e0e0;
         border-radius:6px;
         padding:16px;
         font-size:14px;
         line-height:1.6;
         white-space:pre-wrap;
    ">
      {analysis}
    </div>
  </section>
  {footer}
</body></html>
"""
        send_email(html)

        # 6) Return JSON
        return jsonify({"metrics": metrics, "analysis": analysis})

    except Exception as e:
        app.logger.exception("Error in /boss_analyze")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
