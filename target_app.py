from flask import Flask, request, jsonify
import time
import json
import urllib.request
import urllib.error
from datetime import datetime
from data import (
    log_external_api_conversation, 
    external_api_conversations,
    add_schema_repair_record,
    schema_medic_data,
    log_http_request
)
from schema_repair import repair_json_payload, TARGET_SCHEMAS

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

def process_schema_medic_api_request(service_name, target_endpoint, schema_id, raw_payload):
    """
    SchemaMedic API Conversation Handler:
    Intercepts incoming API request to Port 5000, performs schema validation & repair,
    logs the captured API conversation diff into schema_medic_data, and returns the repaired payload.
    """
    repair_result = repair_json_payload(raw_payload, schema_id=schema_id)
    
    new_id = f"MED-{100 + len(schema_medic_data) + 1}"
    record = {
        "id": new_id,
        "schema_id": schema_id,
        "service_name": service_name,
        "target_path": target_endpoint,
        "original_payload": repair_result["original_payload"],
        "repaired_payload": repair_result["repaired_payload"],
        "confidence": repair_result["confidence"],
        "time": datetime.now().strftime("%H:%M:%S"),
        "changes": [c["reason"] for c in repair_result["changes"]]
    }
    add_schema_repair_record(record)
    
    return repair_result["parsed_repaired"]

def fetch_external_weather():
    """Real External Weather API Conversation (Open-Meteo)"""
    url = "https://api.open-meteo.com/v1/forecast?latitude=37.7749&longitude=-122.4194&current_weather=true"
    start_t = time.time()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Port5000-App/1.0", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            latency = round((time.time() - start_t) * 1000, 2)
            raw = resp.read().decode('utf-8')
            parsed = json.loads(raw)
            return log_external_api_conversation(
                service_name="Open-Meteo Weather API",
                target_url=url,
                method="GET",
                status_code=resp.status,
                latency_ms=latency,
                request_payload={"latitude": 37.7749, "longitude": -122.4194},
                response_payload=parsed.get("current_weather", parsed)
            )
    except Exception as e:
        latency = round((time.time() - start_t) * 1000, 2)
        return log_external_api_conversation(
            service_name="Open-Meteo Weather API",
            target_url=url,
            method="GET",
            status_code=502,
            latency_ms=latency,
            request_payload={"error": str(e)},
            response_payload={"error": "Failed to connect to external weather endpoint"}
        )

