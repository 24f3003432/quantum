from flask import Flask, request, jsonify
import time
from datetime import datetime

# Target Monitored Application running on Port 5000
target_app = Flask(__name__)

# Simulated database and metrics state on Port 5000
target_telemetry_logs = [
    {
        "time": datetime.now().strftime("%H:%M:%S"),
        "level": "INFO",
        "service": "TargetApp:Auth",
        "message": "Auth worker initialized on port 5000."
    },
    {
        "time": datetime.now().strftime("%H:%M:%S"),
        "level": "WARN",
        "service": "TargetApp:DB",
        "message": "Exclusive lock acquired by migration script alter_users_table.sql (PR #42)."
    }
]

@target_app.route("/")
def home():
    return jsonify({
        "app_name": "Target Microservice (Monitored App)",
        "port": 5000,
        "status": "RUNNING",
        "message": "This is the target application on port 5000 being inspected by SchemaMedic & EchoTrace on port 5001."
    })

@target_app.route("/health")
def health():
    return jsonify({
        "status": "UP",
        "port": 5000,
        "uptime": "99.4%",
        "active_threads": 42,
        "db_connections": "38/40 (NEAR CAPACITY)",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })

@target_app.route("/api/telemetry")
def telemetry():
    """Endpoint consumed by SchemaMedic & EchoTrace on Port 5001 to inspect Port 5000 app data"""
    return jsonify({
        "port": 5000,
        "cpu_usage": "78.4%",
        "memory_usage": "86.2%",
        "db_lock_active": True,
        "active_migration": "PR #42 (alter_users_table.sql)",
        "recent_logs": target_telemetry_logs
    })

@target_app.route("/api/users/login", methods=["POST"])
def user_login():
    """Sample target app endpoint expecting strict schema"""
    data = request.get_json(force=True) or {}
    target_telemetry_logs.insert(0, {
        "time": datetime.now().strftime("%H:%M:%S"),
        "level": "INFO",
        "service": "TargetApp:Auth",
        "message": f"Received payload: {data}"
    })
    
    # Check if required fields exist
    if "user_id" not in data:
        return jsonify({
            "error": "CRITICAL_SCHEMA_ERROR: Missing required field 'user_id'",
            "received_keys": list(data.keys())
        }), 400
    
    return jsonify({
        "status": "SUCCESS",
        "message": "Login processed successfully by target app on port 5000",
        "user_id": data["user_id"],
        "device_type": data.get("device_type", "unknown")
    })

if __name__ == "__main__":
    print("Starting Target Monitored Application on http://0.0.0.0:5000 ...")
    target_app.run(host="0.0.0.0", port=5000, debug=True)
