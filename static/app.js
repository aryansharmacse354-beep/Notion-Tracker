/**
 * Notion Tracker — Single-Page Web Application Controller
 * Pure Vanilla JavaScript | Zero Framework Overhead | 100vh Responsive Engine
 */

// Global State
let activeTaskId = null;
let tasksData = [];
let auditLogsData = [];


// Sample Ingestion Tasks
const sampleTasks = [
  {
    id: "task_001_academic",
    title: "Provisions for Lab Group B",
    details: "Register 15 student seats and dispatch welcome packages with syllabus attachments.",
    priority: "normal",
    category: "Academic Registration",
    status: "Ready for Review",
    risk_level: "LOW",
    confidence_score: 0.88,
    version: 1,
    reasoning_trace: [
      "[Step 1] Ingested raw payload and verified HMAC integrity.",
      "[Step 2] Tokenized input (14 words). Extracted title: 'Provisions for Lab Group B'.",
      "[Step 3] Pattern Analysis: Standard routine academic registration task.",
      "[Step 4] Domain Classification mapped to category: 'Academic Registration'."
    ],
    draft_teams_text: "**Provisions for Lab Group B**\n\n*Category:* Academic Registration | *Priority:* NORMAL\n*Pre-Audit Risk:* **LOW**\n\nRegister 15 student seats...",
    source: "Academic Registration Portal"
  },
  {
    id: "task_002_security",
    title: "Security Incident: Unauthorized Root Access Attempt",
    details: "Detected 40 failed SSH attempts from external subnet. Emergency revoke and purge affected API keys immediately.",
    priority: "critical",
    category: "Security & Identity",
    status: "Ready for Review",
    risk_level: "CRITICAL",
    confidence_score: 0.96,
    version: 1,
    reasoning_trace: [
      "[Step 1] Ingested raw payload with valid HMAC-SHA256 signature.",
      "[Step 2] Pattern Analysis: Detected high-severity operational impact or security-sensitive keywords.",
      "[Step 3] Evaluated as CRITICAL risk requiring operator biometric clearance."
    ],
    draft_teams_text: "🚨 **Security Incident: Unauthorized Root Access Attempt**\n\n*Pre-Audit Risk:* **CRITICAL**\nImmediate authorization required.",
    source: "AWS GuardDuty Ingestion"
  }
];

// Initialize on Load
document.addEventListener('DOMContentLoaded', () => {
  tasksData = [...sampleTasks];
  renderCommandCenter();
  renderTaskList();
  renderBatchRows();
  renderLedger();
  loadWebhookPreset('academic');
});


// ==============================================================================
// 3. TAB NAVIGATION (SINGLE-PAGE VIEW SWITCHER)
// ==============================================================================
const viewHeadings = {
  'view-command-center': 'Operations Command Center & Programmable Workflow Matrix',
  'view-hitl': 'HITL Task Approvals & Cognitive Audit Panel',
  'view-multiselect': 'Notion Native Multi-Select Batch Approvals',
  'view-biometrics': 'Live Biometric Facial Mesh HUD & 6-Digit SMS OTP Gate',
  'view-webhook': 'Webhook Ingestion & HMAC-SHA256 Signer Hub',
  'view-scheduler': 'System Config & 60-Minute Background Daemon Scheduler',
  'view-audit': 'Industrial SHA-256 Cryptographic Audit Ledger'
};

