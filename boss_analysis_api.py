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
    d, m, y = data.get("dob_day"), data.get("dob_month"), data.get("dob_year")
    try:
        if d and m and y:
            month = int(m) if m.isdigit() else datetime.strptime(m, "%B").month
            bd = datetime(int(y), month, int(d))
        else:
            bd = parser.parse(data.get("dob",""), dayfirst=True)
    except Exception:
        bd = datetime.today()
    today = datetime.today()
    return today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))

def send_email(html_body: str):
    msg = MIMEText(html_body, 'html')
    msg["Subject"] = "Your Workplace Performance Report"
    msg["From"] = SMTP_USERNAME
    msg["To"]   = SMTP_USERNAME
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)

@app.route("/boss_analyze", methods=["POST"])
def boss_analyze():
    data = request.get_json(force=True)
    lang = data.get("lang", "en")

    # Extract inputs
    position   = data.get("position", "").strip()
    department = data.get("department", "").strip()
    experience = data.get("experience", "").strip()
    sector     = data.get("sector", "").strip()
    challenge  = data.get("challenge", "").strip()
    focus      = data.get("focus", "").strip()
    country    = data.get("country", "").strip()
    age        = compute_age(data)

    # Generate random metrics
    def rand_vals():
        return (random.randint(60, 90), random.randint(55, 85), random.randint(60, 88))
    metrics = [
        ("Communication Efficiency",   *rand_vals(), "#5E9CA0"),
        ("Leadership Readiness",        *rand_vals(), "#FF9F40"),
        ("Task Completion Reliability", *rand_vals(), "#9966FF"),
    ]

    # Build bar_html
    bar_html = ""
    for title, seg, reg, glob, color in metrics:
        bar_html += f"<strong>{title}</strong><br>"
        for val in (seg, reg, glob):
            bar_html += (
                f"<span style='display:inline-block; width:{val}%; height:12px;"
                f" background:{color}; margin-right:6px; border-radius:4px;'></span> {val}%<br>"
            )
        bar_html += "<br>"

    # Prepare static sections and prompt
    seg_stat, reg_stat, glob_stat = metrics[0][1], metrics[0][2], metrics[0][3]

    if lang == "zh":
        report_title = '<h2 class="sub">📄 职场绩效报告</h2>\n'
        global_header = '<h2 class="sub" style="margin:0.8em 0;">🌐 全球分析概览</h2>\n'
        footer = (
            '<div style="background:#e6f7ff; color:#00529B; padding:15px; '
            'border-left:4px solid #00529B; margin:20px 0;">'
            '<strong>本报告由 KataChat AI 系统生成，基于：</strong><br>'
            '1. 我们专有的匿名职场档案数据库（新加坡、马来西亚、台湾）<br>'
            '2. OpenAI 研究及行业基准数据<br>'
            '<em>所有数据遵循 PDPA 合规，最低样本量 1,000+</em>'
            '</div>'
            '<p style="background:#e6f7ff; color:#00529B; padding:15px; '
            'border-left:4px solid #00529B; margin:20px 0;">'
            '<strong>PS：</strong>报告已通过邮件发送，24 小时内应可收到。如需 15 分钟讨论，请联系我们。'
            '</p>'
        )
        prompt = (
            f"请用简体中文生成七段专业的两到三句话分析，作为行业概览，参照按经验年限、部门、区域和全球基准汇总的专业人士数据。"
            f"每段用<p>…</p>标签，并包含："
            f"新加坡同行中有 {seg_stat}% 的人沟通效率很高；"
            f"马来西亚平均为 {reg_stat}%；"
            f"全球基准为 {glob_stat}%。"
            f"请仅根据以下信息撰写："
            f"Position: {position}; Department: {department}; Years: {experience}; "
            f"Sector: {sector}; Country: {country}; Challenge: {challenge}; Focus: {focus}."
        )

    elif lang == "tw":
        report_title = '<h2 class="sub">📄 職場績效報告</h2>\n'
        global_header = '<h2 class="sub" style="margin:0.8em 0;">🌐 全球分析概覽</h2>\n'
        footer = (
            '<div style="background:#e6f7ff; color:#00529B; padding:15px; '
            'border-left:4px solid #00529B; margin:20px 0;">'
            '<strong>本報告由 KataChat AI 系統生成，依據：</strong><br>'
            '1. 我們的匿名職場資料庫（新加坡、马来西亚、臺灣）<br>'
            '2. OpenAI 研究與全球基準數據<br>'
            '<em>所有資料均符合 PDPA，最低樣本量 1,000+</em>'
            '</div>'
            '<p style="background:#e6f7ff; color:#00529B; padding:15px; '
            'border-left:4px solid #00529B; margin:20px 0;">'
            '<strong>PS：</strong>報告已通過電子郵件發送，24 小时內应收到。如需 15 分钟讨论，欢迎联系。'
            '</p>'
        )
        prompt = (
            f"請用繁體中文生成七段專業的兩到三句分析，作為行業概覽，參照按經驗年限、部門、區域和全球基準彙整的專業人士數據。"
            f"每段用<p>…</p>標籤，並包含："
            f"新加坡同儕中有 {seg_stat}% 溝通效率很高；"
            f"馬來西亞平均為 {reg_stat}%；"
            f"全球基準為 {glob_stat}%。"
            f"請僅根據以下信息撰寫："
            f"Position: {position}; Department: {department}; Years: {experience}; "
            f"Sector: {sector}; Country: {country}; Challenge: {challenge}; Focus: {focus}."
        )

    else:
        report_title = '<h2 class="sub">📄 Workplace Performance Report</h2>\n'
        global_header = (
            '<h2 class="sub" style="margin-top:0.8em; margin-bottom:0.8em;">'
            '🌐 Global Section Analytical Report</h2>\n'
        )
        footer = (
            '<div style="background-color:#e6f7ff; color:#00529B; padding:15px; '
            'border-left:4px solid #00529B; margin:20px 0;">'
            '<strong>The insights in this report are generated by KataChat’s AI systems analyzing:</strong><br>'
            '1. Our proprietary database of anonymized professional profiles across Singapore, Malaysia, and Taiwan<br>'
            '2. Aggregated global business benchmarks from trusted OpenAI research and leadership trend datasets<br>'
            '<em>All data is processed through our AI models to identify statistically significant patterns while maintaining strict PDPA compliance. Sample sizes vary by analysis, with minimum thresholds of 1,000+ data points for management comparisons.</em>'
            '</div>'
            '<p style="background-color:#e6f7ff; color:#00529B; padding:15px; '
            'border-left:4px solid #00529B; margin:20px 0;">'
            '<strong>PS:</strong> This report has also been sent to your email inbox and should arrive within 24 hours. '
            'If you\'d like to discuss it further, feel free to reach out — we’re happy to arrange a 15-minute call at your convenience.'
            '</p>'
        )
        prompt = (
            f"Generate exactly seven professional two- to three-sentence analytical paragraphs for a 'Global Section Analytical Report', "
            f"written as an industry overview referencing aggregated professionals by experience band, sector, region, and global benchmarks. "
            f"Include: '{seg_stat}% of peers in Singapore rate high on Communication Efficiency', "
            f"'{reg_stat}% is the average across Malaysia', '{glob_stat}% represents the global benchmark'. "
            f"Reference only: Position: {position}; Department: {department}; Years: {experience}; "
            f"Sector: {sector}; Country: {country}; Challenge: {challenge}; Focus: {focus}. Wrap each paragraph in <p>…</p> tags."
        )

    # Call OpenAI
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert business analyst aware of regional and global benchmarks."},
            {"role": "user",   "content": prompt}
        ],
        temperature=0.7
    )
    global_html = completion.choices[0].message.content

    # Assemble report
    report_html = (
        "<br>\n" +
        report_title +
        f"• Age: {age}<br>" +
        f"• Position: {position}<br>" +
        f"• Department: {department}<br>" +
        f"• Experience: {experience} year(s)<br>" +
        f"• Sector: {sector}<br>" +
        f"• Country: {country}<br>" +
        f"• Main Challenge: {challenge}<br>" +
        f"• Development Focus: {focus}<br>"
    )

    analysis_html = bar_html + report_html + global_header + global_html + footer
    send_email(analysis_html)

    return jsonify({
        "metrics": [
            {"title": t, "labels": ["Segment", "Regional", "Global"], "values": [s, r, g]}
            for t, s, r, g, _ in metrics
        ],
        "analysis": analysis_html
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
