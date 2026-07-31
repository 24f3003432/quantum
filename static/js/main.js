// Client-side 100% Real-Time Reactive UI Engine for SchemaMedic & EchoTrace (Port 5001)

document.addEventListener("DOMContentLoaded", () => {
    fetchFullDynamicState();
    setInterval(fetchFullDynamicState, 2000);
});

async function fetchFullDynamicState() {
    try {
        const response = await fetch("/api/dashboard/full-state");
        const data = await response.json();
        
        // 1. Navbar Status Pill
        updateStatusPill(data.target_info);

        // 2. Metrics Grid
        updateMetricsGrid(data.metrics);

        // 3. Dynamic HTTP Request Stream
        updateHTTPRequestStream(data.http_requests, data.target_info);

        // 4. SchemaMedic Repair Feeds (Dashboard Table + Full Inspector Cards)
        updateSchemaMedicTable(data.schema_medic_data);
        updateSchemaMedicInspector(data.schema_medic_data);

        // 5. EchoTrace Events Timeline
        updateEchoTraceEvents(data.echo_trace_events);

        // 6. AI Root Cause Analysis Cards (Updated ONLY on page load or outside /root-cause to prevent flicker)
        if (window.location.pathname !== "/root-cause") {
            updateAIRootCause(data.analysis, data.rollback_executed);
        }

        // 7. Git Commit Risk Table
        updateGitCommitsTable(data.git_commits);

    } catch (e) {
        console.warn("Dynamic state polling warning:", e);
    }
}

// 1. Navbar Status Pill
function updateStatusPill(info) {
    const textEl = document.getElementById("statusPillText");
    const containerEl = document.getElementById("statusPillContainer");
    if (textEl && info) {
        textEl.innerText = "Target App (Port 5000): " + (info.connected ? "🟢 ONLINE (" + info.latency_ms + ")" : "🔴 WAITING...");
        if (containerEl) {
            containerEl.style.background = info.connected ? "rgba(16, 185, 129, 0.15)" : "rgba(239, 68, 68, 0.15)";
            containerEl.style.borderColor = info.connected ? "rgba(16, 185, 129, 0.3)" : "rgba(239, 68, 68, 0.3)";
            containerEl.style.color = info.connected ? "#34d399" : "#fca5a5";
        }
    }
}

// 2. Metrics Grid
function updateMetricsGrid(metrics) {
    if (!metrics) return;
    const elPrev = document.getElementById("metricFailuresPrevented");
    const elInt = document.getElementById("metricIntercepted");
    const elConf = document.getElementById("metricConfidence");
    const elState = document.getElementById("metricState");
    const elIcon = document.getElementById("metricStateIcon");

    if (elPrev) elPrev.innerText = metrics.failures_prevented;
    if (elInt) elInt.innerText = metrics.total_intercepted;
    if (elConf) elConf.innerText = metrics.avg_confidence;
    if (elState) elState.innerText = metrics.state_badge;
    if (elIcon) elIcon.innerText = metrics.rollback_executed ? "✅" : "🚨";
}