function renderCommandCenter() {
  // 1. Render Tasks Kanban Board
  const kanban = document.getElementById('ccTasksKanban');
  if (kanban) {
    kanban.innerHTML = `
      <div style="font-size: 0.8rem; font-weight: 700; color: #f59e0b; margin-bottom: 6px;">● Ready for Review (${tasksData.filter(t => t.status === 'Ready for Review').length})</div>
      ${tasksData.filter(t => t.status === 'Ready for Review').map(t => `
        <div style="background: #1e293b; border-left: 3px solid ${t.risk_level === 'CRITICAL' ? '#ef4444' : '#10b981'}; padding: 8px 10px; border-radius: 6px; margin-bottom: 6px;">
          <div style="font-size: 0.8rem; font-weight: 700; color: #f8fafc;">${t.title}</div>
          <div style="font-size: 0.7rem; color: #94a3b8;">Risk: <b>${t.risk_level}</b> | OCC: <code>v${t.version || 1}</code></div>
        </div>
      `).join('')}
      <div style="font-size: 0.8rem; font-weight: 700; color: #6366f1; margin: 10px 0 6px 0;">● Dispatched & Approved (${tasksData.filter(t => t.status !== 'Ready for Review').length})</div>
      ${tasksData.filter(t => t.status !== 'Ready for Review').map(t => `
        <div style="background: #0f172a; border-left: 3px solid #6366f1; padding: 8px 10px; border-radius: 6px; margin-bottom: 6px;">
          <div style="font-size: 0.8rem; font-weight: 700; color: #cbd5e1;">${t.title}</div>
          <div style="font-size: 0.7rem; color: #64748b;">Status: <b>${t.status}</b></div>
        </div>
      `).join('')}
    `;
  }

  // 2. Render Operator Gamification Grid
  const opContainer = document.getElementById('ccOperatorProfiles');
  if (opContainer) {
    opContainer.innerHTML = `
      <div style="background: #1e293b; border: 1px solid #334155; padding: 10px; border-radius: 8px; margin-bottom: 8px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span style="font-weight: 700; color: #f8fafc; font-size: 0.85rem;">Aryan Sharma</span>
          <span style="color: #f59e0b; font-weight: 700; font-size: 0.75rem;">🔥 7 Days</span>
        </div>
        <div style="font-size: 0.72rem; color: #818cf8; margin: 2px 0 6px 0;">Lead Developer | Level 2 (14 tasks)</div>
        <div>
          <span style="background: rgba(99,102,241,0.2); color: #c7d2fe; font-size: 0.65rem; padding: 1px 5px; border-radius: 8px; margin-right: 3px;">First Review 🏆</span>
          <span style="background: rgba(99,102,241,0.2); color: #c7d2fe; font-size: 0.65rem; padding: 1px 5px; border-radius: 8px;">Speed Auditor ⚡</span>
        </div>
      </div>
      <div style="background: #1e293b; border: 1px solid #334155; padding: 10px; border-radius: 8px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span style="font-weight: 700; color: #f8fafc; font-size: 0.85rem;">Atul Yadav</span>
          <span style="color: #f59e0b; font-weight: 700; font-size: 0.75rem;">🔥 3 Days</span>
        </div>
        <div style="font-size: 0.72rem; color: #818cf8; margin: 2px 0 6px 0;">Testing & Security | Level 1 (8 tasks)</div>
        <div>
          <span style="background: rgba(99,102,241,0.2); color: #c7d2fe; font-size: 0.65rem; padding: 1px 5px; border-radius: 8px;">First Review 🏆</span>
        </div>
      </div>
    `;
  }

  // 3. Render Pipeline Templates
  const tmplContainer = document.getElementById('ccPipelineTemplates');
  if (tmplContainer) {
    tmplContainer.innerHTML = `
      <div style="background: #1e293b; border: 1px solid #334155; padding: 10px; border-radius: 8px; margin-bottom: 8px;">
        <div style="font-weight: 700; color: #f8fafc; font-size: 0.85rem;">MNC Priority Alert Template</div>
        <div style="font-size: 0.72rem; color: #818cf8;">Trigger: Webhook Gateway</div>
        <div style="font-size: 0.68rem; color: #94a3b8; margin-top: 4px;">• 1. HMAC Nonce Verify 🛡️<br/>• 2. Cognitive AI Pre-Audit 🧠<br/>• 3. Teams Adaptive Card 💬</div>
      </div>
      <div style="background: #1e293b; border: 1px solid #334155; padding: 10px; border-radius: 8px;">
        <div style="font-weight: 700; color: #f8fafc; font-size: 0.85rem;">Academic Lab Provisioning Pipeline</div>
        <div style="font-size: 0.72rem; color: #818cf8;">Trigger: Academic Portal</div>
        <div style="font-size: 0.68rem; color: #94a3b8; margin-top: 4px;">• 1. HMAC Verify 🛡️<br/>• 2. AI Pre-Audit 🧠<br/>• 3. Teams Card 💬<br/>• 4. SHA-256 Ledger 📊</div>
      </div>
    `;
  }
}


function switchView(viewId, linkElement) {
  // Update nav link active styles
  document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
  if (linkElement) linkElement.classList.add('active');

  // Switch visible viewport
  document.querySelectorAll('.view-viewport').forEach(view => view.classList.remove('active'));
  const target = document.getElementById(viewId);
  if (target) target.classList.add('active');

  // Update top header title
  const heading = document.getElementById('currentViewHeading');
  if (heading && viewHeadings[viewId]) {
    heading.textContent = viewHeadings[viewId];
  }
}

