import json
from datetime import datetime

# Global State Variables
rollback_executed = False

# Dynamic HTTP requests stream (populated ONLY when new HTTP requests occur on port 5000)
http_request_stream = []

schema_medic_data = [
    {
        "id": "MED-101",
        "schema_id": "user_auth",
        "service_name": "Port 5000 Auth Endpoint",
        "original_payload": json.dumps({"usr_id": 4021, "action": "login"}),
        "repaired_payload": json.dumps({"user_id": 4021, "action": "login", "timestamp": "2026-07-31T14:00:00Z", "device_type": "unknown"}),
        "confidence": 95,
        "time": "14:00:02",
        "changes": [
            "Remapped 'usr_id' ➔ 'user_id'",
            "Inferred missing field 'device_type' ➔ 'unknown'"
        ]
    },
    {
        "id": "MED-102",
        "schema_id": "payment_transaction",
        "service_name": "Port 5000 Payment Gateway",
        "original_payload": json.dumps({"tx_id": "TX-9821", "amt": 149.99, "curr": "USD"}),
        "repaired_payload": json.dumps({"transaction_id": "TX-9821", "amount": 149.99, "currency": "USD", "status": "pending", "customer_email": "unspecified@domain.com"}),
        "confidence": 92,
        "time": "14:00:08",
        "changes": [
            "Remapped 'tx_id' ➔ 'transaction_id'",
            "Remapped 'amt' ➔ 'amount'",
            "Inferred missing 'status' ➔ 'pending'"
        ]
    }
]

echo_trace_events = [
    {
        "id": "EVT-1001",
        "time": "13:58:00",
        "event_type": "Git Commit Deployed",
        "severity": "commit",
        "source": "Git / CI-CD",
        "description": "PR #42 deployed by alex.dev: 'alter_users_table.sql (Add index & migrate columns)'"
    }
]

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
    total_intercepted = len(schema_medic_data) + len(http_request_stream)
    failures_prevented = len(schema_medic_data)
    avg_confidence = round(sum(r.get("confidence", 90) for r in schema_medic_data) / max(1, len(schema_medic_data)), 1)
    
    return {
        "total_intercepted": total_intercepted,
        "failures_prevented": failures_prevented,
        "avg_confidence": f"{avg_confidence}%",
        "rollback_executed": rollback_executed,
        "state_badge": "RESOLVED" if rollback_executed else "ACTIVE INCIDENT"
    }