// 3. Dynamic HTTP Request Stream
function updateHTTPRequestStream(requests, info) {
    const cardEl = document.getElementById("liveTargetStatusBody");
    if (!cardEl) return;

    if (!info || !info.connected) {
        cardEl.innerHTML = `
            <div style="background: rgba(239, 68, 68, 0.08); border: 1px solid var(--red-border); border-radius: 8px; padding: 1.25rem; text-align: center;">
                <div style="font-size: 1.5rem; margin-bottom: 0.3rem;">🔴</div>
                <div style="font-size: 1.05rem; font-weight: 800; color: #fca5a5;">Waiting for Port 5000 Application</div>
                <p style="margin: 0.4rem 0 0 0; font-size: 0.88rem; color: var(--text-muted);">
                    No active listener found on <code>http://127.0.0.1:5000</code>. Start your app on port 5000 and HTTP requests will stream here dynamically.
                </p>
            </div>
        `;
        return;
    }

    let rowsHtml = "";
    if (requests && requests.length > 0) {
        requests.slice(0, 5).forEach(req => {
            const methodColor = req.method === "POST" ? "#38bdf8" : (req.method === "GET" ? "#34d399" : "#c084fc");
            const statusColor = req.status_code >= 500 ? "#fca5a5" : (req.status_code >= 400 ? "#fbbf24" : "#34d399");
            
            rowsHtml += `
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <td style="padding: 0.5rem 0.75rem;"><span style="font-size: 0.75rem; font-weight: 800; padding: 0.2rem 0.5rem; border-radius: 4px; background: rgba(255,255,255,0.06); color: ${methodColor};">${req.method}</span></td>
                    <td style="padding: 0.5rem 0.75rem;"><code style="color: #e2e8f0;">${escapeHtml(req.path)}</code></td>
                    <td style="padding: 0.5rem 0.75rem;"><span style="font-weight: 700; color: ${statusColor};">${req.status_text}</span></td>
                    <td style="padding: 0.5rem 0.75rem; color: #c084fc; font-weight: 600;">⚡ ${req.latency}</td>
                    <td style="padding: 0.5rem 0.75rem; color: var(--text-muted); font-size: 0.8rem;">${req.timestamp}</td>
                </tr>
            `;
        });
    } else {
        rowsHtml = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted); padding: 1rem;">No HTTP requests recorded yet. Make a request to Port 5000 or via <code>/proxy/...</code> to view dynamic stream.</td></tr>`;
    }

    cardEl.innerHTML = `
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 1rem;">
            <div style="background: rgba(15, 23, 42, 0.7); padding: 0.85rem; border-radius: 8px; border: 1px solid var(--green-border);">
                <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; font-weight: 700;">Target App Status</div>
                <div style="font-size: 1.1rem; font-weight: 800; color: #34d399; margin-top: 0.2rem;">🟢 ONLINE (${info.status_text})</div>
            </div>
            <div style="background: rgba(15, 23, 42, 0.7); padding: 0.85rem; border-radius: 8px; border: 1px solid var(--card-border);">
                <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; font-weight: 700;">Proxy Gateway URL</div>
                <div style="font-size: 1.05rem; font-weight: 800; color: #38bdf8; margin-top: 0.2rem;">http://127.0.0.1:5001/proxy/</div>
            </div>
            <div style="background: rgba(15, 23, 42, 0.7); padding: 0.85rem; border-radius: 8px; border: 1px solid var(--card-border);">
                <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; font-weight: 700;">Latest Latency</div>
                <div style="font-size: 1.05rem; font-weight: 800; color: #c084fc; margin-top: 0.2rem;">⚡ ${info.latency_ms}</div>
            </div>
        </div>
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid var(--card-border); border-radius: 8px; padding: 0.85rem;">
            <div style="font-size: 0.78rem; color: var(--text-muted); text-transform: uppercase; font-weight: 700; margin-bottom: 0.5rem;">Live Dynamic HTTP Requests Stream (Port 5000 Traffic)</div>
            <table style="width: 100%; border-collapse: collapse; text-align: left;">
                <thead>
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.1); font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase;">
                        <th style="padding: 0.4rem 0.75rem;">Method</th>
                        <th style="padding: 0.4rem 0.75rem;">Path</th>
                        <th style="padding: 0.4rem 0.75rem;">Status</th>
                        <th style="padding: 0.4rem 0.75rem;">Latency</th>
                        <th style="padding: 0.4rem 0.75rem;">Time</th>
                    </tr>
                </thead>
                <tbody>
                    ${rowsHtml}
                </tbody>
            </table>
        </div>
    `;
}