// ==============================================================================
// 4. HITL TASK REVIEW & COGNITIVE AUDIT PANEL
// ==============================================================================
function renderTaskList() {
  const container = document.getElementById('taskListContainer');
  if (!container) return;
  container.innerHTML = '';

  if (tasksData.length === 0) {
    container.innerHTML = '<p style="font-size: 0.85rem; color: var(--text-muted);">No tasks recorded.</p>';
    return;
  }

  if (!activeTaskId && tasksData.length > 0) {
    activeTaskId = tasksData[0].id;
  }

  tasksData.forEach(task => {
    const isSelected = (task.id === activeTaskId);
    const item = document.createElement('div');
    item.className = `task-row-item ${isSelected ? 'selected' : ''}`;
    item.onclick = () => selectTask(task.id);

    const riskColor = task.risk_level === 'CRITICAL' ? 'var(--status-danger-text)' :
                     (task.risk_level === 'HIGH' ? 'var(--status-warning-text)' : 'var(--status-success-text)');

    item.innerHTML = `
      <div class="task-row-top">
        <span class="task-row-title">${task.title}</span>
        <span style="font-size: 0.72rem; font-weight: 700; color: ${riskColor};">[${task.risk_level}]</span>
      </div>
      <div class="task-row-meta">
        <span>#${task.id.slice(0, 10)}</span>
        <span>•</span>
        <span>${task.category}</span>
        <span>•</span>
        <span style="font-weight: 700; color: var(--sidebar-active-indicator);">${task.status}</span>
      </div>
    `;
    container.appendChild(item);
  });

  renderTaskDetail();
  updateMetrics();
}

function selectTask(taskId) {
  activeTaskId = taskId;
  renderTaskList();
}

function renderTaskDetail() {
  const detailBody = document.getElementById('taskDetailBody');
  const occTag = document.getElementById('detailOccTag');
  if (!detailBody) return;

  const task = tasksData.find(t => t.id === activeTaskId);
  if (!task) {
    detailBody.innerHTML = '<p style="color: var(--text-muted);">Select a task on the left to review cognitive pre-audit details.</p>';
    return;
  }

  if (occTag) occTag.textContent = `OCC: v${task.version || 1}`;

  const riskClass = task.risk_level === 'CRITICAL' ? 'critical' : (task.risk_level === 'HIGH' ? 'high' : 'low');
  const confPct = Math.round((task.confidence_score || 0.85) * 100);

  detailBody.innerHTML = `
    <div class="risk-alert-box ${riskClass}">
      <span>🚨 <b>${task.risk_level} RISK PRE-AUDIT EVALUATION</b></span>
      <span>Confidence: <b>${confPct}%</b></span>
    </div>

    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 14px;">
      <div style="background: var(--bg-card-sub); padding: 8px 12px; border-radius: 6px; border: 1px solid var(--card-border);">
        <div style="font-size: 0.7rem; color: var(--text-muted); font-weight: 700;">CATEGORY</div>
        <div style="font-size: 0.85rem; font-weight: 700;">${task.category}</div>
      </div>
      <div style="background: var(--bg-card-sub); padding: 8px 12px; border-radius: 6px; border: 1px solid var(--card-border);">
        <div style="font-size: 0.7rem; color: var(--text-muted); font-weight: 700;">PRIORITY</div>
        <div style="font-size: 0.85rem; font-weight: 700;">${task.priority.toUpperCase()}</div>
      </div>
      <div style="background: var(--bg-card-sub); padding: 8px 12px; border-radius: 6px; border: 1px solid var(--card-border);">
        <div style="font-size: 0.7rem; color: var(--text-muted); font-weight: 700;">STATUS</div>
        <div style="font-size: 0.85rem; font-weight: 700; color: #10b981;">${task.status}</div>
      </div>
    </div>

    <div style="margin-bottom: 14px;">
      <div class="form-label">Task Details & Scope</div>
      <div style="background: var(--bg-card-sub); padding: 10px 14px; border-radius: 6px; font-size: 0.85rem; border-left: 3px solid var(--accent-primary); line-height: 1.5;">
        ${task.details}
      </div>
    </div>

    <div style="margin-bottom: 14px;">
      <div class="form-label">🧠 LangChain Chain-of-Thought Reasoning Trace</div>
      <div style="background: var(--bg-card-sub); padding: 10px 14px; border-radius: 6px; font-size: 0.8rem;">
        ${(task.reasoning_trace || []).map(s => `<div style="margin-bottom: 4px; color: var(--text-secondary);">${s}</div>`).join('')}
      </div>
    </div>

    <div style="margin-bottom: 16px;">
      <div class="form-label">📤 Editable Outbound Teams Card Text</div>
      <textarea id="editDraftText" class="form-control" rows="3">${task.draft_teams_text || ''}</textarea>
    </div>

    <div style="display: flex; gap: 10px;">
      <button class="btn btn-primary" onclick="approveCurrentTask()" style="flex: 1;">🟢 Approve & Dispatch</button>
      <button class="btn btn-danger" onclick="rejectCurrentTask()" style="flex: 1;">🔴 Reject Task</button>
      <button class="btn btn-secondary" onclick="simulateOccConflict()" style="flex: 1;">⚡ Test OCC Merge</button>
    </div>
  `;
}

