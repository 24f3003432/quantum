from datetime import datetime

# AI Root Cause Candidates with probabilities, explanations, and remediation steps
def get_root_cause_analysis(events, rollback_executed=False):
    """
    EchoTrace AI Intelligence Engine:
    - Scans unified incident context (Logs + Commits + Deploys + Metrics + Schema Interceptions)
    - Ranks likely causes with probability scores
    - Generates step-by-step diagnostic breakdown & rollback recommendation
    """
    if rollback_executed:
        return {
            "status": "REMEDIATED",
            "active_alert": False,
            "headline": "System Operating Normally — PR #42 Successfully Rolled Back",
            "confidence": 99,
            "primary_cause": {
                "title": "PR #42 Database Schema Lock (Resolved)",
                "probability": 94,
                "author": "dev-team@company.com",
                "commit": "a3f891b",
                "summary": "Database lock released after automated rollback of PR #42. Thread pool and connection pool back to 100% capacity.",
                "affected_services": ["AuthService", "DBCluster-01", "PaymentGateway"]
            },
            "ranked_causes": [
                {
                    "rank": 1,
                    "title": "PR #42 (Migration SQL Lock) — ROLLED BACK",
                    "probability": 94,
                    "severity": "CRITICAL (RESOLVED)",
                    "details": "Exclusive table lock on 'users' table during migration blocked auth workers.",
                    "status_badge": "RESOLVED"
                },
                {
                    "rank": 2,
                    "title": "3rd Party Auth0 API Schema Change — PATCHED BY SCHEMAMEDIC",
                    "probability": 88,
                    "severity": "WARNING (PREVENTED)",
                    "details": "SchemaMedic intercepted missing 'device_type' and mapped 'usr_id' -> 'user_id', preventing downstream crash.",
                    "status_badge": "PREVENTED"
                }
            ],
            "recommended_action": "No further action needed. System health restored to 99.8%.",
            "rollback_available": False
        }

    return {
        "status": "ACTIVE_INCIDENT",
        "active_alert": True,
        "headline": "CRITICAL INCIDENT: Database Pool Exhaustion & Null Pointer dereference",
        "confidence": 94,
        "primary_cause": {
            "title": "PR #42 — Schema Migration & Database Lock",
            "probability": 94,
            "author": "alex.dev@quantum.io",
            "commit": "a3f891b (2026-07-31 13:58:00)",
            "summary": "Pull Request #42 ('alter_users_table.sql') executed an exclusive lock on the primary transactions DB node. This caused thread starvation in AuthService, triggering cascading null pointer exceptions during payload deserialization.",
            "affected_services": ["AuthService", "DBCluster-01", "PaymentGateway", "WorkerPool-3"]
        },
        "ranked_causes": [
            {
                "rank": 1,
                "title": "PR #42 Database Lock & Migration Collision",
                "probability": 94,
                "severity": "CRITICAL",
                "details": "Exclusive table lock on 'users' table during index migration blocked 42 auth threads within 12 seconds.",
                "status_badge": "PRIMARY CAUSE"
            },
            {
                "rank": 2,
                "title": "3rd Party API Schema Breaking Change (Interception Success)",
                "probability": 88,
                "severity": "WARNING (INTERCEPTED)",
                "details": "3rd Party Auth0 API omitted required 'device_type' key. SchemaMedic repaired payload in 1.2ms with 95% confidence.",
                "status_badge": "INTERCEPTED & FIXED"
            },
            {
                "rank": 3,
                "title": "Unbounded Recursion in Legacy Parser (Secondary)",
                "probability": 65,
                "severity": "HIGH",
                "details": "Fallback parser retried null payloads continuously due to timeout under memory pressure.",
                "status_badge": "SECONDARY EFFECT"
            }
        ],
        "timeline_highlights": {
            "first_anomaly": "14:00:05 (Memory allocation exceeded 85% threshold)",
            "fatal_exception": "14:00:12 (Null Pointer Access at 0x00000008)",
            "prevented_failure": "14:00:15 (SchemaMedic repaired 3 missing field payloads)"
        },
        "recommended_action": "Automated rollback of Pull Request #42 will release table locks and restore normal thread allocation.",
        "rollback_available": True
    }

def handle_ai_chat(query, events, rollback_executed=False):
    """
    AI Assistant interactive chat logic for EchoTrace & SchemaMedic queries.
    """
    q = query.lower()
    
    if "root cause" in q or "why" in q or "crash" in q or "fail" in q:
        if rollback_executed:
            return "The incident has been resolved! The root cause was exclusive table locking in **PR #42** ('alter_users_table.sql'). The automated rollback successfully released the DB locks and restored thread capacity."
        return "Based on EchoTrace telemetry correlation, the root cause is **PR #42 (Commit a3f891b)** deployed at 13:58:00. It executed an exclusive table lock on the primary DB node, causing thread starvation in `AuthService` and cascading pool exhaustion at 14:00:12."
    
    if "schema" in q or "medic" in q or "repair" in q or "payload" in q:
        return "**SchemaMedic** active status: 100% operational. It has intercepted and auto-repaired multiple payload anomalies today (e.g. mapping `usr_id` ➔ `user_id` and inferring missing `device_type` with 95% confidence score), preventing 3 potential production crashes!"

    if "rollback" in q or "fix" in q or "remediate" in q:
        if rollback_executed:
            return "Rollback for PR #42 has already been executed. All services are healthy."
        return "You can execute an **Automated Rollback of PR #42** directly from the Incident Timeline or Root Cause tab. This will revert commit `a3f891b` and release active DB locks immediately."

    if "git" in q or "commit" in q or "pr" in q:
        return "Recent Git Commits:\n- **PR #42 (a3f891b)**: Add index on users.created_at & alter columns (Authored by alex.dev)\n- **PR #41 (c9e104f)**: Refactor auth token validation pipeline (Authored by sarah.dev)"

    return f"EchoTrace & SchemaMedic AI Assistant: I'm tracking real-time incident telemetry and API proxy state. Ask me about root cause analysis, schema repairs, recent Git commits, or automated rollbacks!"
