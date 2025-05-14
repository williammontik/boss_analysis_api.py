from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # enable if your front end is on a different domain

@app.route('/boss_analyze', methods=['POST'])
def boss_analyze():
    data = request.get_json()
    # Log or inspect incoming payload
    app.logger.info(f"Received payload: {data}")

    # TODO: replace this with your real metric calculations & OpenAI call
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
        "- Leadership Effectiveness is solid, but could improve Execution.\n"
        "- Team Engagement metrics show high Trust but room to boost Collaboration.\n\n"
        "I recommend a targeted workshop on cross-team collaboration and a one-on-one coaching session focused on execution planning."
    )

    return jsonify({
        "metrics": dummy_metrics,
        "analysis": dummy_analysis
    })


if __name__ == '__main__':
    # Run on port 5000 by default
    app.run(host='0.0.0.0', port=5000, debug=True)
