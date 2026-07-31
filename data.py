import json
from datetime import datetime

# Global State Variables
rollback_executed = False

# Dynamic HTTP requests stream (populated ONLY when new HTTP requests occur on port 5000)
http_request_stream = []

import json
from datetime import datetime

# Global State Variables
rollback_executed = False

# Dynamic HTTP requests stream (populated ONLY when new HTTP requests occur on port 5000)
http_request_stream = []

# Dynamic External API Conversations Stream (captured from Port 5000 external API integrations)
external_api_conversations = []

# Dynamic SchemaMedic Repair Records
schema_medic_data = []

# Dynamic EchoTrace Events Stream
echo_trace_events = []

git_commits = [
    {
        "hash": "a3f891b",
        "branch": "main",
        "author": "alex.dev@quantum.io",
        "time": "13:58:00",
        "message": "PR #42: Add index on users.created_at & alter columns (alter_users_table.sql)",
        "files_changed": ["migrations/2026_07_31_alter_users.sql", "models/user.py"],
        "is_culprit": True
    },
    {
        "hash": "c9e104f",
        "branch": "main",
        "author": "sarah.dev@quantum.io",
        "time": "11:20:15",
        "message": "PR #41: Refactor auth token validation pipeline & session timeout handlers",
        "files_changed": ["auth/jwt.py", "auth/session.py"],
        "is_culprit": False
    }
]

deployments = [
    {
        "id": "DEP-9021",
        "env": "production-us-east",
        "commit": "a3f891b",
        "time": "13:58:00",
        "status": "COMPLETED_WITH_WARNINGS"
    }
]

def log_http_request(method, path, status_code, latency_ms, payload_summary=""):
    """Logs a real HTTP request event ONLY when a new request is sent to Port 5000"""
    now_str = datetime.now().strftime("%H:%M:%S")
    req_id = f"REQ-{len(http_request_stream) + 100}"
    status_text = f"{status_code} OK" if status_code == 200 else f"{status_code} Error"
    
    req_entry = {
        "id": req_id,
        "method": method.upper(),
        "path": path,
        "status_code": status_code,
        "status_text": status_text,
        "latency": f"{latency_ms} ms",
        "timestamp": now_str,
        "payload_summary": payload_summary
    }
    http_request_stream.insert(0, req_entry)

    severity = "critical" if status_code >= 500 else ("warning" if status_code >= 400 else "info")
    echo_trace_events.insert(0, {
        "id": f"EVT-{len(echo_trace_events) + 1000}",
        "time": now_str,
        "event_type": f"HTTP {method.upper()} Request",
        "severity": severity,
        "source": "TargetApp (Port 5000)",
        "description": f"HTTP {method.upper()} {path} - {status_text} ({latency_ms} ms)"
    })

    # Ensure every logged API call appears in SchemaMedic section as well
    svc_name = "Port 5000 App"
    if "weather" in path.lower():
        svc_name = f"Port 5000 Weather Service ({path})"
    elif "user" in path.lower() or "auth" in path.lower() or "login" in path.lower():
        svc_name = f"Port 5000 User Auth API ({path})"
    elif "payment" in path.lower() or "checkout" in path.lower():
        svc_name = f"Port 5000 Payment Gateway ({path})"
    elif "sensor" in path.lower() or "telemetry" in path.lower():
        svc_name = f"Port 5000 IoT Sensor API ({path})"
    elif "profile" in path.lower():
        svc_name = f"Port 5000 Profile Service ({path})"
    else:
        svc_name = f"Port 5000 API ({path})"

    orig_payload = payload_summary if payload_summary else f'{{"endpoint": "{path}", "method": "{method.upper()}"}}'
    
    repaired_payload = orig_payload
    if "usr_id" in orig_payload:
        repaired_payload = orig_payload.replace("usr_id", "user_id")
    elif "tx_id" in orig_payload:
        repaired_payload = orig_payload.replace("tx_id", "transaction_id")
    elif "amt" in orig_payload:
        repaired_payload = orig_payload.replace("amt", "amount")
    elif "temp" in orig_payload:
        repaired_payload = orig_payload.replace("temp", "temperature")
    elif "GET" in method.upper() or "weather" in path.lower():
        parts = path.strip("/").split("/")
        param_val = parts[-1] if len(parts) > 1 else "default"
        repaired_payload = f'{{"query": "{param_val}", "validated_path": "{path}", "status": "SCHEMA_VALIDATED"}}'

    medic_id = f"MED-{len(schema_medic_data) + 100}"
    schema_medic_record = {
        "id": medic_id,
        "schema_id": "api_request_interception",
        "service_name": svc_name,
        "target_path": path,
        "original_payload": orig_payload,
        "repaired_payload": repaired_payload,
        "confidence": 98 if status_code == 200 else 82,
        "time": now_str,
        "changes": [
            f"Intercepted HTTP {method.upper()} request to '{path}'",
            f"SchemaMedic verified payload structure & returned HTTP {status_code}"
        ]
    }
    schema_medic_data.insert(0, schema_medic_record)

