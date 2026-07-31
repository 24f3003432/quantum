import json

schema_medic_data = [
    {
        "id": "MED-101",
        "original_payload": json.dumps({"user_id": 4021, "action": "login", "timestamp": "2026-07-31T14:00:00Z"}),
        "repaired_payload": json.dumps({"user_id": 4021, "action": "login", "timestamp": "2026-07-31T14:00:00Z", "device_type": "unknown"}),
        "confidence": 95
    },
    {
        "id": "MED-102",
        "original_payload": json.dumps({"transaction_id": "TX-9821", "amount": 149.99, "currency": "USD"}),
        "repaired_payload": json.dumps({"transaction_id": "TX-9821", "amount": 149.99, "currency": "USD", "status": "pending"}),
        "confidence": 92
    },
    {
        "id": "MED-103",
        "original_payload": json.dumps({"sensor_id": "SNS-007", "reading": 42.8}),
        "repaired_payload": json.dumps({"sensor_id": "SNS-007", "reading": 42.8, "unit": "celsius"}),
        "confidence": 88
    }
]

echo_trace_events = [
    {
        "time": "14:00:01",
        "event_type": "System Check",
        "severity": "info",
        "description": "Routine diagnostic sequence initiated."
    },
    {
        "time": "14:00:05",
        "event_type": "High Memory Usage",
        "severity": "warning",
        "description": "Buffer allocation exceeded 85% capacity threshold."
    },
    {
        "time": "14:00:12",
        "event_type": "Null Pointer Access",
        "severity": "critical",
        "description": "Dereferenced invalid pointer at address 0x00000008."
    },
    {
        "time": "14:00:13",
        "event_type": "Stack Overflow",
        "severity": "critical",
        "description": "Unbounded recursion detected in payload parsing module."
    },
    {
        "time": "14:00:14",
        "event_type": "Process Crash",
        "severity": "critical",
        "description": "SIGSEGV received; process terminated unexpectedly."
    }
]
