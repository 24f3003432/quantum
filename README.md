# SchemaMedic + EchoTrace

### An AI platform that prevents API failures and automatically identifies the root cause of production incidents.

> **Prevent failures before they happen. Diagnose the ones you can't prevent.**

---

# Problem Statement

Modern applications depend on third-party APIs and distributed services. A small API schema change or an unexpected production issue can lead to application failures, downtime, and lengthy debugging.

Existing tools either monitor failures after they occur or validate API contracts during development. Our solution bridges this gap by combining intelligent API resilience with AI-powered root cause analysis.

---

# Our Solution

SchemaMedic + EchoTrace is an integrated AI platform that improves application reliability in two ways:

- **SchemaMedic** intercepts third-party API responses, detects schema mismatches, and automatically repairs incompatible responses before they reach the application.
- **EchoTrace** analyzes logs, metrics, deployment history, and code changes to identify the most likely root cause of production incidents and recommend the next debugging steps.

Together, they provide both **failure prevention** and **rapid incident diagnosis** within a single platform.

---

# Architecture

```
                     Internet
                        │
                        ▼
               Third-party APIs
                        │
              ┌───────────────────┐
              │    SchemaMedic     │
              │ AI Schema Repair   │
              └───────────────────┘
                        │
               Fixed API Response
                        │
                  Application
                        │
                Logs + Metrics
                        │
              ┌───────────────────┐
              │     EchoTrace      │
              │ AI Root Cause      │
              └───────────────────┘
                        │
              AI Incident Report
                        │
                        ▼
                 Unified Dashboard
```

---

# Key Features

### SchemaMedic
- Detects API schema changes automatically.
- Repairs incompatible JSON responses using AI.
- Prevents application failures caused by API contract changes.
- Returns a contract-safe response to the backend.

### EchoTrace
- Collects logs, metrics, deployment history, and Git commits.
- Uses AI to identify the most probable root cause.
- Generates human-readable explanations.
- Suggests actionable remediation steps.

---

# Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python (Flask) |
| AI | Featherless AI |
| Database | SQLite |

---

# How It Works

1. A third-party API returns an unexpected or incompatible response.
2. SchemaMedic detects the schema mismatch and automatically repairs the response before forwarding it to the application.
3. If a production issue still occurs, EchoTrace collects logs, metrics, deployment history, and Git changes.
4. The AI analyzes the collected evidence, identifies the most likely root cause, and generates recommended debugging actions.
5. The dashboard presents both the repaired API response and the complete AI-powered incident analysis.

---

# Demo Flow

1. Simulate an API schema change.
2. Show SchemaMedic automatically repairing the response.
3. Trigger a production incident.
4. Demonstrate EchoTrace identifying the root cause.
5. Display the complete analysis on the unified dashboard.

---

# Why Our Solution?

Unlike traditional monitoring tools that only report failures after they occur, our platform actively prevents avoidable failures while also providing intelligent root cause analysis for incidents that cannot be prevented. This end-to-end approach reduces downtime, accelerates debugging, and improves overall system reliability.

---

# Getting Started

```bash
pip install -r requirements.txt
python app.py
```

Open:

```
http://localhost:5000
```