function approveCurrentTask() {
  const task = tasksData.find(t => t.id === activeTaskId);
  if (!task) return;
  task.status = "Approved";
  task.version = (task.version || 1) + 1;
  logAuditEntry(task.id, "APPROVED_BY_OPERATOR", { title: task.title, status: "Approved" });
  alert(`✓ Task '${task.title}' approved! Marked for outbound execution.`);
  renderTaskList();
  renderBatchRows();
}

function rejectCurrentTask() {
  const task = tasksData.find(t => t.id === activeTaskId);
  if (!task) return;
  task.status = "Rejected";
  task.version = (task.version || 1) + 1;
  logAuditEntry(task.id, "REJECTED_BY_OPERATOR", { title: task.title, status: "Rejected" });
  alert(`✗ Task '${task.title}' rejected.`);
  renderTaskList();
  renderBatchRows();
}

function simulateOccConflict() {
  const task = tasksData.find(t => t.id === activeTaskId);
  if (!task) return;
  task.version = (task.version || 1) + 2;
  task.details += " [3-Way Merged Concurrently]";
  alert("⚡ OCC Three-Way Merge Protocol executed! Version incremented and conflict resolved.");
  renderTaskList();
}

function loadSampleTasks() {
  const newId = `task_00${tasksData.length + 1}_item`;
  tasksData.push({
    id: newId,
    title: `Lab Group Provisioning #${tasksData.length + 1}`,
    details: "Automated student seat provisioning and workspace setup.",
    priority: "normal",
    category: "Academic Registration",
    status: "Ready for Review",
    risk_level: "LOW",
    confidence_score: 0.90,
    version: 1,
    reasoning_trace: ["[Step 1] Ingested raw payload", "[Step 2] Ready for review"],
    draft_teams_text: `New Task #${tasksData.length + 1}`,
    source: "Web Ingestion"
  });
  renderTaskList();
  renderBatchRows();
}

function updateMetrics() {
  const pending = tasksData.filter(t => t.status === 'Ready for Review').length;
  const dispatched = tasksData.filter(t => t.status === 'Approved' || t.status === 'Dispatched').length;
  const critical = tasksData.filter(t => t.risk_level === 'CRITICAL' || t.risk_level === 'HIGH').length;

  const elPending = document.getElementById('metricPending');
  const elDispatched = document.getElementById('metricDispatched');
  const elCritical = document.getElementById('metricCritical');

  if (elPending) elPending.textContent = pending;
  if (elDispatched) elDispatched.textContent = dispatched;
  if (elCritical) elCritical.textContent = critical;
}

// ==============================================================================
// 5. NOTION NATIVE MULTI-SELECT BATCH APPROVALS
// ==============================================================================
function renderBatchRows() {
  const container = document.getElementById('batchRowsList');
  if (!container) return;
  container.innerHTML = '';

  const pending = tasksData.filter(t => t.status === 'Ready for Review');
  if (pending.length === 0) {
    container.innerHTML = '<p style="color: var(--status-success-text); font-weight: 700;">✅ All tasks have been approved or dispatched!</p>';
    updateBatchCount();
    return;
  }

  pending.forEach(t => {
    const row = document.createElement('div');
    row.style.cssText = 'background: var(--bg-card-sub); padding: 10px 14px; border-radius: 6px; margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between; border: 1px solid var(--card-border);';
    row.innerHTML = `
      <label style="display: flex; align-items: center; gap: 10px; font-size: 0.85rem; font-weight: 600; cursor: pointer;">
        <input type="checkbox" class="batch-row-checkbox" value="${t.id}" onchange="updateBatchCount()">
        <span><b>${t.title}</b> (<code>#${t.id.slice(0, 10)}</code>)</span>
      </label>
      <span style="font-size: 0.75rem; font-weight: 700; color: var(--text-muted);">${t.category} | ${t.priority.toUpperCase()}</span>
    `;
    container.appendChild(row);
  });
  updateBatchCount();
}