def log_external_api_conversation(service_name, target_url, method, status_code, latency_ms, request_payload=None, response_payload=None):
    """
    Logs dynamic external API conversations captured from Port 5000 application external integrations.
    """
    now_str = datetime.now().strftime("%H:%M:%S")
    conv_id = f"EXT-{len(external_api_conversations) + 100}"
    
    req_str = json.dumps(request_payload) if isinstance(request_payload, (dict, list)) else str(request_payload or "N/A")
    resp_str = json.dumps(response_payload) if isinstance(response_payload, (dict, list)) else str(response_payload or "N/A")

    conv_entry = {
        "id": conv_id,
        "service_name": service_name,
        "target_url": target_url,
        "method": method.upper(),
        "status_code": status_code,
        "status_text": f"{status_code} OK" if status_code == 200 else f"HTTP {status_code}",
        "latency": f"{latency_ms} ms",
        "timestamp": now_str,
        "request_payload": req_str[:300],
        "response_payload": resp_str[:300]
    }
    external_api_conversations.insert(0, conv_entry)

    severity = "critical" if status_code >= 500 else ("warning" if status_code >= 400 else "info")
    echo_trace_events.insert(0, {
        "id": f"EVT-{len(echo_trace_events) + 1000}",
        "time": now_str,
        "event_type": f"External API ({service_name})",
        "severity": severity,
        "source": f"Port 5000 ➔ {service_name}",
        "description": f"External HTTP {method.upper()} {target_url} — {status_code} ({latency_ms} ms)"
    })
    
    # Also log to HTTP request stream for unified real-time visibility
    log_http_request(method, f"External: {service_name}", status_code, latency_ms, f"Target: {target_url}")
    return conv_entry

def add_schema_repair_record(record):
    """Adds a newly repaired payload record from Proxy Sandbox or live inspection"""
    schema_medic_data.insert(0, record)
    now_str = datetime.now().strftime("%H:%M:%S")
    echo_trace_events.insert(0, {
        "id": f"EVT-{len(echo_trace_events) + 1000}",
        "time": now_str,
        "event_type": "Schema Interception",
        "severity": "schema",
        "source": "SchemaMedic Proxy",
        "description": f"Intercepted & auto-repaired payload for '{record['service_name']}' ({record['confidence']}% confidence)."
    })

def execute_rollback_state():
    """Toggles rollback state for PR #42"""
    global rollback_executed
    rollback_executed = True
    now_str = datetime.now().strftime("%H:%M:%S")
    echo_trace_events.insert(0, {
        "id": f"EVT-{len(echo_trace_events) + 1000}",
        "time": now_str,
        "event_type": "Automated Rollback Executed",
        "severity": "info",
        "source": "EchoTrace Remediation Engine",
        "description": "Reverted Commit a3f891b (PR #42). Exclusive DB table lock released on Port 5000 app. System healthy."
    })

def reset_demo_state():
    """Resets the demo state back to default"""
    global rollback_executed
    rollback_executed = False

def get_live_metrics():
    """Computes dynamic metrics in real time"""
    total_intercepted = len(schema_medic_data) + len(http_request_stream) + len(external_api_conversations)
    failures_prevented = len(schema_medic_data)
    avg_confidence = round(sum(r.get("confidence", 90) for r in schema_medic_data) / max(1, len(schema_medic_data)), 1) if schema_medic_data else 95.0
    
    return {
        "total_intercepted": total_intercepted,
        "failures_prevented": failures_prevented,
        "external_api_count": len(external_api_conversations),
        "avg_confidence": f"{avg_confidence}%",
        "rollback_executed": rollback_executed,
        "state_badge": "RESOLVED" if rollback_executed else "ACTIVE INCIDENT"
    }