def fetch_external_currency():
    """Real External Exchange Rates API Conversation"""
    url = "https://open.er-api.com/v6/latest/USD"
    start_t = time.time()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Port5000-App/1.0", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            latency = round((time.time() - start_t) * 1000, 2)
            raw = resp.read().decode('utf-8')
            parsed = json.loads(raw)
            rates_sample = {k: parsed.get("rates", {}).get(k) for k in ["EUR", "GBP", "JPY", "CAD", "INR"] if k in parsed.get("rates", {})}
            return log_external_api_conversation(
                service_name="External Exchange Rates API",
                target_url=url,
                method="GET",
                status_code=resp.status,
                latency_ms=latency,
                request_payload={"base_currency": "USD"},
                response_payload={"base": "USD", "rates_sample": rates_sample}
            )
    except Exception as e:
        url_alt = "https://jsonplaceholder.typicode.com/posts/1"
        try:
            req = urllib.request.Request(url_alt, headers={"User-Agent": "Port5000-App/1.0"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                latency = round((time.time() - start_t) * 1000, 2)
                parsed = json.loads(resp.read().decode('utf-8'))
                return log_external_api_conversation(
                    service_name="JSONPlaceholder External Post API",
                    target_url=url_alt,
                    method="GET",
                    status_code=resp.status,
                    latency_ms=latency,
                    request_payload={"post_id": 1},
                    response_payload=parsed
                )
        except Exception as fe:
            latency = round((time.time() - start_t) * 1000, 2)
            return log_external_api_conversation(
                service_name="External Currency API",
                target_url=url,
                method="GET",
                status_code=500,
                latency_ms=latency,
                request_payload={"error": str(fe)},
                response_payload={"status": "error"}
            )

def fetch_external_user_service():
    """Real External Identity Service Conversation (JSONPlaceholder Users)"""
    url = "https://jsonplaceholder.typicode.com/users/1"
    start_t = time.time()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Port5000-App/1.0", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            latency = round((time.time() - start_t) * 1000, 2)
            parsed = json.loads(resp.read().decode('utf-8'))
            return log_external_api_conversation(
                service_name="External User Identity Service",
                target_url=url,
                method="GET",
                status_code=resp.status,
                latency_ms=latency,
                request_payload={"fetch_user_id": 1},
                response_payload={"id": parsed.get("id"), "name": parsed.get("name"), "email": parsed.get("email"), "company": parsed.get("company", {}).get("name")}
            )
    except Exception as e:
        latency = round((time.time() - start_t) * 1000, 2)
        return log_external_api_conversation(
            service_name="External Identity Service",
            target_url=url,
            method="GET",
            status_code=502,
            latency_ms=latency,
            request_payload={"error": str(e)},
            response_payload={"error": "Identity service connection timeout"}
        )

def trigger_all_external_apis():
    """Executes all external API conversations from Port 5000"""
    res1 = fetch_external_weather()
    res2 = fetch_external_currency()
    res3 = fetch_external_user_service()
    return [res1, res2, res3]

def trigger_initial_schema_medic_conversations():
    """
    Fires real initial API conversations with variant payloads to Port 5000 endpoints
    so SchemaMedic captures actual API conversations from Port 5000 app right at startup!
    """
    sample_conversations = [
        ("Port 5000 User Auth API", "/api/users/login", "user_auth", {"usr_id": 4021, "action": "login"}),
        ("Port 5000 Payment Gateway", "/api/payment/checkout", "payment_transaction", {"tx_id": "TX-9821", "amt": 149.99, "curr": "USD"}),
        ("Port 5000 IoT Sensor Service", "/api/sensor/telemetry", "sensor_telemetry", {"sensor": "SNS-901", "temp": 48.2}),
        ("Port 5000 Profile Service", "/api/profile/update", "user_profile", {"usr_id": 7812, "name": "Alex Dev"})
    ]
    for service, path, schema, payload in sample_conversations:
        process_schema_medic_api_request(service, path, schema, payload)

# Trigger initial external and SchemaMedic API conversations on module load
try:
    trigger_all_external_apis()
    trigger_initial_schema_medic_conversations()
except Exception as ex:
    print("Initial API trigger warning:", ex)

@target_app.route("/")
def home():
    return jsonify({
        "app_name": "Target Microservice (Monitored App)",
        "port": 5000,
        "status": "RUNNING",
        "message": "This is the target application on port 5000 being inspected by SchemaMedic & EchoTrace on port 5001.",
        "external_conversations_count": len(external_api_conversations),
        "schema_medic_repairs_count": len(schema_medic_data)
    })

@target_app.route("/health")
def health():
    return jsonify({
        "status": "UP",
        "port": 5000,
        "uptime": "99.4%",
        "active_threads": 42,
        "db_connections": "38/40 (NEAR CAPACITY)",
        "external_api_captured": len(external_api_conversations),
        "schema_medic_captured": len(schema_medic_data),
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
        "external_conversations": external_api_conversations,
        "schema_medic_repairs": schema_medic_data,
        "recent_logs": target_telemetry_logs
    })

@target_app.route("/api/external/weather")
def route_external_weather():
    res = fetch_external_weather()
    return jsonify({"status": "SUCCESS", "conversation": res})

@target_app.route("/api/external/rates")
def route_external_rates():
    res = fetch_external_currency()
    return jsonify({"status": "SUCCESS", "conversation": res})

@target_app.route("/api/external/user-sync")
def route_external_user_sync():
    res = fetch_external_user_service()
    return jsonify({"status": "SUCCESS", "conversation": res})

@target_app.route("/api/external/trigger", methods=["POST", "GET"])
def route_external_trigger():
    res = trigger_all_external_apis()
    return jsonify({"status": "SUCCESS", "triggered_count": len(res), "conversations": res})

@target_app.route("/api/external/conversations")
def route_external_conversations():
    return jsonify({
        "port": 5000,
        "total_captured": len(external_api_conversations),
        "conversations": external_api_conversations
    })

@target_app.route("/api/users/login", methods=["POST"])
def user_login():
    """Port 5000 User Auth API Endpoint protected by SchemaMedic"""
    raw_data = request.get_json(force=True) or {}
    repaired_data = process_schema_medic_api_request("Port 5000 User Auth Endpoint", "/api/users/login", "user_auth", raw_data)
    
    target_telemetry_logs.insert(0, {
        "time": datetime.now().strftime("%H:%M:%S"),
        "level": "INFO",
        "service": "TargetApp:Auth",
        "message": f"Processed login for user_id={repaired_data.get('user_id')}"
    })
    
    return jsonify({
        "status": "SUCCESS",
        "message": "Login processed successfully by target app on port 5000",
        "repaired_payload": repaired_data,
        "user_id": repaired_data.get("user_id"),
        "device_type": repaired_data.get("device_type", "unknown")
    })

@target_app.route("/api/payment/checkout", methods=["POST"])
def payment_checkout():
    """Port 5000 Payment Gateway API Endpoint protected by SchemaMedic"""
    raw_data = request.get_json(force=True) or {}
    repaired_data = process_schema_medic_api_request("Port 5000 Payment Gateway", "/api/payment/checkout", "payment_transaction", raw_data)
    
    return jsonify({
        "status": "SUCCESS",
        "message": "Payment transaction processed successfully on port 5000",
        "repaired_payload": repaired_data,
        "transaction_id": repaired_data.get("transaction_id"),
        "amount": repaired_data.get("amount")
    })

@target_app.route("/api/sensor/telemetry", methods=["POST"])
def sensor_telemetry():
    """Port 5000 IoT Sensor API Endpoint protected by SchemaMedic"""
    raw_data = request.get_json(force=True) or {}
    repaired_data = process_schema_medic_api_request("Port 5000 IoT Sensor Service", "/api/sensor/telemetry", "sensor_telemetry", raw_data)
    
    return jsonify({
        "status": "SUCCESS",
        "message": "Sensor telemetry logged on port 5000",
        "repaired_payload": repaired_data,
        "sensor_id": repaired_data.get("sensor_id"),
        "reading": repaired_data.get("reading")
    })

@target_app.route("/api/profile/update", methods=["POST"])
def profile_update():
    """Port 5000 User Profile API Endpoint protected by SchemaMedic"""
    raw_data = request.get_json(force=True) or {}
    repaired_data = process_schema_medic_api_request("Port 5000 Profile Service", "/api/profile/update", "user_profile", raw_data)
    
    return jsonify({
        "status": "SUCCESS",
        "message": "User profile updated on port 5000",
        "repaired_payload": repaired_data,
        "user_id": repaired_data.get("user_id"),
        "full_name": repaired_data.get("full_name")
    })

if __name__ == "__main__":
    print("Starting Target Monitored Application on http://0.0.0.0:5000 ...")
    target_app.run(host="0.0.0.0", port=5000, debug=True)