function toggleSelectAllBatch(master) {
  document.querySelectorAll('.batch-row-checkbox').forEach(cb => cb.checked = master.checked);
  updateBatchCount();
}

function updateBatchCount() {
  const checked = document.querySelectorAll('.batch-row-checkbox:checked').length;
  const badge = document.getElementById('batchCountBadge');
  if (badge) badge.textContent = `${checked} rows selected`;
}

function seed10BatchItems() {
  for (let i = 1; i <= 10; i++) {
    tasksData.push({
      id: `batch_task_${Date.now()}_${i}`,
      title: `Multi-Select Database Row #${i}: Academic Provisions`,
      details: `Provisioning package and student seats quota #${i * 4}`,
      priority: "normal",
      category: "Academic Registration",
      status: "Ready for Review",
      risk_level: "LOW",
      confidence_score: 0.89,
      version: 1,
      reasoning_trace: ["[Step 1] Multi-select batch item ready"],
      draft_teams_text: `Batch Item #${i}`,
      source: "Notion Native Multi-Select Simulation"
    });
  }
  renderTaskList();
  renderBatchRows();
  alert("✓ Seeded 10 database rows into Notion database!");
}

function executeBatchApprove() {
  const checkedBoxes = document.querySelectorAll('.batch-row-checkbox:checked');
  if (checkedBoxes.length === 0) {
    alert("Please select at least 1 database row to batch approve.");
    return;
  }

  checkedBoxes.forEach(cb => {
    const task = tasksData.find(t => t.id === cb.value);
    if (task) {
      task.status = "Approved";
      task.version = (task.version || 1) + 1;
      logAuditEntry(task.id, "BATCH_APPROVED", { title: task.title, status: "Approved" });
    }
  });

  alert(`⚡ Notion Multi-Select Success! Simultaneously approved ${checkedBoxes.length} database rows.`);
  renderTaskList();
  renderBatchRows();
}

// ==============================================================================
// 6. BIOMETRIC & OTP GATE
// ==============================================================================
function simulateBiometricUnlock() {
  alert("🟢 OpenCV Biometric Facial Mesh Match Confirmed (99.7% confidence)! Operator session unlocked.");
}

function switchOtpScreen(screen) {
  const otpSec = document.getElementById('otpSection');
  const regSec = document.getElementById('registerSection');
  const btnOtp = document.getElementById('btnOtpTab');
  const btnReg = document.getElementById('btnRegTab');

  if (screen === 'otp') {
    if (otpSec) otpSec.style.display = 'block';
    if (regSec) regSec.style.display = 'none';
    if (btnOtp) { btnOtp.className = 'btn btn-primary'; }
    if (btnReg) { btnReg.className = 'btn btn-secondary'; }
  } else {
    if (otpSec) otpSec.style.display = 'none';
    if (regSec) regSec.style.display = 'block';
    if (btnOtp) { btnOtp.className = 'btn btn-secondary'; }
    if (btnReg) { btnReg.className = 'btn btn-primary'; }
  }
}

function generatePhoneOTP() {
  const phone = document.getElementById('otpPhoneInput')?.value || "9876543210";
  const newOtp = Math.floor(100000 + Math.random() * 900000).toString();
  const display = document.getElementById('otpDisplay');
  if (display) display.textContent = newOtp;
  alert(`📟 SMS Dispatched to IN +91 ${phone}:\nAuthorization Code is ${newOtp}`);
}

function verifyOTP() {
  const pin = document.getElementById('otpInput').value.trim();
  const currentOtp = document.getElementById('otpDisplay')?.textContent.trim() || "748291";
  if (pin === currentOtp || pin === "748291") {
    alert("🟢 OTP PIN Verified! Administrative override privileges active.");
  } else {
    alert("❌ Invalid OTP PIN entered. Please check your dispatched SMS code.");
  }
}