// 4. SchemaMedic Repair Table Feed (Dashboard)
function updateSchemaMedicTable(records) {
    const tableBody = document.getElementById("schemaMedicTableBody");
    if (!tableBody || !records) return;

    let html = "";
    records.slice(0, 6).forEach(item => {
        html += `
            <tr style="transition: all 0.3s ease;">
                <td><span class="item-id-badge">${item.id}</span></td>
                <td><strong>${item.service_name}</strong></td>
                <td><code style="color: var(--red-text); font-size: 0.85rem;">${escapeHtml(item.original_payload)}</code></td>
                <td><code style="color: var(--green-text); font-size: 0.85rem;">${escapeHtml(item.repaired_payload)}</code></td>
                <td><span class="confidence-badge">${item.confidence}%</span></td>
            </tr>
        `;
    });
    tableBody.innerHTML = html;
}

// 4b. SchemaMedic Full Visual Diff Inspector Cards Feed
function updateSchemaMedicInspector(records) {
    const feedContainer = document.getElementById("inspectorFeedContainer");
    if (!feedContainer || !records) return;

    let html = "";
    records.forEach(item => {
        let changesHtml = "";
        if (item.changes && item.changes.length > 0) {
            let liHtml = item.changes.map(c => `<li>${escapeHtml(c)}</li>`).join("");
            changesHtml = `
                <div class="changes-box">
                    <h4>Applied Key Mappings & Field Inferences</h4>
                    <ul class="changes-ul">
                        ${liHtml}
                    </ul>
                </div>
            `;
        }

        let origPretty = item.original_payload;
        let repPretty = item.repaired_payload;
        try { origPretty = JSON.stringify(JSON.parse(item.original_payload), null, 2); } catch(e){}
        try { repPretty = JSON.stringify(JSON.parse(item.repaired_payload), null, 2); } catch(e){}

        html += `
            <div class="inspector-card" style="margin-bottom: 1.5rem; animation: fadeIn 0.4s ease-in-out;">
                <div class="card-top-bar">
                    <div class="item-meta">
                        <span class="item-id-badge">${item.id}</span>
                        <span class="service-tag">Target API: <strong>${escapeHtml(item.service_name)}</strong></span>
                        <span style="font-size: 0.8rem; color: var(--text-muted); margin-left: 0.75rem;">🕒 ${item.time || ''}</span>
                    </div>
                    <div class="confidence-container">
                        <span class="confidence-label">AI Repair Confidence</span>
                        <span class="confidence-score">${item.confidence}%</span>
                    </div>
                </div>

                <div class="diff-grid">
                    <div class="diff-panel original-panel">
                        <div class="panel-header header-red">
                            <span class="panel-icon">❌</span>
                            <span class="panel-title">Original Payload (Missing / Variant Keys)</span>
                        </div>
                        <div class="code-wrapper wrapper-red">
                            <pre><code class="language-json">${escapeHtml(origPretty)}</code></pre>
                        </div>
                    </div>

                    <div class="diff-panel repaired-panel">
                        <div class="panel-header header-green">
                            <span class="panel-icon">✅</span>
                            <span class="panel-title">SchemaMedic Repaired Payload (Valid JSON Forwarded)</span>
                        </div>
                        <div class="code-wrapper wrapper-green">
                            <pre><code class="language-json">${escapeHtml(repPretty)}</code></pre>
                        </div>
                    </div>
                </div>

                ${changesHtml}
            </div>
        `;
    });

    feedContainer.innerHTML = html;
}

// 5. EchoTrace Events Timeline
function updateEchoTraceEvents(events) {
    const tableBody = document.getElementById("echoTraceTableBody");
    const timelineList = document.getElementById("timelineList");

    if (tableBody && events) {
        let html = "";
        events.slice(0, 6).forEach(evt => {
            html += `
                <tr>
                    <td><code>${evt.time}</code></td>
                    <td><span style="color: var(--text-muted);">${evt.source}</span></td>
                    <td><strong>${evt.event_type}</strong></td>
                    <td><span class="badge badge-${evt.severity}">${evt.severity.toUpperCase()}</span></td>
                    <td>${escapeHtml(evt.description)}</td>
                </tr>
            `;
        });
        tableBody.innerHTML = html;
    }

    if (timelineList && events) {
        let listHtml = "";
        events.forEach(evt => {
            listHtml += `
                <div class="timeline-item">
                    <div class="timeline-node node-${evt.severity}"></div>
                    <div class="timeline-card">
                        <div class="timeline-card-header">
                            <div>
                                <span class="timeline-time">${evt.time}</span>
                                <span class="event-source">${evt.source}</span>
                            </div>
                            <span class="badge badge-${evt.severity}">${evt.severity.toUpperCase()}</span>
                        </div>
                        <h3 class="event-title">${escapeHtml(evt.event_type)}</h3>
                        <p class="event-desc">${escapeHtml(evt.description)}</p>
                    </div>
                </div>
            `;
        });
        timelineList.innerHTML = listHtml;
    }
}

