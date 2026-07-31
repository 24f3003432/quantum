import json
from flask import Flask, render_template
from data import schema_medic_data, echo_trace_events

app = Flask(__name__)

@app.template_filter('pretty_json')
def pretty_json_filter(val):
    try:
        if isinstance(val, str):
            val = json.loads(val)
        return json.dumps(val, indent=2)
    except Exception:
        return val

@app.route("/")
def index():
    return render_template(
        "index.html",
        schema_medic_data=schema_medic_data,
        echo_trace_events=echo_trace_events
    )

@app.route("/api-inspector")
def api_inspector():
    return render_template(
        "api_inspector.html",
        schema_medic_data=schema_medic_data
    )

@app.route("/incident-timeline")
def timeline():
    return render_template(
        "timeline.html",
        echo_trace_events=echo_trace_events
    )

if __name__ == "__main__":
    app.run(debug=True)
