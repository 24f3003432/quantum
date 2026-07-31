# SchemaMedic + EchoTrace
### An AI platform that prevents API failures — and diagnoses the ones it can't stop

> "Our platform doesn't just detect production failures — it prevents some
> failures from happening (SchemaMedic), and when failures still occur,
> EchoTrace finds the root cause automatically."

---

## The Pitch

Most reliability tooling does one job: it either watches your system or it
alerts you after something breaks. This platform does both ends of the
incident lifecycle in one integrated flow:

1. **SchemaMedic** sits in front of third-party APIs as a proxy. When an
   upstream API silently changes its response shape — a renamed field, a
   missing key, a type change — SchemaMedic detects the mismatch, repairs
   the payload using AI-assisted schema mapping, and forwards a
   contract-safe response to your backend. Many failures never happen at all.
2. **EchoTrace** watches what does go wrong. It ingests logs, metrics,
   deployment history, and git commits into a unified incident context,
   then uses an LLM to rank likely root causes, explain *why*, and suggest
   concrete next steps — in seconds instead of an on-call engineer digging
   through dashboards.

**Prevent what you can. Diagnose what you can't.** That combined story is
the core differentiator versus either feature alone.

---

## Architecture

```
                     Internet
                        │
                        ▼
               Third-party APIs
                        │
              ┌───────────────────┐
              │    SchemaMedic     │   API proxy · schema diff · AI repair
              └───────────────────┘
                        │
               Fixed API Response
                        │
                  Your Backend
                        │
                Logs + Metrics
                        │
              ┌───────────────────┐
              │     EchoTrace      │   Log/metric/git ingestion · AI RCA
              └───────────────────┘
                        │
             AI Root Cause Report
                        │
                        ▼
                  Dashboard (Person 5)
```

Two independent pipelines feed one dashboard: SchemaMedic protects the
request path, EchoTrace explains what happens after something still fails.

---

## Work Distribution (5 People)

### Person 1 — Backend & API Middleware (SchemaMedic core)
- API proxy / reverse proxy in front of third-party APIs
- Response interception
- Schema comparison against an expected contract
- Payload repair orchestration
- Forwarding the fixed response downstream
- **Tech:** FastAPI / Flask / Express, reverse proxy
- **Deliverable:** `Incoming API → Middleware → Fixed JSON`

### Person 2 — AI & Schema Repair
- Prompt engineering for repair suggestions
- JSON repair logic (structural fixes, not just field renames)
- Key mapping (e.g. `name → full_name`)
- Missing field inference
- Confidence scoring per repair
- **Tech:** GPT / Ollama, LangChain, Pydantic
- **Example:** `name → full_name → 95% confidence`

### Person 3 — EchoTrace Backend
- Reads logs
- Reads deployment history
- Parses git commits
- Collects monitoring events
- Generates a timeline
- **Pipeline:** `Logs + Metrics + Git + Deployment → Unified incident context`
- Sends this unified context as JSON to Person 4

### Person 4 — AI Root Cause Engine
- Analyzes the incident context from Person 3
- Ranks likely causes
- Generates plain-language explanations
- Suggests concrete debugging/remediation steps
- Produces structured incident summaries
- **Example output:** `Most likely cause → Recent migration → Rollback recommended`
- **Tech:** FastAPI, Pydantic, Ollama (Qwen2.5:7B) / OpenAI-compatible APIs, SQLite

### Person 5 — Frontend, Dashboard & Demo
- Incident dashboard
- Incident timeline view
- Schema diff / repair visualization
- AI chat interface for querying incidents
- Owns demo orchestration end-to-end
- **Screens:** Incident Dashboard · AI Analysis · API Inspector · Root Cause
  Timeline · Schema Repair Viewer

---

## Suggested Tech Stack

| Layer | Choice |
|---|---|
| Frontend | React + Tailwind CSS |
| Backend | FastAPI |
| LLM | Ollama (Qwen/Llama) or an OpenAI-compatible API |
| Database | PostgreSQL or SQLite |
| Monitoring | OpenTelemetry + Prometheus (or simulated metrics for the demo) |
| Visualization | Mermaid or React Flow for timelines and dependency graphs |

---

## Integration Contract

The two subsystems connect through two JSON handoffs:

1. **SchemaMedic → Backend:** a repaired, contract-conformant API response
   (Person 1 + Person 2's output).
2. **Person 3 → Person 4:** a unified incident context (logs, metrics,
   deployment history, git commits, API errors, incident ID + timestamp).
3. **Person 4 → Person 5:** a structured root cause report (summary,
   root cause, confidence, severity, evidence, recommendations, owning team).

Keeping these three contracts stable and documented early is what lets all
5 people build in parallel without blocking each other.

---

## Demo Story

A suggested live-demo arc for judges:

1. Show a third-party API returning a subtly broken payload (renamed/missing
   field).
2. Show SchemaMedic catching and repairing it transparently — your backend
   never sees the break.
3. Trigger a real incident (e.g. a bad deployment causing DB timeouts) that
   SchemaMedic can't prevent.
4. Show EchoTrace automatically ingesting logs/metrics/deploys/commits and
   producing a root cause report with a confidence score and a
   recommendation (e.g. "rollback to v2.13.2").
5. Close on the dashboard showing both systems working together: prevention
   on the left, diagnosis on the right.

---

## Estimated Hackathon Impact

| Scope | Estimated score |
|---|---|
| SchemaMedic only | 8.3 / 10 |
| EchoTrace only | 8.8 / 10 |
| **Combined platform (prevent + diagnose)** | **9.4 – 9.7 / 10** |

The combination tells a compelling end-to-end story: prevent failures
caused by API changes, and rapidly diagnose the failures that still occur.
That integrated prevention + incident-response workflow is the kind of
narrative that tends to stand out in hackathons, because it addresses both
resilience and incident response rather than just one.

---

## Getting Started

Each person's service can be developed and demoed independently before
integration:

```bash
# Person 1 + 2 (SchemaMedic)
cd schemamedic/
pip install -r requirements.txt
uvicorn app:app --reload --port 8000

# Person 3 + 4 (EchoTrace)
cd echotrace/
pip install -r requirements.txt
uvicorn app:app --reload --port 8001

# Person 5 (Dashboard)
cd dashboard/
npm install
npm run dev
```

Wire the dashboard to both backend ports once each service's contract is
stable, and point EchoTrace's `LLM_BACKEND` and SchemaMedic's repair engine
at whichever LLM provider you're using for the demo (Ollama for an offline
fallback, or a hosted API for speed/quality).