// 6. AI Root Cause Panel & Hub
function updateAIRootCause(analysis, rollbackExecuted) {
    if (!analysis) return;

    const headlineEl = document.getElementById("aiHeadline");
    const confidenceEl = document.getElementById("aiConfidence");
    const summaryTextEl = document.getElementById("aiSummaryText");
    const causesContainer = document.getElementById("rankedCausesList");
    const bannerCard = document.getElementById("aiBannerCard");
    const statusBadge = document.getElementById("aiStatusBadge");

    if (headlineEl) headlineEl.innerText = analysis.headline;
    if (confidenceEl) confidenceEl.innerText = analysis.confidence + "%";
    
    if (summaryTextEl) {
        summaryTextEl.innerText = analysis.summary || (analysis.primary_cause ? analysis.primary_cause.summary : "System operational.");
    }

    const isHealthy = (analysis.status === "NO_ISSUES" || !analysis.has_error || rollbackExecuted);

    if (bannerCard) {
        bannerCard.style.borderLeft = isHealthy ? "4px solid #10b981" : "4px solid #ef4444";
    }

    if (statusBadge) {
        statusBadge.className = isHealthy ? "badge badge-schema" : "badge badge-critical";
        if (analysis.status === "NO_ISSUES") {
            statusBadge.innerText = "🟢 HEALTHY — NO ISSUES DETECTED";
        } else if (rollbackExecuted) {
            statusBadge.innerText = "SYSTEM RESTORED";
        } else {
            statusBadge.innerText = "ACTIVE ERROR INCIDENT REPORT";
        }
    }

    if (causesContainer) {
        if (analysis.status === "NO_ISSUES" || !analysis.has_error) {
            causesContainer.innerHTML = `
                <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid var(--green-border); padding: 1.5rem; border-radius: 8px; text-align: center; animation: fadeIn 0.4s ease-in-out;">
                    <div style="font-size: 2rem; margin-bottom: 0.3rem;">🟢</div>
                    <h3 style="color: #34d399; margin: 0 0 0.3rem 0; font-size: 1.2rem;">No issues till now</h3>
                    <p style="margin: 0; color: var(--text-muted); font-size: 0.9rem;">
                        All target application endpoints on Port 5000 and proxy response traffic are returning healthy responses (200 OK). Featherless AI actively monitors log stream and will auto-generate incident diagnostics if an HTTP error occurs.
                    </p>
                </div>
            `;
        } else if (analysis.ranked_causes && analysis.ranked_causes.length > 0) {
            let cHtml = "";
            analysis.ranked_causes.forEach(cause => {
                cHtml += `
                    <div class="cause-card">
                        <div class="cause-rank-badge">#${cause.rank}</div>
                        <div class="cause-info">
                            <div class="cause-title-bar">
                                <h3>${escapeHtml(cause.title)}</h3>
                                <div class="cause-prob">${cause.probability}% Likelihood</div>
                            </div>
                            <p style="margin: 0 0 0.5rem 0; color: #cbd5e1; font-size: 0.92rem;">
                                ${escapeHtml(cause.details)}
                            </p>
                            <div>
                                <span class="badge badge-info">${cause.status_badge}</span>
                            </div>
                        </div>
                    </div>
                `;
            });
            causesContainer.innerHTML = cHtml;
        }
    }
}

