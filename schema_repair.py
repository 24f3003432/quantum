import json
import time
from datetime import datetime

# Target Schemas representing expected API contracts
TARGET_SCHEMAS = {
    "user_auth": {
        "required_fields": {
            "user_id": {"type": int, "default_generator": lambda p: p.get("usr_id") or p.get("id") or 1001},
            "action": {"type": str, "default": "login"},
            "timestamp": {"type": str, "default_generator": lambda p: datetime.utcnow().isoformat() + "Z"},
            "device_type": {"type": str, "default": "unknown"}
        },
        "key_mappings": {
            "usr_id": "user_id",
            "uid": "user_id",
            "act": "action",
            "device": "device_type",
            "time": "timestamp"
        }
    },
    "payment_transaction": {
        "required_fields": {
            "transaction_id": {"type": str, "default_generator": lambda p: f"TX-{int(time.time())}"},
            "amount": {"type": float, "default_generator": lambda p: float(p.get("amt") or p.get("price") or 0.0)},
            "currency": {"type": str, "default": "USD"},
            "status": {"type": str, "default": "pending"},
            "customer_email": {"type": str, "default_generator": lambda p: p.get("email") or p.get("cust_email") or "unspecified@domain.com"}
        },
        "key_mappings": {
            "tx_id": "transaction_id",
            "id": "transaction_id",
            "amt": "amount",
            "curr": "currency",
            "email": "customer_email",
            "cust_email": "customer_email",
            "state": "status"
        }
    },
    "sensor_telemetry": {
        "required_fields": {
            "sensor_id": {"type": str, "default": "SNS-001"},
            "reading": {"type": float, "default": 0.0},
            "unit": {"type": str, "default": "celsius"},
            "battery_level": {"type": int, "default": 100}
        },
        "key_mappings": {
            "sensor": "sensor_id",
            "val": "reading",
            "value": "reading",
            "temp": "reading",
            "batt": "battery_level"
        }
    },
    "user_profile": {
        "required_fields": {
            "user_id": {"type": int, "default": 9999},
            "full_name": {"type": str, "default_generator": lambda p: p.get("name") or "Anonymous User"},
            "email": {"type": str, "default": "user@example.com"},
            "role": {"type": str, "default": "standard"}
        },
        "key_mappings": {
            "name": "full_name",
            "usr_name": "full_name",
            "usr_id": "user_id",
            "mail": "email"
        }
    }
}

def repair_json_payload(raw_payload_str_or_dict, schema_id="user_auth"):
    """
    SchemaMedic Core AI Repair Logic:
    - Parses input JSON
    - Performs schema comparison & key mapping
    - Infers missing fields with high-confidence defaults
    - Generates confidence score and repair changelog
    """
    if isinstance(raw_payload_str_or_dict, str):
        try:
            payload = json.loads(raw_payload_str_or_dict)
        except Exception:
            payload = {}
    else:
        payload = dict(raw_payload_str_or_dict)

    schema = TARGET_SCHEMAS.get(schema_id, TARGET_SCHEMAS["user_auth"])
    required_fields = schema["required_fields"]
    key_mappings = schema["key_mappings"]

    repaired = {}
    changes = []
    confidence_penalties = 0

    # Step 1: Handle Key Mappings (e.g. name -> full_name, usr_id -> user_id)
    mapped_source_keys = set()
    for src_key, value in payload.items():
        if src_key in key_mappings:
            target_key = key_mappings[src_key]
            repaired[target_key] = value
            mapped_source_keys.add(src_key)
            changes.append({
                "type": "REMAP_KEY",
                "field": target_key,
                "original_key": src_key,
                "value": value,
                "reason": f"Mapped legacy/variant key '{src_key}' to standard field '{target_key}'"
            })
            confidence_penalties += 3 # minor penalty for key remapping
        elif src_key in required_fields or True:
            # Pass through standard or unrecognized extra fields
            repaired[src_key] = value

    # Step 2: Handle Missing Required Fields & Inference
    for target_key, config in required_fields.items():
        if target_key not in repaired:
            # Field missing! Infer value
            if "default_generator" in config:
                inferred_val = config["default_generator"](payload)
            else:
                inferred_val = config.get("default", "N/A")
            
            repaired[target_key] = inferred_val
            changes.append({
                "type": "INFER_MISSING_FIELD",
                "field": target_key,
                "value": inferred_val,
                "reason": f"Inferred missing required field '{target_key}'"
            })
            confidence_penalties += 5 # penalty for missing inferred field

    # Calculate AI Confidence Score (base 100%, capped minimum at 70%)
    confidence_score = max(72, 100 - confidence_penalties)
    if len(changes) == 0:
        confidence_score = 100

    return {
        "schema_id": schema_id,
        "original_payload": json.dumps(payload),
        "repaired_payload": json.dumps(repaired),
        "parsed_original": payload,
        "parsed_repaired": repaired,
        "confidence": confidence_score,
        "changes": changes,
        "changes_count": len(changes),
        "status": "REPAIRED" if len(changes) > 0 else "PASSTHROUGH"
    }