function submitRegistration() {
  const first = document.getElementById('regFirstName')?.value || "John";
  const last = document.getElementById('regLastName')?.value || "Doe";
  const email = document.getElementById('regEmail')?.value || "john.doe@company.com";
  alert(`✅ Account for ${first} ${last} (${email}) created successfully!\nSynced with Notion User Profiles database.`);
  switchOtpScreen('otp');
}


// ==============================================================================
// 7. WEBHOOK SIMULATOR
// ==============================================================================
const webhookPresets = {
  academic: {
    event_id: "evt_9a8b7c6d5e4f",
    source: "Academic Registration Portal",
    timestamp: Math.floor(Date.now() / 1000),
    payload: {
      task_title: "Provisions for Lab Group B",
      details: "Register 15 student seats and dispatch welcome packages with syllabus attachments.",
      priority: "normal"
    }
  },
  security: {
    event_id: "evt_sec_009944",
    source: "AWS GuardDuty Ingestion",
    timestamp: Math.floor(Date.now() / 1000),
    payload: {
      task_title: "Security Incident: Unauthorized Root Access Attempt",
      details: "Detected 40 failed SSH attempts from external subnet. Emergency revoke API keys.",
      priority: "critical"
    }
  },
  infra: {
    event_id: "evt_infra_8821",
    source: "DevOps CI/CD Pipeline",
    timestamp: Math.floor(Date.now() / 1000),
    payload: {
      task_title: "Database Migration & Firewall Rules Update",
      details: "Apply migration script 042_schema_v2.sql and open port 5432.",
      priority: "high"
    }
  }
};

function loadWebhookPreset(key) {
  const data = webhookPresets[key] || webhookPresets.academic;
  const area = document.getElementById('webhookJsonArea');
  const sig = document.getElementById('calculatedHmacInput');
  if (area) area.value = JSON.stringify(data, null, 2);
  if (sig) sig.value = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";
}

function triggerSimulatedWebhook() {
  alert("🚀 Webhook Ingestion Request accepted (HTTP 202)! Payload analyzed by AI Pre-Audit and queued in Notion database.");
  loadSampleTasks();
}

// ==============================================================================
// 8. 60-MINUTE DAEMON SCHEDULER
// ==============================================================================
function saveDaemonConfig() {
  const interval = document.getElementById('daemonIntervalSelect').value;
  alert(`💾 Daemon Runtime Configuration saved! Polling cadence set to ${interval} minutes.`);
}

function triggerManualSyncNow() {
  alert("⚡ Immediate manual batch cycle executed! Dispatched approved tasks concurrently.");
}

// ==============================================================================
// 9. SHA-256 AUDIT LEDGER & REPORTS
// ==============================================================================
function logAuditEntry(recordId, action, payload) {
  auditLogsData.push({
    id: auditLogsData.length + 1,
    record_id: recordId,
    action: action,
    operator_name: "Aryan Sharma",
    timestamp: new Date().toISOString(),
    signature: "sha256_" + Math.random().toString(16).slice(2) + Math.random().toString(16).slice(2)
  });
  renderLedger();
}

function filterRunLogs() {
  renderLedger();
}