// 7. Git Commits Risk Table
function updateGitCommitsTable(commits) {
    const tableBody = document.getElementById("gitCommitsTableBody");
    if (!tableBody || !commits) return;

    let html = "";
    commits.forEach(commit => {
        const rowStyle = commit.is_culprit ? 'style="background: rgba(239, 68, 68, 0.08);"' : '';
        const badge = commit.is_culprit ? '<span class="badge badge-critical">PRIMARY CULPRIT (PR #42)</span>' : '<span class="badge badge-info">LOW RISK</span>';
        
        html += `
            <tr ${rowStyle}>
                <td><code>${commit.hash}</code></td>
                <td>${commit.author}</td>
                <td><code>${commit.time}</code></td>
                <td><strong>${escapeHtml(commit.message)}</strong></td>
                <td>${badge}</td>
            </tr>
        `;
    });
    tableBody.innerHTML = html;
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// Automated Rollback Trigger for PR #42
async function triggerRollback() {
    const btn = document.getElementById("rollbackBtn");
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = "⏳ Executing Automated Rollback...";
    }

    try {
        const response = await fetch("/api/rollback", {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        });
        const data = await response.json();
        
        if (data.success) {
            if (btn) {
                btn.innerHTML = "✅ Rollback Completed (PR #42 Reverted)";
                btn.style.background = "linear-gradient(135deg, #10b981, #059669)";
            }

            const aiPanel = document.getElementById("aiPanel");
            if (aiPanel) {
                aiPanel.classList.add("resolved-panel");
            }

            showToast("Automated Rollback Executed! Database lock released. System operating normally.");
            fetchFullDynamicState();
        } else {
            alert("Rollback failed: " + data.message);
            if (btn) btn.disabled = false;
        }
    } catch (e) {
        alert("Network error initiating rollback: " + e);
        if (btn) btn.disabled = false;
    }
}

// AI Chat Widget Functions
function toggleChatWindow() {
    const win = document.getElementById("chatWindow");
    if (win) {
        win.classList.toggle("open");
        if (win.classList.contains("open")) {
            document.getElementById("chatInput").focus();
        }
    }
}

function handleChatKeyPress(event) {
    if (event.key === "Enter") {
        sendChatMessage();
    }
}

async function sendChatMessage() {
    const input = document.getElementById("chatInput");
    const msg = input.value.trim();
    if (!msg) return;

    const chatMessages = document.getElementById("chatMessages");

    const userDiv = document.createElement("div");
    userDiv.className = "chat-msg msg-user";
    userDiv.innerText = msg;
    chatMessages.appendChild(userDiv);
    input.value = "";
    chatMessages.scrollTop = chatMessages.scrollHeight;

    const typingDiv = document.createElement("div");
    typingDiv.className = "chat-msg msg-assistant";
    typingDiv.innerText = "Thinking...";
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        const response = await fetch("/api/ai-chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: msg })
        });
        const data = await response.json();
        
        if (data.success) {
            typingDiv.innerHTML = data.reply.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        } else {
            typingDiv.innerText = "Sorry, I encountered an error processing your query.";
        }
    } catch (e) {
        typingDiv.innerText = "Network error connecting to AI Assistant.";
    }

    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Toast Notification Helper
function showToast(message) {
    let toast = document.createElement("div");
    toast.style.position = "fixed";
    toast.style.bottom = "20px";
    toast.style.left = "50%";
    toast.style.transform = "translateX(-50%)";
    toast.style.background = "linear-gradient(135deg, #10b981, #059669)";
    toast.style.color = "#ffffff";
    toast.style.padding = "1rem 2rem";
    toast.style.borderRadius = "30px";
    toast.style.boxShadow = "0 8px 24px rgba(16, 185, 129, 0.4)";
    toast.style.fontWeight = "700";
    toast.style.fontSize = "0.95rem";
    toast.style.zIndex = "9999";
    toast.innerText = message;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 4000);
}
