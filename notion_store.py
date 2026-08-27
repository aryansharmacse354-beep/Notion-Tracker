"""Notion Unified Store and Resilient Datastore.

Provides a unified interface for Notion API operations with local SQLite fallback.
Manages Tasks Database, Run Log Database, and RBAC User Profiles with thread-safe OCC.
"""

from typing import Dict, Any, List, Optional, Tuple
from contextlib import contextmanager
import sqlite3
import json
import time
import uuid
import logging


try:
    import requests
except ImportError:
    requests = None

from config import (
    NOTION_TOKEN,
    NOTION_TASKS_DB_ID,
    NOTION_LOGS_DB_ID,
    NOTION_USERS_DB_ID,
    STORAGE_MODE,
    DB_FILE,
    CONFIG_FILE,
    POLL_INTERVAL_MINUTES,
    POLL_INTERVAL_SECONDS,
)

from notion_enterprise_guard import (
    default_rate_limiter,
    OptimisticConcurrencyControl,
    WorkspaceSelfHealing,
)
from audit_ledger import AuditLedger
from notion_typesetter import NotionTypesetter

logger = logging.getLogger("notion_tracker.store")



class NotionStore:
    """Unified datastore managing tasks, audit logs, and operator profiles."""

    def __init__(self, db_path: str = str(DB_FILE)):
        self.db_path = db_path
        self.self_healing = WorkspaceSelfHealing()
        self._init_db()
        self._seed_default_users()

    @contextmanager
    def _get_connection(self):
        """Yields a thread-safe sqlite3 connection and guarantees commit and close upon exit."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self) -> None:

        """Initializes database tables if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 1. Tasks Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    details TEXT,
                    priority TEXT DEFAULT 'normal',
                    category TEXT DEFAULT 'General',
                    status TEXT DEFAULT 'Ready for Review',
                    risk_level TEXT DEFAULT 'LOW',
                    confidence_score REAL DEFAULT 0.85,
                    reasoning_trace TEXT,
                    draft_summary TEXT,
                    draft_email_html TEXT,
                    draft_teams_text TEXT,
                    source TEXT DEFAULT 'Webhook',
                    version INTEGER DEFAULT 1,
                    nonce TEXT,
                    budget TEXT DEFAULT '$0',
                    ai_reasoning_ledger TEXT,
                    proposed_ai_draft TEXT,
                    edited_draft TEXT,
                    ingestion_fingerprint TEXT,
                    dlq_error_trace TEXT,
                    dlq_reason TEXT,
                    audio_file TEXT,
                    comment_thread TEXT,
                    created_at REAL,
                    updated_at REAL,
                    archived INTEGER DEFAULT 0
                )
            """)

            # Ensure newly added columns exist for existing tables
            for col, col_type in [
                ("budget", "TEXT DEFAULT '$0'"),
                ("ai_reasoning_ledger", "TEXT"),
                ("proposed_ai_draft", "TEXT"),
                ("edited_draft", "TEXT"),
                ("ingestion_fingerprint", "TEXT"),
                ("dlq_error_trace", "TEXT"),
                ("dlq_reason", "TEXT"),
                ("audio_file", "TEXT"),
                ("comment_thread", "TEXT"),
            ]:
                try:
                    cursor.execute(f"ALTER TABLE tasks ADD COLUMN {col} {col_type}")
                except Exception:
                    pass

            # Ingestion Fingerprints Table (Deduplication Authority)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ingestion_fingerprints (
                    fingerprint TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    payload_summary TEXT
                )
            """)

            # 2. Run Log Table

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_id TEXT,
                    action TEXT NOT NULL,
                    operator_name TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    payload_data TEXT,
                    signature TEXT NOT NULL,
                    prev_signature TEXT NOT NULL
                )
            """)

            # 3. RBAC User Profiles Table (with Gamification, Streaks & Badges)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    role TEXT NOT NULL,
                    permissions TEXT NOT NULL,
                    biometric_id TEXT,
                    avatar_url TEXT,
                    tasks_completed INTEGER DEFAULT 0,
                    current_streak INTEGER DEFAULT 1,
                    unlocked_badges TEXT DEFAULT '[]',
                    last_active_date TEXT
                )
            """)

            # Ensure gamification columns exist for existing tables
            for col, col_type in [
                ("tasks_completed", "INTEGER DEFAULT 0"),
                ("current_streak", "INTEGER DEFAULT 1"),
                ("unlocked_badges", "TEXT DEFAULT '[]'"),
                ("last_active_date", "TEXT"),
            ]:
                try:
                    cursor.execute(f"ALTER TABLE user_profiles ADD COLUMN {col} {col_type}")
                except Exception:
                    pass

            # 4. Notion System Health & Turn-Off Test Heartbeat Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_health (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    cpu_percent REAL NOT NULL,
                    ram_percent REAL NOT NULL,
                    disk_percent REAL NOT NULL,
                    active_threads INTEGER NOT NULL,
                    available_tokens REAL NOT NULL,
                    uptime_seconds INTEGER NOT NULL,
                    timestamp REAL NOT NULL,
                    signature TEXT
                )
            """)

            # 5. Visual Workflow Builder: Pipeline Templates Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pipeline_templates (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    trigger_source TEXT NOT NULL,
                    steps TEXT NOT NULL,
                    risk_threshold TEXT DEFAULT 'Strict HITL (All Risks)',
                    status TEXT DEFAULT 'Active 🟢',
                    version INTEGER DEFAULT 1,
                    created_at REAL,
                    updated_at REAL
                )
            """)
            conn.commit()


    def _seed_default_users(self) -> None:
        """Seeds default operator profiles and visual workflow templates."""
        default_users = [
            {
                "id": "usr_aryan_01",
                "name": "Aryan Sharma",
                "role": "Lead Developer & Architect",
                "permissions": json.dumps(["admin", "approve", "reject", "dispatch", "config", "biometric_auth"]),
                "biometric_id": "BIO_ARYAN_SHARMA",
                "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=Aryan",
                "tasks_completed": 14,
                "current_streak": 7,
                "unlocked_badges": json.dumps(["First Review 🏆", "Speed Auditor ⚡", "7-Day Streak 🔥"]),
                "last_active_date": "2026-08-24",
            },
            {
                "id": "usr_atul_02",
                "name": "Atul Yadav",
                "role": "Code Quality Testing & Security",
                "permissions": json.dumps(["audit", "approve", "reject", "test", "view", "biometric_auth"]),
                "biometric_id": "BIO_ATUL_YADAV",
                "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=Atul",
                "tasks_completed": 8,
                "current_streak": 3,
                "unlocked_badges": json.dumps(["First Review 🏆", "Speed Auditor ⚡"]),
                "last_active_date": "2026-08-24",
            },
            {
                "id": "usr_daemon_00",
                "name": "Automation Daemon",
                "role": "System Ingestion & Dispatcher",
                "permissions": json.dumps(["ingest", "pre_audit", "dispatch", "system"]),
                "biometric_id": "SYSTEM",
                "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=Daemon",
                "tasks_completed": 45,
                "current_streak": 30,
                "unlocked_badges": json.dumps(["First Review 🏆", "Speed Auditor ⚡", "7-Day Streak 🔥", "Zero-Error Champion 🛡️"]),
                "last_active_date": "2026-08-24",
            },
        ]

        seed_templates = [
            (
                "tmpl_mnc_alert",
                "MNC Priority Alert Template",
                "Webhook Gateway",
                json.dumps([
                    "1. HMAC Nonce Verify 🛡️",
                    "2. Cognitive AI Pre-Audit 🧠",
                    "3. Biometric & OTP Gate 🔐",
                    "4. Teams Adaptive Card 💬",
                    "5. SendGrid Email 📧",
                    "6. SHA-256 Signature Seal 📊",
                ]),
                "Strict HITL (All Risks)",
                "Active 🟢",
                1,
                time.time(),
                time.time(),
            ),
            (
                "tmpl_academic_lab",
                "Academic Lab Provisioning Pipeline",
                "Academic Portal",
                json.dumps([
                    "1. HMAC Nonce Verify 🛡️",
                    "2. Cognitive AI Pre-Audit 🧠",
                    "4. Teams Adaptive Card 💬",
                    "6. SHA-256 Signature Seal 📊",
                ]),
                "Auto-Approve LOW",
                "Active 🟢",
                1,
                time.time(),
                time.time(),
            ),
            (
                "tmpl_sec_incident",
                "Emergency Security Escalation Pipeline",
                "AWS GuardDuty Security",
                json.dumps([
                    "1. HMAC Nonce Verify 🛡️",
                    "2. Cognitive AI Pre-Audit 🧠",
                    "3. Biometric & OTP Gate 🔐",
                    "4. Teams Adaptive Card 💬",
                    "5. SendGrid Email 📧",
                    "6. SHA-256 Signature Seal 📊",
                ]),
                "CRITICAL / HIGH Gate Only",
                "Active 🟢",
                1,
                time.time(),
                time.time(),
            ),
        ]

        with self._get_connection() as conn:
            cursor = conn.cursor()
            for u in default_users:
                cursor.execute("""
                    INSERT OR IGNORE INTO user_profiles (
                        id, name, role, permissions, biometric_id, avatar_url,
                        tasks_completed, current_streak, unlocked_badges, last_active_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    u["id"], u["name"], u["role"], u["permissions"], u["biometric_id"], u["avatar_url"],
                    u["tasks_completed"], u["current_streak"], u["unlocked_badges"], u["last_active_date"]
                ))
            for tmpl in seed_templates:
                cursor.execute("""
                    INSERT OR IGNORE INTO pipeline_templates (
                        id, name, trigger_source, steps, risk_threshold, status, version, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, tmpl)
            conn.commit()



    # --- Task Methods ---

    def create_task(self, task_dict: Dict[str, Any], operator_name: str = "Webhook Ingestion") -> Dict[str, Any]:
        """Creates a new task with initial OCC version and logs the signed audit entry."""
        default_rate_limiter.acquire(1.0)

        task_id = task_dict.get("id") or f"task_{uuid.uuid4().hex[:12]}"
        now = time.time()
        nonce = OptimisticConcurrencyControl.generate_nonce()

        reasoning = json.dumps(task_dict.get("reasoning_trace", []))
        record = {
            "id": task_id,
            "title": task_dict.get("title", "Untitled Task"),
            "details": task_dict.get("details", ""),
            "priority": task_dict.get("priority", "normal"),
            "category": task_dict.get("category", "General"),
            "status": task_dict.get("status", "Ready for Review"),
            "risk_level": task_dict.get("risk_level", "LOW"),
            "confidence_score": float(task_dict.get("confidence_score", 0.85)),
            "reasoning_trace": reasoning,
            "draft_summary": task_dict.get("draft_summary", ""),
            "draft_email_html": task_dict.get("draft_email_html", ""),
            "draft_teams_text": task_dict.get("draft_teams_text", ""),
            "proposed_ai_draft": task_dict.get("proposed_ai_draft", task_dict.get("draft_teams_text", "")),
            "edited_draft": task_dict.get("edited_draft", None),
            "ai_reasoning_ledger": task_dict.get("ai_reasoning_ledger", ""),
            "ingestion_fingerprint": task_dict.get("ingestion_fingerprint", None),
            "dlq_error_trace": task_dict.get("dlq_error_trace", None),
            "dlq_reason": task_dict.get("dlq_reason", None),
            "audio_file": task_dict.get("audio_file", None),
            "comment_thread": task_dict.get("comment_thread", None),
            "source": task_dict.get("source", "Webhook"),
            "version": task_dict.get("version", 1),
            "nonce": task_dict.get("nonce", nonce),
            "budget": task_dict.get("budget", "$0"),
            "created_at": now,
            "updated_at": now,
            "archived": 0,
        }

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tasks (id, title, details, priority, category, status, risk_level,
                                   confidence_score, reasoning_trace, draft_summary, draft_email_html,
                                   draft_teams_text, proposed_ai_draft, edited_draft, ai_reasoning_ledger,
                                   ingestion_fingerprint, dlq_error_trace, dlq_reason, audio_file,
                                   comment_thread, source, version, nonce, budget, created_at, updated_at, archived)
                VALUES (:id, :title, :details, :priority, :category, :status, :risk_level,
                        :confidence_score, :reasoning_trace, :draft_summary, :draft_email_html,
                        :draft_teams_text, :proposed_ai_draft, :edited_draft, :ai_reasoning_ledger,
                        :ingestion_fingerprint, :dlq_error_trace, :dlq_reason, :audio_file,
                        :comment_thread, :source, :version, :nonce, :budget, :created_at, :updated_at, :archived)
            """, record)
            conn.commit()

        # Self-healing snapshot
        self.self_healing.snapshot(task_id, record)

        # Append signed audit log
        self.append_audit_log(
            record_id=task_id,
            action="INGESTED",
            operator_name=operator_name,
            payload_data={"title": record["title"], "risk_level": record["risk_level"], "status": record["status"]},
        )

        return self.get_task(task_id)

    def update_staged_draft(self, task_id: str, edited_draft: str, operator_name: str = "Operator") -> Optional[Dict[str, Any]]:
        """Stage 3 HITL: Updates the human-edited draft wording before final dispatch.

        Args:
            task_id: Identifier of the task.
            edited_draft: The modified wording created by the human operator.
            operator_name: Name of the operator authoring the revision.

        Returns:
            The updated task dictionary.
        """
        default_rate_limiter.acquire(1.0)
        now = time.time()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tasks
                SET edited_draft = ?, updated_at = ?, version = version + 1
                WHERE id = ?
            """, (edited_draft, now, task_id))
            conn.commit()

        self.append_audit_log(
            record_id=task_id,
            action="DRAFT_STAGED_BY_HUMAN",
            operator_name=operator_name,
            payload_data={"edited_length": len(edited_draft)},
        )
        return self.get_task(task_id)

    def route_to_dlq(
        self,
        task_id: str,
        error_trace: str,
        reason: str = "Processing Exception",
        operator_name: str = "System Guard",
    ) -> Optional[Dict[str, Any]]:
        """Stage 5 DLQ: Isolates a failed/corrupt task into DLQ: Needs Technical Review.

        Updates status, stores error traceback, appends non-repudiation audit log,
        and programmatically typesets a red warning callout block inside the Notion page body.

        Args:
            task_id: Identifier of the corrupt/failed task.
            error_trace: Full formatted traceback or parser error text.
            reason: Short human-readable summary of the root failure cause.
            operator_name: Reporting entity.

        Returns:
            The quarantined task dictionary.
        """
        now = time.time()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tasks
                SET status = 'DLQ: Needs Technical Review',
                    dlq_error_trace = ?,
                    dlq_reason = ?,
                    updated_at = ?,
                    version = version + 1
                WHERE id = ?
            """, (error_trace, reason, now, task_id))
            conn.commit()

        task = self.get_task(task_id) or {"id": task_id, "title": task_id}

        self.append_audit_log(
            record_id=task_id,
            action="ROUTED_TO_DLQ",
            operator_name=operator_name,
            payload_data={"reason": reason, "status": "DLQ: Needs Technical Review", "error_summary": str(reason)[:200]},
        )

        # Stage 5 Typesetting: If Notion API is active, append red warning callout + traceback code blocks
        if STORAGE_MODE in ("live", "hybrid") and NOTION_TOKEN and requests:
            try:
                default_rate_limiter.acquire(1.0)
                dlq_blocks = NotionTypesetter.build_dlq_diagnostic_blocks(
                    task_data=task,
                    error_trace=error_trace,
                    reason=reason,
                )
                url = f"https://api.notion.com/v1/blocks/{task_id}/children"
                headers = {
                    "Authorization": f"Bearer {NOTION_TOKEN}",
                    "Notion-Version": "2022-06-28",
                    "Content-Type": "application/json",
                }
                requests.patch(url, headers=headers, json={"children": dlq_blocks}, timeout=5.0)
                # Update page property to DLQ
                page_url = f"https://api.notion.com/v1/pages/{task_id}"
                requests.patch(page_url, headers=headers, json={"properties": {"Status": {"select": {"name": "DLQ: Needs Technical Review"}}}}, timeout=5.0)
            except Exception as e:
                logger.warning(f"Could not push DLQ blocks to Notion API for task {task_id}: {e}")

        return self.get_task(task_id)

    def get_dlq_tasks(self) -> List[Dict[str, Any]]:
        """Retrieves all tasks quarantined in the Dead-Letter Queue."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM tasks
                WHERE status IN ('DLQ: Needs Technical Review', 'DLQ: Technical Review')
                ORDER BY updated_at DESC
            """)
            rows = cursor.fetchall()
            tasks = []
            for row in rows:
                t = dict(row)
                try:
                    t["reasoning_trace"] = json.loads(t["reasoning_trace"]) if t.get("reasoning_trace") else []
                except Exception:
                    t["reasoning_trace"] = []
                tasks.append(t)
            return tasks

    def check_and_record_fingerprint(
        self,
        fingerprint: str,
        task_id: str,
        payload_summary: str = "",
        window_seconds: int = 3600,
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Stage 1 Ingestion: Validates and persists an ingestion fingerprint to block duplicates within 1-hour window."""
        now = time.time()
        cutoff = now - window_seconds
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Check existing fingerprint in database
            cursor.execute("""
                SELECT task_id, created_at FROM ingestion_fingerprints
                WHERE fingerprint = ?
            """, (fingerprint,))
            row = cursor.fetchone()
            if row:
                existing_task_id = row["task_id"]
                created_at = row["created_at"]
                if created_at >= cutoff:
                    age = int(now - created_at)
                    msg = f"Duplicate submission rejected. Fingerprint matched Task '{existing_task_id}' ({age}s ago)."
                    return False, existing_task_id, msg

            # Insert or replace fresh fingerprint
            cursor.execute("""
                INSERT OR REPLACE INTO ingestion_fingerprints (fingerprint, task_id, created_at, payload_summary)
                VALUES (?, ?, ?, ?)
            """, (fingerprint, task_id, now, payload_summary))
            conn.commit()
            return True, None, None


    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single task by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            if not row:
                return None
            data = dict(row)
            try:
                data["reasoning_trace"] = json.loads(data["reasoning_trace"]) if data.get("reasoning_trace") else []
            except Exception:
                data["reasoning_trace"] = [str(data.get("reasoning_trace"))]
            return data

    def list_tasks(self, include_archived: bool = False) -> List[Dict[str, Any]]:
        """Lists all tasks ordered by creation time descending."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if include_archived:
                cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC")
            else:
                cursor.execute("SELECT * FROM tasks WHERE archived = 0 ORDER BY created_at DESC")
            rows = cursor.fetchall()
            tasks = []
            for row in rows:
                t = dict(row)
                try:
                    t["reasoning_trace"] = json.loads(t["reasoning_trace"]) if t.get("reasoning_trace") else []
                except Exception:
                    t["reasoning_trace"] = []
                tasks.append(t)
            return tasks

    def update_task_with_occ(
        self,
        task_id: str,
        base_record: Dict[str, Any],
        local_updates: Dict[str, Any],
        operator_name: str,
    ) -> Tuple[Dict[str, Any], bool, List[str]]:
        """Updates a task enforcing Optimistic Concurrency Control with Three-Way Merge if needed.

        Args:
            task_id: ID of the task to update.
            base_record: State of task when operator/worker began editing.
            local_updates: Desired field modifications.
            operator_name: Name of the operator authorizing the update.

        Returns:
            Tuple of (updated_task, had_conflict, conflict_details).
        """
        default_rate_limiter.acquire(1.0)
        current = self.get_task(task_id)
        if not current:
            raise ValueError(f"Task '{task_id}' not found.")

        # Check if OCC conflict exists (remote version != base version)
        base_version = base_record.get("version", 1)
        remote_version = current.get("version", 1)

        had_conflict = False
        conflict_details: List[str] = []

        local_record = copy = dict(base_record)
        local_record.update(local_updates)

        if base_version != remote_version:
            # Conflict detected! Run 3-Way Merge Resolution
            logger.warning(f"OCC conflict detected on task {task_id}: base v{base_version} vs remote v{remote_version}")
            merged_record, had_conflict, conflict_details = OptimisticConcurrencyControl.resolve_three_way_merge(
                base_record=base_record,
                local_record=local_record,
                remote_record=current,
            )
            final_data = merged_record
        else:
            final_data = local_record
            final_data["version"] = remote_version + 1
            final_data["nonce"] = OptimisticConcurrencyControl.generate_nonce()
            final_data["updated_at"] = time.time()

        # Update in database
        reasoning_str = json.dumps(final_data.get("reasoning_trace", []))
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tasks
                SET title = ?, details = ?, priority = ?, category = ?, status = ?,
                    risk_level = ?, confidence_score = ?, reasoning_trace = ?,
                    draft_summary = ?, draft_email_html = ?, draft_teams_text = ?,
                    proposed_ai_draft = ?, edited_draft = ?, ai_reasoning_ledger = ?,
                    ingestion_fingerprint = ?, dlq_error_trace = ?, dlq_reason = ?,
                    audio_file = ?, comment_thread = ?, source = ?, version = ?,
                    nonce = ?, budget = ?, updated_at = ?, archived = ?
                WHERE id = ?
            """, (
                final_data.get("title"),
                final_data.get("details"),
                final_data.get("priority"),
                final_data.get("category"),
                final_data.get("status"),
                final_data.get("risk_level"),
                float(final_data.get("confidence_score", 0.85)),
                reasoning_str,
                final_data.get("draft_summary"),
                final_data.get("draft_email_html"),
                final_data.get("draft_teams_text"),
                final_data.get("proposed_ai_draft"),
                final_data.get("edited_draft"),
                final_data.get("ai_reasoning_ledger", ""),
                final_data.get("ingestion_fingerprint"),
                final_data.get("dlq_error_trace"),
                final_data.get("dlq_reason"),
                final_data.get("audio_file"),
                final_data.get("comment_thread"),
                final_data.get("source"),
                final_data.get("version"),
                final_data.get("nonce"),
                final_data.get("budget", "$0"),
                final_data.get("updated_at"),
                int(final_data.get("archived", 0)),
                task_id,
            ))
            conn.commit()

        # Update self-healing snapshot
        self.self_healing.snapshot(task_id, final_data)

        # Log to tamper-proof audit ledger
        action_name = f"UPDATED_{final_data.get('status', 'MODIFIED').upper()}"
        self.append_audit_log(
            record_id=task_id,
            action=action_name,
            operator_name=operator_name,
            payload_data={
                "title": final_data.get("title"),
                "status": final_data.get("status"),
                "version": final_data.get("version"),
                "had_conflict": had_conflict,
            },
        )

        return self.get_task(task_id), had_conflict, conflict_details

    # --- Audit Log Methods ---

    def write_to_run_log(
        self,
        record_id: str,
        action: str,
        operator_name: str,
        task_data: Optional[Dict[str, Any]] = None,
        reasoning_steps: Optional[List[str]] = None,
        raw_payload: Optional[Dict[str, Any]] = None,
        lang: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Programmatically generates native Notion Toggle blocks and writes a Run Log record.

        Generates:
        - Toggle 1: 🔍 View Step-by-Step AI Reasoning Steps (bulleted list of CoT steps)
        - Toggle 2: 📄 View Raw JSON Ingestion Payload (formatted code block with language 'json')

        Appends a cryptographically signed non-repudiation audit record.
        """
        task = task_data or self.get_task(record_id) or {}
        steps = reasoning_steps or task.get("reasoning_trace", [])
        if not steps:
            steps = [
                f"[Step 1] Ingested task '{task.get('title', record_id)}' into Notion Tracker.",
                f"[Step 2] Cognitive AI risk pre-audit evaluated as {task.get('risk_level', 'LOW')}.",
                f"[Step 3] Execution authorization confirmed by {operator_name} and dispatched.",
            ]

        payload = raw_payload or {
            "id": task.get("id", record_id),
            "title": task.get("title", ""),
            "details": task.get("details", ""),
            "priority": task.get("priority", "normal"),
            "category": task.get("category", "General"),
            "status": task.get("status", "Dispatched"),
            "source": task.get("source", "Notion Ingest"),
        }

        # Build Notion native Toggle Blocks in the active workspace language
        notion_blocks = NotionTypesetter.build_run_log_page_blocks(
            reasoning_steps=steps,
            raw_payload=payload,
            action=action,
            operator_name=operator_name,
            lang=lang,
        )


        payload_record = {
            "title": task.get("title", record_id),
            "status": task.get("status", "Dispatched"),
            "risk_level": task.get("risk_level", "LOW"),
            "reasoning_steps": steps,
            "raw_payload": payload,
            "notion_blocks": notion_blocks,
        }

        # Append to SHA-256 digital signature ledger
        log_entry = self.append_audit_log(
            record_id=record_id,
            action=action,
            operator_name=operator_name,
            payload_data=payload_record,
        )

        # If live Notion API is active, push blocks to Notion
        if STORAGE_MODE in ("live", "hybrid") and NOTION_TOKEN and requests:
            try:
                # Append blocks to Notion Page
                default_rate_limiter.acquire(1.0)
                url = f"https://api.notion.com/v1/blocks/{record_id}/children"
                headers = {
                    "Authorization": f"Bearer {NOTION_TOKEN}",
                    "Notion-Version": "2022-06-28",
                    "Content-Type": "application/json",
                }
                requests.patch(url, headers=headers, json={"children": notion_blocks}, timeout=5.0)
            except Exception as e:
                logger.warning(f"Could not push native blocks to Notion API: {e}")

        return log_entry

    def append_audit_log(
        self,
        record_id: str,
        action: str,
        operator_name: str,
        payload_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Appends a new cryptographically signed entry to the audit log chain."""

        now = time.time()
        payload_json = json.dumps(payload_data, sort_keys=True)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT signature FROM audit_logs ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            last_sig = row["signature"] if row else AuditLedger.GENESIS_HASH

            sig = AuditLedger.compute_record_signature(
                record_id=record_id,
                action=action,
                operator_name=operator_name,
                timestamp=now,
                payload_data=payload_data,
                prev_signature=last_sig,
            )

            cursor.execute("""
                INSERT INTO audit_logs (record_id, action, operator_name, timestamp, payload_data, signature, prev_signature)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (record_id, action, operator_name, now, payload_json, sig, last_sig))
            log_id = cursor.lastrowid


        return {
            "id": log_id,
            "record_id": record_id,
            "action": action,
            "operator_name": operator_name,
            "timestamp": now,
            "payload_data": payload_data,
            "signature": sig,
            "prev_signature": last_sig,
        }

    def get_latest_signature(self) -> str:
        """Retrieves the signature of the most recent log record."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT signature FROM audit_logs ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            return row["signature"] if row else AuditLedger.GENESIS_HASH

    def list_audit_logs(self) -> List[Dict[str, Any]]:
        """Returns all audit logs in chronological order."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM audit_logs ORDER BY id ASC")
            rows = cursor.fetchall()
            logs = []
            for r in rows:
                entry = dict(r)
                try:
                    entry["payload_data"] = json.loads(entry["payload_data"])
                except Exception:
                    pass
                logs.append(entry)
            return logs

    # --- RBAC User Profiles & Gamification ---

    def _enrich_user_gamification(self, u: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates derived Notion formulas (streak flame, level badge, progress wheel)."""
        u["permissions"] = json.loads(u["permissions"]) if isinstance(u.get("permissions"), str) else (u.get("permissions") or [])
        u["unlocked_badges"] = json.loads(u["unlocked_badges"]) if isinstance(u.get("unlocked_badges"), str) else (u.get("unlocked_badges") or [])
        tasks_done = u.get("tasks_completed", 0) or 0
        streak = u.get("current_streak", 0) or 0
        
        # Notion-Native Formulas
        u["streak_flame"] = f"🔥 {streak} Days" if streak > 0 else "💤 Inactive"
        u["level_badge"] = f"Level {tasks_done // 10 + 1}"
        u["progress_percent"] = min(100, max(0, (tasks_done % 10) * 10))
        return u

    def list_user_profiles(self) -> List[Dict[str, Any]]:
        """Returns list of registered operator user profiles with gamification formulas."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_profiles")
            rows = cursor.fetchall()
            users = []
            for r in rows:
                users.append(self._enrich_user_gamification(dict(r)))
            return users

    def get_user_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Finds user by name with gamification stats and badges."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_profiles WHERE name = ?", (name,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._enrich_user_gamification(dict(row))

    def record_operator_approval(self, operator_name: str) -> Dict[str, Any]:
        """Increments operator's Tasks Completed and Current Streak, evaluating badge unlocks."""
        user = self.get_user_by_name(operator_name)
        if not user:
            user_id = f"usr_{uuid.uuid4().hex[:8]}"
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO user_profiles (id, name, role, permissions, biometric_id, avatar_url, tasks_completed, current_streak, unlocked_badges, last_active_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id, operator_name, "Task Reviewer",
                    json.dumps(["approve", "reject", "view"]),
                    f"BIO_{operator_name.replace(' ', '_').upper()}",
                    f"https://api.dicebear.com/7.x/bottts/svg?seed={operator_name}",
                    0, 1, json.dumps([]), time.strftime("%Y-%m-%d")
                ))
                conn.commit()
            user = self.get_user_by_name(operator_name)

        new_tasks_completed = (user.get("tasks_completed") or 0) + 1
        current_streak = user.get("current_streak") or 1
        badges = list(user.get("unlocked_badges") or [])

        # Evaluate Badge Unlocks
        if new_tasks_completed >= 1 and "First Review 🏆" not in badges:
            badges.append("First Review 🏆")
        if new_tasks_completed >= 5 and "Speed Auditor ⚡" not in badges:
            badges.append("Speed Auditor ⚡")
        if current_streak >= 7 and "7-Day Streak 🔥" not in badges:
            badges.append("7-Day Streak 🔥")
        if new_tasks_completed >= 20 and "Zero-Error Champion 🛡️" not in badges:
            badges.append("Zero-Error Champion 🛡️")
        if new_tasks_completed >= 100 and "100 Tasks Certified 👑" not in badges:
            badges.append("100 Tasks Certified 👑")

        today_str = time.strftime("%Y-%m-%d")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE user_profiles
                SET tasks_completed = ?,
                    current_streak = ?,
                    unlocked_badges = ?,
                    last_active_date = ?
                WHERE name = ?
            """, (
                new_tasks_completed,
                current_streak,
                json.dumps(badges),
                today_str,
                operator_name,
            ))
            conn.commit()

        return self.get_user_by_name(operator_name)

    # --- Batch Operations & Multi-Select Queries ---

    def get_tasks_by_status(self, status: str = "Approved") -> List[Dict[str, Any]]:
        """Pulls all tasks currently sitting in the specified status in a single batch query."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE status = ? AND archived = 0 ORDER BY created_at ASC", (status,))
            rows = cursor.fetchall()
            tasks = []
            for row in rows:
                t = dict(row)
                try:
                    t["reasoning_trace"] = json.loads(t["reasoning_trace"]) if t.get("reasoning_trace") else []
                except Exception:
                    t["reasoning_trace"] = []
                tasks.append(t)
            return tasks

    def batch_update_status(self, task_ids: List[str], new_status: str, operator_name: str) -> int:
        """Batch updates the status of multiple tasks simultaneously (honoring Notion multi-select)."""
        updated_count = 0
        for tid in task_ids:
            task = self.get_task(tid)
            if task:
                self.update_task_with_occ(
                    task_id=tid,
                    base_record=task,
                    local_updates={"status": new_status},
                    operator_name=operator_name,
                )
                if new_status == "Approved":
                    self.record_operator_approval(operator_name)
                updated_count += 1
        return updated_count


    # --- Runtime System Configuration ---

    def get_system_config(self) -> Dict[str, Any]:
        """Retrieves runtime configurable daemon settings."""
        defaults = {
            "poll_interval_minutes": POLL_INTERVAL_MINUTES,
            "poll_interval_seconds": POLL_INTERVAL_SECONDS,
            "auto_refresh_enabled": True,
            "max_batch_workers": 10,
            "language": "en",
            "last_sync_timestamp": time.time(),
        }

        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    defaults.update(data)
            except Exception:
                pass
        return defaults

    def update_system_config(self, new_settings: Dict[str, Any]) -> Dict[str, Any]:
        """Updates runtime configuration settings and persists them to CONFIG_FILE."""
        current = self.get_system_config()
        current.update(new_settings)
        if "poll_interval_minutes" in new_settings:
            current["poll_interval_seconds"] = float(current["poll_interval_minutes"] * 60)
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(current, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist system config: {e}")
        return current

    # --- System Health & Turn-Off Test Heartbeats ---

    def record_system_health_heartbeat(self, metrics: Dict[str, Any]) -> Dict[str, Any]:

        """Records a real-time system health heartbeat in the Notion System Health table."""
        now = metrics.get("timestamp", time.time())
        service = metrics.get("service_name", "Notion Tracker Worker Daemon")
        status = metrics.get("status", "HEALTHY")
        cpu = metrics.get("cpu_percent", 0.0)
        ram = metrics.get("ram_percent", 0.0)
        disk = metrics.get("disk_percent", 0.0)
        threads = metrics.get("active_threads", 1)
        tokens = metrics.get("available_tokens", 10.0)
        uptime = metrics.get("uptime_seconds", 0)

        # Compute signature seal for the heartbeat
        sig = AuditLedger.compute_record_signature(
            record_id=f"heartbeat_{int(now)}",
            action="SYSTEM_HEARTBEAT",
            operator_name="SystemHealthMonitor",
            timestamp=now,
            payload_data={"cpu": cpu, "ram": ram, "disk": disk, "status": status},
            prev_signature=self.get_latest_signature(),
        )

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO system_health (
                    service_name, status, cpu_percent, ram_percent, disk_percent,
                    active_threads, available_tokens, uptime_seconds, timestamp, signature
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (service, status, cpu, ram, disk, threads, tokens, uptime, now, sig))
            conn.commit()
            hid = cursor.lastrowid

        return {
            "id": hid,
            "service_name": service,
            "status": status,
            "cpu_percent": cpu,
            "ram_percent": ram,
            "disk_percent": disk,
            "active_threads": threads,
            "available_tokens": tokens,
            "uptime_seconds": uptime,
            "timestamp": now,
            "signature": sig,
        }

    def list_system_health_records(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves recent system health heartbeats."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM system_health ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_latest_system_health(self) -> Optional[Dict[str, Any]]:
        """Retrieves the most recent system health heartbeat."""
        records = self.list_system_health_records(limit=1)
        return records[0] if records else None

    # --- Visual Workflow Builder: Pipeline Templates ---

    def list_pipeline_templates(self) -> List[Dict[str, Any]]:
        """Retrieves all visual workflow automation templates from the Notion templates database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pipeline_templates ORDER BY created_at ASC")
            rows = cursor.fetchall()
            templates = []
            for r in rows:
                t = dict(r)
                try:
                    t["steps"] = json.loads(t["steps"]) if isinstance(t.get("steps"), str) else t.get("steps", [])
                except Exception:
                    t["steps"] = []
                templates.append(t)
            return templates

    def get_pipeline_template(self, name_or_id: str) -> Optional[Dict[str, Any]]:
        """Finds a pipeline template by its unique name or ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pipeline_templates WHERE id = ? OR name = ?", (name_or_id, name_or_id))
            row = cursor.fetchone()
            if not row:
                return None
            t = dict(row)
            try:
                t["steps"] = json.loads(t["steps"]) if isinstance(t.get("steps"), str) else t.get("steps", [])
            except Exception:
                t["steps"] = []
            return t

    def create_pipeline_template(self, template_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Creates and registers a new visual pipeline workflow template in the database."""
        tid = template_dict.get("id") or f"tmpl_{uuid.uuid4().hex[:8]}"
        name = template_dict.get("name", "Custom Visual Pipeline")
        source = template_dict.get("trigger_source", "Webhook Gateway")
        steps = template_dict.get("steps", [])
        threshold = template_dict.get("risk_threshold", "Strict HITL (All Risks)")
        status = template_dict.get("status", "Active 🟢")
        now = time.time()

        steps_json = json.dumps(steps) if isinstance(steps, list) else str(steps)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO pipeline_templates (id, name, trigger_source, steps, risk_threshold, status, version, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
            """, (tid, name, source, steps_json, threshold, status, now, now))
            conn.commit()

        return self.get_pipeline_template(tid)

    def update_pipeline_template(self, template_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Updates an existing pipeline workflow template with OCC version bump."""
        current = self.get_pipeline_template(template_id)
        if not current:
            return None

        name = updates.get("name", current["name"])
        source = updates.get("trigger_source", current["trigger_source"])
        steps = updates.get("steps", current["steps"])
        threshold = updates.get("risk_threshold", current["risk_threshold"])
        status = updates.get("status", current["status"])
        new_version = (current.get("version") or 1) + 1
        now = time.time()

        steps_json = json.dumps(steps) if isinstance(steps, list) else str(steps)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE pipeline_templates
                SET name = ?, trigger_source = ?, steps = ?, risk_threshold = ?, status = ?, version = ?, updated_at = ?
                WHERE id = ?
            """, (name, source, steps_json, threshold, status, new_version, now, template_id))
            conn.commit()

        return self.get_pipeline_template(template_id)


# Global datastore instance
default_store = NotionStore()