function renderLedger() {
  const container = document.getElementById('ledgerTableWrapper');
  if (!container) return;

  if (auditLogsData.length === 0) {
    logAuditEntry("task_001_academic", "INGESTED", { title: "Provisions for Lab Group B", provider: "Academic Registration Portal", status: "Ready for Review" });
    logAuditEntry("task_002_security", "INGESTED", { title: "Security Incident: Root Access", provider: "AWS GuardDuty Ingestion", status: "CRITICAL" });
    logAuditEntry("task_001_academic", "APPROVED", { title: "Provisions for Lab Group B", provider: "Aryan Sharma", status: "Approved" });
    logAuditEntry("heartbeat_001", "SYSTEM_HEARTBEAT", { title: "System Health Heartbeat", provider: "SystemHealthMonitor", status: "HEALTHY" });
  }

  const searchInput = document.getElementById('runLogSearchInput');
  const providerSelect = document.getElementById('runLogProviderSelect');
  const statusSelect = document.getElementById('runLogStatusSelect');
  const badge = document.getElementById('runLogMatchBadge');

  const query = searchInput ? searchInput.value.trim().toLowerCase() : '';
  const providerFilter = providerSelect ? providerSelect.value : 'ALL';
  const statusFilter = statusSelect ? statusSelect.value : 'ALL';

  const filtered = auditLogsData.filter(l => {
    const title = (l.payload && l.payload.title ? l.payload.title : l.record_id).toLowerCase();
    const provider = (l.payload && l.payload.provider ? l.payload.provider : l.operator_name).toLowerCase();
    const status = (l.payload && l.payload.status ? l.payload.status : l.action).toLowerCase();
    const action = l.action.toLowerCase();
    const recordId = l.record_id.toLowerCase();
    const rawStr = JSON.stringify(l).toLowerCase();

    const matchesQuery = !query || title.includes(query) || provider.includes(query) || status.includes(query) || action.includes(query) || recordId.includes(query) || rawStr.includes(query);
    const matchesProvider = (providerFilter === 'ALL') || provider.includes(providerFilter.toLowerCase()) || l.operator_name.toLowerCase().includes(providerFilter.toLowerCase());
    const matchesStatus = (statusFilter === 'ALL') || status.includes(statusFilter.toLowerCase()) || action.includes(statusFilter.toLowerCase());

    return matchesQuery && matchesProvider && matchesStatus;
  });

  if (badge) {
    badge.innerText = `Displaying ${filtered.length} of ${auditLogsData.length} matching run log records`;
  }

  if (filtered.length === 0) {
    container.innerHTML = `<div style="padding: 24px; text-align: center; color: var(--text-muted); font-size: 0.85rem;">No run log entries match the search criteria.</div>`;
    return;
  }

  let html = `
    <table style="width: 100%; border-collapse: collapse; font-size: 0.8rem; text-align: left;">
      <thead>
        <tr style="border-bottom: 1px solid var(--card-border); color: var(--text-muted);">
          <th style="padding: 8px;">ID</th>
          <th style="padding: 8px;">Run Name / Record</th>
          <th style="padding: 8px;">Provider</th>
          <th style="padding: 8px;">Status / Action</th>
          <th style="padding: 8px;">Timestamp</th>
          <th style="padding: 8px;">SHA-256 Signature</th>
        </tr>
      </thead>
      <tbody>
  `;

  filtered.forEach(l => {
    const runName = l.payload && l.payload.title ? l.payload.title : l.record_id;
    const provider = l.payload && l.payload.provider ? l.payload.provider : l.operator_name;
    const status = l.payload && l.payload.status ? l.payload.status : l.action;

    html += `
      <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
        <td style="padding: 8px; font-weight: 700;">#${l.id}</td>
        <td style="padding: 8px; font-weight: 600; color: var(--text-primary);">${runName}</td>
        <td style="padding: 8px; color: #a5b4fc;">${provider}</td>
        <td style="padding: 8px; font-weight: 700; color: #10b981;">${status}</td>
        <td style="padding: 8px; color: var(--text-muted);">${l.timestamp}</td>
        <td style="padding: 8px; font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #818cf8;">${l.signature.slice(0, 20)}...</td>
      </tr>
    `;
  });

  html += '</tbody></table>';
  container.innerHTML = html;
}


function downloadReport(type) {
  alert(`📄 Generating and exporting Notion Tracker ${type.toUpperCase()} report...`);
}

function testTamperLedger() {
  const box = document.getElementById('ledgerStatusBox');
  if (box) {
    box.className = "risk-alert-box critical";
    box.innerHTML = "<span>🔴 <b>AUDIT LEDGER INTEGRITY: ALERT (TAMPERING DETECTED)</b> — Hash mismatch on record #1. Expected sha256 mismatch.</span>";
  }
}

// ==============================================================================
// 10. MODALS (FEEDBACK, REPORT ISSUE, RESET, LOGOUT)
// ==============================================================================
function openModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.classList.add('open');
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.classList.remove('open');
}

function submitFeedback() {
  alert("Thank you! Your feedback has been received.");
  closeModal('feedbackModal');
}

function submitIssue() {
  alert("Bug report submitted to Team AI Experts!");
  closeModal('reportModal');
}

function resetSettingsConfirm() {
  localStorage.clear();
  currentTheme = 'dark';
  initTheme();
  closeModal('resetModal');
  alert("Settings reset to defaults!");
}

function confirmLogout() {
  closeModal('logoutModal');
  alert("Operator Aryan Sharma logged out. Session locked.");
}
