from flask import Flask, request, jsonify
import time
import json
import urllib.request
import urllib.error
from datetime import datetime
from data import log_external_api_conversation, external_api_conversations

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
        # Fallback external service
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

# Trigger initial external API conversations on app module load
try:
    trigger_all_external_apis()
except Exception as ex:
    print("Initial external API trigger warning:", ex)

@target_app.route("/")
def home():
    return jsonify({
        "app_name": "Target Microservice (Monitored App)",
        "port": 5000,
        "status": "RUNNING",
        "message": "This is the target application on port 5000 being inspected by SchemaMedic & EchoTrace on port 5001.",
        "external_conversations_count": len(external_api_conversations)
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

