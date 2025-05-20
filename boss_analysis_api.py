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
    """Send the HTML email to yourself."""
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
        # 1) Extract & strip inputs
        name       = data.get("memberName","").strip()
        position   = data.get("position","").strip()
        department = data.get("department","").strip()
        experience = data.get("experience","").strip()
        sector     = data.get("sector","").strip()
        challenge  = data.get("challenge","").strip()
        focus      = data.get("focus","").strip()
        email_addr = data.get("email","").strip()
        country    = data.get("country","").strip()
        referrer   = data.get("referrer","").strip()
        lang       = data.get("lang","en").lower()

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

        # 4) Build plain_report for screen (including footer)
        icon = "📄"
        if lang == "zh":
            heading      = f"{icon} AI-生成报告"
            report_title = "工作绩效报告"
            trend_title  = "📌 区域与全球趋势对比："
            find_title   = "🔍 关键发现："
        elif lang == "tw":
            heading      = f"{icon} AI-生成報告"
            report_title = "工作績效報告"
            trend_title  = "📌 區域與全球趨勢對比："
            find_title   = "🔍 關鍵發現："
        else:
            heading      = f"{icon} AI-Generated Report"
            report_title = "Workplace Performance Report"
            trend_title  = "📌 Comparison with Regional & Global Trends:"
            find_title   = "🔍 Key Findings:"

        lines = [
            heading, "",
            report_title,
            f"• 年龄：{age}" if lang.startswith("zh") else f"• Age: {age}",
            f"• 职位：{position}" if lang.startswith("zh") else f"• Position: {position}",
            f"• 部门：{department}" if lang.startswith("zh") else f"• Department: {department}",
            f"• 工作经验：{experience} 年" if lang.startswith("zh") else f"• Experience: {experience} year(s)",
            f"• 行业：{sector}" if lang.startswith("zh") else f"• Sector: {sector}",
            f"• 国家：{country}" if lang.startswith("zh") else f"• Country: {country}",
            f"• 主要挑战：{challenge}" if lang.startswith("zh") else f"• Main Challenge: {challenge}",
            f"• 发展重点：{focus}" if lang.startswith("zh") else f"• Development Focus: {focus}",
            "", 
            "📊 职场指标：" if lang.startswith("zh") else "📊 Workplace Metrics:"
        ]
        for m in metrics:
            a,b,c = m["values"]
            lines.append(f"• {m['title']}: Segment {a}%, Regional {b}%, Global {c}%")

        lines += [
            "",
            trend_title,
            (f"该指标在「{focus}」方面表现较强。" if lang.startswith("zh")
                   else f"This segment shows relative strength in {focus.lower()} performance."),
            (f"在「{focus}」方面可能存在一定差距，与区域和全球平均水平相比有中等差距。" if lang.startswith("zh")
                   else f"There may be challenges around {focus.lower()}, with moderate gaps compared to regional and global averages."),
            ("建议通过持续培训和辅导来缩小差距。" if lang.startswith("zh")
                   else "Consistency, training, and mentorship are recommended to bridge performance gaps."),
            "",
            find_title,
            ( "1. 任务执行可靠性高于所有基准。" if lang.startswith("zh")
                   else "1. Task execution reliability is above average across all benchmarks."),
            ( "2. 可增强沟通风格以改善跨团队协作。" if lang.startswith("zh")
                   else "2. Communication style can be enhanced to improve cross-team alignment."),
            ( "3. 在适当支持下具有强劲的成长潜力。" if lang.startswith("zh")
                   else "3. Growth potential is strong with proper support.")
        ]

        # Footer for screen
        lines += [
            "",
            "The insights in this report are generated by KataChat’s AI systems analyzing:",
            "1. Our proprietary database of anonymized professional profiles across Singapore, Malaysia, and Taiwan",
            "2. Aggregated global business benchmarks from trusted OpenAI research and leadership trend datasets",
            "All data is processed through our AI models to identify statistically significant patterns while maintaining strict PDPA compliance. Sample sizes vary by analysis, with minimum thresholds of 1,000+ data points for management comparisons.",
            "",
            "PS: This report has also been sent to your email inbox and should arrive within 24 hours. If you'd like to discuss it further, feel free to reach out — we’re happy to arrange a 15-minute call at your convenience."
        ]

        plain_report = "\n".join(lines)

        # 5) Build email HTML (with footer + charts). Do the newline→<br> replace outside the f-string:
        safe_report = plain_report.replace("\n", "<br>")

        footer_html = """
<div style="background-color:#e6f7ff;color:#00529B;padding:15px;border-left:4px solid #00529B;margin:20px 0;">
  <strong>The insights in this report are generated by KataChat’s AI systems analyzing:</strong><br>
  1. Our proprietary database of anonymized professional profiles across Singapore, Malaysia, and Taiwan<br>
  2. Aggregated global business benchmarks from trusted OpenAI research and leadership trend datasets<br>
  <em>All data is processed through our AI models to identify statistically significant patterns while maintaining strict PDPA compliance. Sample sizes vary by analysis, with minimum thresholds of 1,000+ data points for management comparisons.</em>
</div>
<p style="background-color:#e6f7ff;color:#00529B;padding:15px;border-left:4px solid #00529B;margin:20px 0;">
  <strong>PS:</strong> This report has also been sent to your email inbox and should arrive within 24 hours. If you'd like to discuss it further, feel free to reach out — we’re happy to arrange a 15-minute call at your convenience.
</p>
"""

        charts_html = "<h2>📊 Charts</h2><div style='font-family:sans-serif;color:#333'>"
        for m in metrics:
            charts_html += f"<h3>{m['title']}</h3>"
            for lbl,val in zip(m["labels"], m["values"]):
                charts_html += f"""
<div style="display:flex; align-items:center; margin-bottom:6px;">
  <span style="width:100px;">{lbl}:</span>
  <div style="flex:1; background:#e0e0e0; border-radius:4px; overflow:hidden; margin-right:8px;">
    <div style="width:{val}%; background:#5E9CA0; height:12px;"></div>
  </div>
  <span>{val}%</span>
</div>
"""
        charts_html += "</div>"

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
  <section style="margin-bottom:20px;">
    <div style="display:flex;align-items:center;margin-bottom:12px;">
      <span style="font-size:28px;color:#5E9CA0;line-height:1;margin-right:8px;">📄</span>
      <h3 style="font-size:24px;color:#5E9CA0;font-weight:bold;margin:0;">{heading.split(' ',1)[1]}</h3>
    </div>
    <div style="
         background:#fafafa;
         border:1px solid #e0e0e0;
         border-radius:6px;
         padding:16px;
         font-size:14px;
         line-height:1.6;
         white-space:pre-wrap;
    ">
      {safe_report}
    </div>
  </section>
  {footer_html}
  {charts_html}
</body></html>
"""
        send_email(html)

        # 6) Return JSON (plain_report) for screen display
        return jsonify({"metrics": metrics, "analysis": plain_report})

    except Exception as e:
        app.logger.exception("Error in /boss_analyze")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
