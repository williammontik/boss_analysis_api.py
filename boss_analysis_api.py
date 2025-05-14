from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # allows cross‐origin requests from your WordPress site

@app.route('/analyze_name', methods=['POST'])
def analyze_name():
    data = request.get_json()
    # … your existing name‐analysis logic here …
    return jsonify({
        # … your existing name analysis response …
    })

@app.route('/boss_analyze', methods=['POST'])
def boss_analyze():
    data = request.get_json()
    app.logger.info(f"Boss payload: {data}")

    # Dummy metrics & analysis—replace later with real logic
    dummy_metrics = [
        {
            "title": "Leadership Effectiveness",
            "labels": ["Vision", "Execution", "Empathy"],
            "values": [75, 60, 85]
        },
        {
            "title": "Team Engagement",
            "labels": ["Motivation", "Collaboration", "Trust"],
            "values": [70, 65, 80]
        }
    ]
    dummy_analysis = (
        f"Here’s a quick analysis for {data.get('memberName')}:\n\n"
        "- Strong Vision and Empathy; consider boosting Execution.\n"
        "- Team shows high Trust but needs more Collaboration.\n"
    )

    return jsonify({
        "metrics": dummy_metrics,
        "analysis": dummy_analysis
    })

if __name__ == '__main__':
    # if you ever run this locally via `python name_analysis_api.py`
    app.run(host='0.0.0.0', port=5000, debug=True)
