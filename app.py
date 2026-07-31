import os
import re
import json
import time
import random
import urllib.request
import urllib.error
from flask import Flask, render_template, request, jsonify, Response
from data import (
    schema_medic_data, 
    echo_trace_events, 
    http_request_stream,
    external_api_conversations,
    git_commits, 
    deployments, 
    add_schema_repair_record, 
    log_http_request,
    log_external_api_conversation,
    execute_rollback_state, 
    reset_demo_state,
    get_live_metrics,
    rollback_executed
)
from schema_repair import repair_json_payload, TARGET_SCHEMAS
from echo_engine import get_root_cause_analysis, handle_ai_chat

# Main EchoTrace & SchemaMedic Inspection Application on Port 5001
app = Flask(__name__)

TARGET_APP_URL = "http://127.0.0.1:5000"
DUP_LOG_FILE = "/home/sashank/Downloads/dup/requests.log"

processed_line_signatures = set()
last_500_logged_time = 0

def parse_dup_log_file():
    """
    Parses /home/sashank/Downloads/dup/requests.log and updates logs
    ONLY when a NEW user/browser HTTP request or HTTP Error is sent to Port 5000.
    """
    if not os.path.exists(DUP_LOG_FILE):
        return

    try:
        with open(DUP_LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        for line in lines:
            line_str = line.strip()
            if not line_str or line_str in processed_line_signatures:
                continue

            processed_line_signatures.add(line_str)

            # Match 1: Standard full request format with User-Agent
            match1 = re.search(r'(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}).*?\|\s*(GET|POST|PUT|DELETE|PATCH)\s+http://127\.0\.0\.1:5000([^\s|]*).*?User-Agent=([^\r\n]+)', line_str)
            
            # Match 2: Flask/Werkzeug log lines: 2026-07-31 15:50:49,060 | 127.0.0.1 - - [31/Jul/2026 15:50:49] "GET / HTTP/1.1" 500 -
            match2 = re.search(r'(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}).*?"(GET|POST|PUT|DELETE|PATCH)\s+([^\s"]+)\s+HTTP/[0-9.]+"\s+(\d{3})', line_str)

            if match1:
                dt_str, method, path, user_agent = match1.groups()
                if "SchemaMedic-EchoTrace-Inspector" in user_agent:
                    continue

                time_only = dt_str.split()[-1]
                path_clean = path if path else "/"
                status_code = 302 if method == 'POST' else 200
                status_text = "302 Found" if status_code == 302 else "200 OK"
                
                log_http_request(method, path_clean, status_code, 1.4, f"User-Agent: {user_agent[:45]}")

            elif match2:
                dt_str, method, path, status_code_str = match2.groups()
                status_code = int(status_code_str)
                time_only = dt_str.split()[-1]
                path_clean = path if path else "/"

                # If HTTP Error (4xx, 5xx), always log immediately into stream & critical events
                if status_code >= 400:
                    log_http_request(method, path_clean, status_code, 12.5, f"Port 5000 HTTP {status_code} Error Logged")

    except Exception as e:
        print("Log parsing error:", e)

def inspect_target_app_live():
    """
    Dynamic scanner for user's application on Port 5000.
    Measures status & latency and appends 500 Internal Server Errors immediately to logs & critical events.
    """
    global last_500_logged_time
    endpoints = ["/", "/health", "/api/telemetry", "/telemetry", "/api", "/metrics", "/data"]
    start_time = time.time()
    
    # Try 127.0.0.1 and localhost
    target_bases = [TARGET_APP_URL, "http://localhost:5000"]
    for base in target_bases:
        for ep in endpoints:
            url = f"{base}{ep}"
            try:
                req = urllib.request.Request(
                    url, 
                    headers={"User-Agent": "SchemaMedic-EchoTrace-Inspector/1.0", "Accept": "application/json, text/html, */*"}
                )
                with urllib.request.urlopen(req, timeout=2.5) as resp:
                    latency_ms = round((time.time() - start_time) * 1000, 2)
                    raw_body = resp.read().decode('utf-8', errors='ignore')
                    status_code = resp.status
                    content_type = resp.headers.get("Content-Type", "text/plain")
                    
                    parsed_json = None
                    try:
                        parsed_json = json.loads(raw_body)
                    except Exception:
                        parsed_json = None

                    return {
                        "connected": True,
                        "url": url,
                        "target_base": TARGET_APP_URL,
                        "port": 5000,
                        "status_code": status_code,
                        "status_text": f"{status_code} OK" if status_code == 200 else f"HTTP {status_code}",
                        "status_badge": "🟢 ONLINE (LIVE CONNECTED)",
                        "latency_ms": f"{latency_ms} ms",
                        "content_type": content_type,
                        "parsed_json": parsed_json,
                        "raw_preview": raw_body[:350] + ("..." if len(raw_body) > 350 else ""),
                        "timestamp": time.strftime("%H:%M:%S")
                    }
            except urllib.error.HTTPError as e:
                latency_ms = round((time.time() - start_time) * 1000, 2)
                raw_body = e.read().decode('utf-8', errors='ignore')
                
                # Immediately log 500 / 5xx HTTP Error to stream and critical events if not logged in last 3s
                now_t = time.time()
                if now_t - last_500_logged_time > 3.0:
                    last_500_logged_time = now_t
                    log_http_request("GET", ep, e.code, latency_ms, f"HTTP {e.code} Internal Error on Port 5000")

                return {
                    "connected": True,
                    "url": url,
                    "target_base": TARGET_APP_URL,
                    "port": 5000,
                    "status_code": e.code,
                    "status_text": f"HTTP {e.code} Error",
                    "status_badge": f"⚠️ ERROR ({e.code})",
                    "latency_ms": f"{latency_ms} ms",
                    "content_type": "text/plain",
                    "parsed_json": None,
                    "raw_preview": raw_body[:350] if raw_body else str(e),
                    "timestamp": time.strftime("%H:%M:%S")
                }
            except Exception:
                continue

    return {
        "connected": False,
        "url": TARGET_APP_URL,
        "target_base": TARGET_APP_URL,
        "port": 5000,
        "status_code": 0,
        "status_text": "Not Connected",
        "status_badge": "🔴 WAITING FOR PORT 5000 APP...",
        "latency_ms": "N/A",
        "content_type": "N/A",
        "parsed_json": None,
        "raw_preview": "No response on http://127.0.0.1:5000. Start your application on port 5000 to stream HTTP requests dynamically here.",
        "timestamp": time.strftime("%H:%M:%S")
    }

@app.template_filter('pretty_json')
def pretty_json_filter(val):
    try:
        if isinstance(val, str):
            val = json.loads(val)
        return json.dumps(val, indent=2)
    except Exception:
        return val

# --- HTML View Routes ---

@app.route("/")
def index():
    parse_dup_log_file()
    target_info = inspect_target_app_live()
    analysis = get_root_cause_analysis(echo_trace_events, rollback_executed, http_request_stream)
    metrics = get_live_metrics()
    return render_template(
        "index.html",
        schema_medic_data=schema_medic_data,
        echo_trace_events=echo_trace_events,
        analysis=analysis,
        rollback_executed=rollback_executed,
        target_info=target_info,
        metrics=metrics,
        http_requests=http_request_stream
    )

@app.route("/api-inspector")
def api_inspector():
    parse_dup_log_file()
    target_info = inspect_target_app_live()
    return render_template(
        "api_inspector.html",
        schema_medic_data=schema_medic_data,
        target_info=target_info
    )

@app.route("/incident-timeline")
def timeline():
    parse_dup_log_file()
    target_info = inspect_target_app_live()
    analysis = get_root_cause_analysis(echo_trace_events, rollback_executed, http_request_stream)
    filter_type = request.args.get("filter", "all")
    
    filtered_events = echo_trace_events
    if filter_type == "critical":
        filtered_events = [e for e in echo_trace_events if e["severity"] == "critical"]
    elif filter_type == "schema":
        filtered_events = [e for e in echo_trace_events if e["severity"] == "schema"]
    elif filter_type == "git":
        filtered_events = [e for e in echo_trace_events if e["severity"] in ["commit", "info"]]

    return render_template(
        "timeline.html",
        echo_trace_events=filtered_events,
        analysis=analysis,
        current_filter=filter_type,
        rollback_executed=rollback_executed,
        target_info=target_info
    )

@app.route("/root-cause")
def root_cause_view():
    parse_dup_log_file()
    target_info = inspect_target_app_live()
    analysis = get_root_cause_analysis(echo_trace_events, rollback_executed, http_request_stream)
    return render_template(
        "root_cause.html",
        analysis=analysis,
        git_commits=git_commits,
        deployments=deployments,
        rollback_executed=rollback_executed,
        target_info=target_info
    )

@app.route("/proxy-sandbox")
def proxy_sandbox():
    parse_dup_log_file()
    target_info = inspect_target_app_live()
    return render_template(
        "proxy_sandbox.html",
        schemas=TARGET_SCHEMAS,
        schema_medic_data=schema_medic_data,
        target_info=target_info
    )

# --- Dynamic Transparent HTTP Request Gateway & REST APIs ---

@app.route("/proxy/", defaults={'path': ''}, methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@app.route("/proxy/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def proxy_gateway(path):
    target_path = f"/{path}"
    start_time = time.time()
    req_body = request.get_data()
    req_headers = {k: v for k, v in request.headers if k.lower() != 'host'}

    if request.method in ["POST", "PUT", "PATCH"] and req_body:
        try:
            parsed_json = json.loads(req_body.decode('utf-8'))
            schema_id = "user_auth" if "usr" in str(parsed_json) or "user" in str(parsed_json) else "payment_transaction"
            repair_res = repair_json_payload(parsed_json, schema_id=schema_id)
            
            if repair_res["changes"]:
                new_rec = {
                    "id": f"MED-{100 + len(schema_medic_data) + 1}",
                    "schema_id": schema_id,
                    "service_name": f"Proxy Interceptor ({target_path})",
                    "original_payload": repair_res["original_payload"],
                    "repaired_payload": repair_res["repaired_payload"],
                    "confidence": repair_res["confidence"],
                    "time": time.strftime("%H:%M:%S"),
                    "changes": [c["reason"] for c in repair_res["changes"]]
                }
                add_schema_repair_record(new_rec)
                req_body = json.dumps(repair_res["parsed_repaired"]).encode('utf-8')
        except Exception:
            pass

    try:
        url = f"{TARGET_APP_URL}{target_path}"
        req = urllib.request.Request(
            url,
            data=req_body if request.method in ["POST", "PUT", "PATCH"] else None,
            headers=req_headers,
            method=request.method
        )
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            latency_ms = round((time.time() - start_time) * 1000, 2)
            resp_body = resp.read()
            status_code = resp.status

            log_http_request(request.method, target_path, status_code, latency_ms, req_body.decode('utf-8', errors='ignore')[:200])
            return Response(resp_body, status=status_code, content_type=resp.headers.get("Content-Type", "text/plain"))
    except urllib.error.HTTPError as e:
        latency_ms = round((time.time() - start_time) * 1000, 2)
        err_body = e.read()
        log_http_request(request.method, target_path, e.code, latency_ms, f"HTTP Error {e.code}")
        return Response(err_body, status=e.code, content_type=e.headers.get("Content-Type", "text/plain"))
    except Exception as ex:
        latency_ms = round((time.time() - start_time) * 1000, 2)
        log_http_request(request.method, target_path, 502, latency_ms, f"Proxy Error: {str(ex)}")
        return jsonify({"error": "Bad Gateway / Target App Offline on Port 5000", "details": str(ex)}), 502

@app.route("/api/dashboard/full-state", methods=["GET"])
def api_dashboard_full_state():
    parse_dup_log_file()
    target_info = inspect_target_app_live()
    analysis = get_root_cause_analysis(echo_trace_events, rollback_executed, http_request_stream)
    metrics = get_live_metrics()

    return jsonify({
        "target_info": target_info,
        "metrics": metrics,
        "http_requests": http_request_stream,
        "external_api_conversations": external_api_conversations,
        "schema_medic_data": schema_medic_data,
        "echo_trace_events": echo_trace_events,
        "analysis": analysis,
        "git_commits": git_commits,
        "rollback_executed": rollback_executed,
        "log_file_source": DUP_LOG_FILE,
        "timestamp": time.strftime("%H:%M:%S")
    })

@app.route("/api/external-conversations", methods=["GET"])
def api_get_external_conversations():
    return jsonify({
        "success": True,
        "count": len(external_api_conversations),
        "conversations": external_api_conversations
    })

@app.route("/api/trigger-external-apis", methods=["POST"])
def api_trigger_external_apis():
    """Triggers real external API calls on Port 5000 target application"""
    try:
        req = urllib.request.Request(
            f"{TARGET_APP_URL}/api/external/trigger",
            data=b"{}",
            headers={"Content-Type": "application/json", "User-Agent": "SchemaMedic-Platform/1.0"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=4.0) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return jsonify({"success": True, "details": data})
    except Exception as e:
        return jsonify({"success": False, "error": f"Target App on Port 5000 not reachable or error: {str(e)}"}), 500


@app.route("/api/proxy/repair-sample", methods=["POST"])
def api_proxy_repair_sample():
    """Fires a real HTTP API request with legacy/variant keys to Port 5000 app, capturing live SchemaMedic repair"""
    samples = [
        ("/api/users/login", "user_auth", {"usr_id": random.randint(1000, 9999), "action": "login"}),
        ("/api/payment/checkout", "payment_transaction", {"tx_id": f"TX-{random.randint(1000,9999)}", "amt": round(random.uniform(10, 500), 2), "curr": "USD"}),
        ("/api/sensor/telemetry", "sensor_telemetry", {"sensor": f"SNS-{random.randint(100,999)}", "temp": round(random.uniform(20, 80), 1)}),
        ("/api/profile/update", "user_profile", {"usr_id": random.randint(5000, 8000), "name": "Dynamic User"})
    ]
    endpoint, schema_id, payload = random.choice(samples)
    
    # Send actual HTTP POST request to Port 5000
    try:
        url = f"{TARGET_APP_URL}{endpoint}"
        req_data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=req_data,
            headers={"Content-Type": "application/json", "User-Agent": "SchemaMedic-Platform/1.0"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            resp_body = json.loads(resp.read().decode('utf-8'))
            latest_record = schema_medic_data[0] if schema_medic_data else {}
            return jsonify({"success": True, "http_status": resp.status, "port5000_response": resp_body, "record": latest_record})
    except Exception as e:
        # Fallback to direct call if Port 5000 app HTTP is initializing
        repair_res = repair_json_payload(payload, schema_id=schema_id)
        new_rec = {
            "id": f"MED-{100 + len(schema_medic_data) + 1}",
            "schema_id": schema_id,
            "service_name": f"Port 5000 ({endpoint})",
            "original_payload": repair_res["original_payload"],
            "repaired_payload": repair_res["repaired_payload"],
            "confidence": repair_res["confidence"],
            "time": time.strftime("%H:%M:%S"),
            "changes": [c["reason"] for c in repair_res["changes"]]
        }
        add_schema_repair_record(new_rec)
        return jsonify({"success": True, "record": new_rec, "fallback": str(e)})


@app.route("/api/proxy/repair", methods=["POST"])
def api_proxy_repair():
    start_time = time.time()
    try:
        data = request.get_json(force=True) or {}
        raw_payload = data.get("payload", {})
        schema_id = data.get("schema_id", "user_auth")
        target_path = data.get("target_path", "/")

        repair_result = repair_json_payload(raw_payload, schema_id=schema_id)
        
        new_id = f"MED-{100 + len(schema_medic_data) + 1}"
        record = {
            "id": new_id,
            "schema_id": schema_id,
            "service_name": f"Port 5000 Target App Proxy ({schema_id})",
            "original_payload": repair_result["original_payload"],
            "repaired_payload": repair_result["repaired_payload"],
            "confidence": repair_result["confidence"],
            "time": time.strftime("%H:%M:%S"),
            "changes": [c["reason"] for c in repair_result["changes"]]
        }
        add_schema_repair_record(record)

        forward_response = None
        status_code = 200
        try:
            post_data = json.dumps(repair_result["parsed_repaired"]).encode('utf-8')
            target_full_url = f"{TARGET_APP_URL}{target_path}"
            req = urllib.request.Request(
                target_full_url,
                data=post_data,
                headers={"Content-Type": "application/json", "User-Agent": "SchemaMedic-Proxy/1.0"}
            )
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                latency_ms = round((time.time() - start_time) * 1000, 2)
                status_code = resp.status
                body_resp = resp.read().decode('utf-8', errors='ignore')
                log_http_request("POST", target_path, status_code, latency_ms, repair_result["repaired_payload"])
                try:
                    forward_response = json.loads(body_resp)
                except Exception:
                    forward_response = {"status": status_code, "body": body_resp}
        except urllib.error.HTTPError as fe:
            latency_ms = round((time.time() - start_time) * 1000, 2)
            log_http_request("POST", target_path, fe.code, latency_ms, f"HTTP Error {fe.code}")
            forward_response = {"status_code": fe.code, "error": fe.reason}
        except Exception as fe:
            latency_ms = round((time.time() - start_time) * 1000, 2)
            log_http_request("POST", target_path, 502, latency_ms, f"Connection Refused")
            forward_response = {"forward_note": "Port 5000 app not listening or refused connection", "error": str(fe)}

        return jsonify({
            "success": True,
            "record": record,
            "repair": repair_result,
            "forward_response": forward_response
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/rollback", methods=["POST"])
def api_trigger_rollback():
    execute_rollback_state()
    return jsonify({
        "success": True,
        "message": "Automated Rollback Executed Successfully for PR #42 on Target App (Port 5000)",
        "rollback_executed": True
    })

@app.route("/api/ai-chat", methods=["POST"])
def api_chat():
    data = request.get_json(force=True) or {}
    message = data.get("message", "")
    response_text = handle_ai_chat(
        message, 
        events=echo_trace_events, 
        rollback_executed=rollback_executed, 
        http_requests=http_request_stream, 
        schema_data=schema_medic_data
    )
    return jsonify({
        "success": True,
        "reply": response_text
    })

@app.route("/api/demo/reset", methods=["POST"])
def api_demo_reset():
    reset_demo_state()
    return jsonify({"success": True, "message": "Demo state reset."})

if __name__ == "__main__":
    print("Starting EchoTrace & SchemaMedic Inspection Platform on http://0.0.0.0:5001 ...")
    app.run(host="0.0.0.0", port=5001, debug=True)
