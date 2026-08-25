"""Comprehensive Unit Test Suite for Notion Tracker.

Verifies zero-network, mocked enterprise components:
1. Cryptographic HMAC-SHA256 & Non-Repudiation Audit Ledger Signatures
2. Optimistic Concurrency Control (OCC) 3-Way Merge Protocol
3. Token-Bucket Rate Limiter Throttling & Telemetry
4. LangChain AI Cognitive Risk Pre-Audit & Dynamic Typesetting

Run with: python -m unittest test_tracker.py
"""

import sys
import unittest
import time
import json
import copy

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from notion_enterprise_guard import (
    TokenBucketRateLimiter,
    NonceGuard,
    generate_hmac_signature,
    verify_hmac_signature,
    OptimisticConcurrencyControl,
)
from audit_ledger import AuditLedger
from ai_audit_engine import AIAuditEngine
from notion_typesetter import NotionTypesetter


class TestCryptographicHMACAndLedger(unittest.TestCase):
    """Test Suite 1: Cryptographic HMAC, Nonce Replay Guards, and SHA-256 Ledger."""

    def setUp(self):
        self.secret = "test_enterprise_secret_key_12345"
        self.payload = b'{"event_id":"evt_001","action":"CREATE_TASK"}'

    def test_hmac_and_nonce_guards(self):
        # 1. Test HMAC generation & verification
        sig = generate_hmac_signature(self.payload, self.secret)
        self.assertTrue(verify_hmac_signature(self.payload, sig, self.secret))

        # Tampered payload must fail
        tampered = b'{"event_id":"evt_001","action":"MUTATED_TASK"}'
        self.assertFalse(verify_hmac_signature(tampered, sig, self.secret))

        # 2. Test Nonce Replay Guard
        guard = NonceGuard(max_drift_seconds=300)
        now_ts = int(time.time())
        nonce_val = "nonce_abc_123"

        # First use must pass
        valid, msg = guard.validate_and_record(nonce_val, now_ts)
        self.assertTrue(valid)

        # Re-use must be rejected as replay attack
        valid_reused, msg_reused = guard.validate_and_record(nonce_val, now_ts)
        self.assertFalse(valid_reused)
        self.assertIn("Replay attack detected", msg_reused)

        # Timestamp drift > 300s must be rejected
        valid_drift, msg_drift = guard.validate_and_record("nonce_drift_test", now_ts - 500)
        self.assertFalse(valid_drift)
        self.assertIn("Timestamp drift", msg_drift)

        # 3. Test SHA-256 Audit Ledger Chain
        log1_sig = AuditLedger.compute_record_signature(
            record_id="task_1",
            action="INGESTED",
            operator_name="Aryan Sharma",
            timestamp=1700000000.0,
            payload_data={"status": "Ready for Review"},
            prev_signature=AuditLedger.GENESIS_HASH,
        )
        log2_sig = AuditLedger.compute_record_signature(
            record_id="task_1",
            action="APPROVED",
            operator_name="Atul Yadav",
            timestamp=1700000010.0,
            payload_data={"status": "Approved"},
            prev_signature=log1_sig,
        )

        entries = [
            {
                "id": 1,
                "record_id": "task_1",
                "action": "INGESTED",
                "operator_name": "Aryan Sharma",
                "timestamp": 1700000000.0,
                "payload_data": {"status": "Ready for Review"},
                "signature": log1_sig,
                "prev_signature": AuditLedger.GENESIS_HASH,
            },
            {
                "id": 2,
                "record_id": "task_1",
                "action": "APPROVED",
                "operator_name": "Atul Yadav",
                "timestamp": 1700000010.0,
                "payload_data": {"status": "Approved"},
                "signature": log2_sig,
                "prev_signature": log1_sig,
            },
        ]

        # Valid chain test
        audit_res = AuditLedger.verify_ledger_chain(entries)
        self.assertEqual(audit_res["status"], "SECURE")
        self.assertEqual(audit_res["mismatches_detected"], 0)
        self.assertTrue(audit_res["signature_chain_valid"])

        # Tampered entry test
        entries_tampered = copy.deepcopy(entries)
        entries_tampered[0]["payload_data"]["status"] = "UNAUTHORIZED_EDIT"
        tamper_res = AuditLedger.verify_ledger_chain(entries_tampered)
        self.assertEqual(tamper_res["status"], "ALERT")
        self.assertGreater(tamper_res["mismatches_detected"], 0)


class TestOptimisticConcurrencyControl(unittest.TestCase):
    """Test Suite 2: Optimistic Concurrency Control (OCC) & 3-Way Merge."""

    def test_occ_three_way_merge(self):
        # Base snapshot
        base = {
            "id": "task_101",
            "title": "Lab Provisioning",
            "priority": "normal",
            "status": "Ready for Review",
            "details": "Initial lab quota request.",
            "version": 1,
            "nonce": "nonce_v1",
        }

        # Local edit: Human approves the task
        local = copy.deepcopy(base)
        local["status"] = "Approved"

        # Remote edit: Background worker updated the details
        remote = copy.deepcopy(base)
        remote["details"] = "Initial lab quota request. [Worker: Quota confirmed]"
        remote["version"] = 2
        remote["nonce"] = "nonce_v2"

        # Execute 3-Way Merge
        merged, had_conflict, details = OptimisticConcurrencyControl.resolve_three_way_merge(
            base_record=base,
            local_record=local,
            remote_record=remote,
        )

        # Assertions
        self.assertEqual(merged["status"], "Approved")  # Operator decision preserved
        self.assertEqual(merged["details"], "Initial lab quota request. [Worker: Quota confirmed]")  # Remote edit merged
        self.assertEqual(merged["version"], 3)  # Incremented version
        self.assertNotEqual(merged["nonce"], "nonce_v1")  # New nonce generated


class TestTokenBucketRateLimiter(unittest.TestCase):
    """Test Suite 3: Token-Bucket Rate Limiter Throttling & Telemetry."""

    def test_rate_limiter_behavior(self):
        limiter = TokenBucketRateLimiter(capacity=5.0, replenish_rate=10.0)

        # 1. Should acquire initial tokens immediately
        self.assertTrue(limiter.acquire(tokens=3.0, block=False))

        # 2. Telemetry check
        state = limiter.get_state()
        self.assertEqual(state["token_bucket"]["capacity"], 5.0)
        self.assertEqual(state["token_bucket"]["status"], "NOMINAL")

        # 3. Exhaust tokens
        limiter.acquire(tokens=2.0, block=False)
        # Immediate non-blocking request should fail if empty
        self.assertFalse(limiter.acquire(tokens=10.0, block=False))

        # 4. Wait for replenishment
        time.sleep(0.25)
        # Should now have replenished ~2.5 tokens
        self.assertTrue(limiter.acquire(tokens=1.0, block=False))

    def test_daemon_batch_query_and_60m_config(self):
        from notion_store import default_store
        # 1. Test 60m default config
        cfg = default_store.get_system_config()
        self.assertIn("poll_interval_minutes", cfg)
        self.assertEqual(cfg["poll_interval_minutes"], 60)
        self.assertEqual(cfg["poll_interval_seconds"], 3600.0)

        # 2. Test runtime config update
        updated_cfg = default_store.update_system_config({"poll_interval_minutes": 30, "auto_refresh_enabled": True})
        self.assertEqual(updated_cfg["poll_interval_minutes"], 30)
        self.assertEqual(updated_cfg["poll_interval_seconds"], 1800.0)

        # Restore 60m default
        default_store.update_system_config({"poll_interval_minutes": 60, "auto_refresh_enabled": True})

        # 3. Test batch query
        t1 = default_store.create_task({"title": "Batch Test Item 1", "status": "Ready for Review"})
        t2 = default_store.create_task({"title": "Batch Test Item 2", "status": "Ready for Review"})
        default_store.batch_update_status([t1["id"], t2["id"]], "Approved", "Test Multi-Select")
        approved_batch = default_store.get_tasks_by_status("Approved")
        self.assertGreaterEqual(len(approved_batch), 2)



class TestAIAuditAndTypesetting(unittest.TestCase):
    """Test Suite 4: AI Pre-Audit Cognitive Scoring and Notion Blocks Typesetting."""

    def test_ai_pre_audit_and_typesetting(self):
        # 1. Test High/Critical Risk Detection
        critical_title = "Emergency Security Incident: Unauthorized Root Access"
        critical_details = "Purge compromised tokens and revoke administrative credentials."
        crit_res = AIAuditEngine.analyze_task(critical_title, critical_details, requested_priority="critical")

        self.assertEqual(crit_res.risk_level, "CRITICAL")
        self.assertGreaterEqual(crit_res.confidence_score, 0.90)
        self.assertIn("CRITICAL_OPERATION_DETECTED", crit_res.security_flags)
        self.assertGreater(len(crit_res.reasoning_trace), 3)

        # 2. Test Normal/Low Risk Task
        norm_title = "Provisions for Lab Group B"
        norm_details = "Register 15 student seats and dispatch welcome packages."
        norm_res = AIAuditEngine.analyze_task(norm_title, norm_details, requested_priority="normal")

        self.assertIn(norm_res.risk_level, ("LOW", "MEDIUM"))
        self.assertEqual(norm_res.category, "Academic Registration")
        self.assertTrue(len(norm_res.draft_email_html) > 0)
        self.assertTrue(len(norm_res.draft_teams_text) > 0)

        # 3. Test Notion Blocks Typesetting
        task_data = {
            "title": norm_title,
            "details": norm_details,
            "priority": "normal",
        }
        blocks = NotionTypesetter.build_cognitive_audit_blocks(task_data, norm_res.to_dict())

        # Verify essential Notion block types exist
        block_types = [b.get("type") for b in blocks]
        self.assertIn("callout", block_types)  # Risk banner
        self.assertIn("toggle", block_types)   # CoT trace toggle
        self.assertIn("to_do", block_types)    # Verification checklist
        self.assertIn("divider", block_types)  # Turn-Off Test styling

    def test_notion_run_log_typesetting_and_dual_toggles(self):
        """Verifies Toggle 1 (bulleted reasoning steps) and Toggle 2 (code raw payload)."""
        from notion_typesetter import NotionTypesetter
        from notion_store import default_store

        reasoning = [
            "[Step 1] Ingested raw payload via HMAC gateway",
            "[Step 2] AI classified as LOW risk",
            "[Step 3] Operator approved and dispatched"
        ]
        raw_payload = {
            "title": "Lab Group Provisions",
            "seats": 15,
            "status": "Approved"
        }

        # 1. Test programmatic block generation
        blocks = NotionTypesetter.build_run_log_page_blocks(
            reasoning_steps=reasoning,
            raw_payload=raw_payload,
            action="EXECUTION_DISPATCHED",
            operator_name="Aryan Sharma",
        )

        toggles = [b for b in blocks if b.get("type") == "toggle"]
        self.assertEqual(len(toggles), 2)

        # Toggle 1: 🔍 View Step-by-Step AI Reasoning Steps
        toggle1 = toggles[0]["toggle"]
        self.assertIn("🔍 View Step-by-Step AI Reasoning Steps", toggle1["rich_text"][0]["text"]["content"])
        self.assertEqual(len(toggle1["children"]), 3)
        self.assertEqual(toggle1["children"][0]["type"], "bulleted_list_item")

        # Toggle 2: 📄 View Raw JSON Ingestion Payload
        toggle2 = toggles[1]["toggle"]
        self.assertIn("📄 View Raw JSON Ingestion Payload", toggle2["rich_text"][0]["text"]["content"])
        self.assertEqual(len(toggle2["children"]), 1)
        self.assertEqual(toggle2["children"][0]["type"], "code")
        self.assertEqual(toggle2["children"][0]["code"]["language"], "json")

        # 2. Test write_to_run_log integration
        log_entry = default_store.write_to_run_log(
            record_id="task_test_run_log_101",
            action="EXECUTION_DISPATCHED",
            operator_name="Aryan Sharma",
            task_data={"id": "task_test_run_log_101", "title": "Test Run Log Task", "status": "Dispatched"},
            reasoning_steps=reasoning,
            raw_payload=raw_payload,
        )
        self.assertIsNotNone(log_entry)
        self.assertEqual(log_entry["action"], "EXECUTION_DISPATCHED")
        self.assertIn("notion_blocks", log_entry["payload_data"])

    def test_system_health_heartbeat_and_turn_off_test(self):
        """Verifies psutil resource polling and Notion System Health table heartbeats."""
        from system_health_monitor import SystemHealthMonitor
        from notion_store import default_store

        metrics = SystemHealthMonitor.collect_metrics()
        self.assertIn("cpu_percent", metrics)
        self.assertIn("ram_percent", metrics)
        self.assertIn("status", metrics)
        self.assertEqual(metrics["status"], "HEALTHY")

        # Emit heartbeat to Notion table
        hb = SystemHealthMonitor.emit_heartbeat()
        self.assertIsNotNone(hb["id"])
        self.assertIsNotNone(hb["signature"])

        latest = default_store.get_latest_system_health()
        self.assertIsNotNone(latest)
        self.assertEqual(latest["service_name"], "Notion Tracker Worker Daemon")

    def test_voice_memo_and_comment_agent_budget(self):
        """Verifies native audio memo transcription and @AI budget command parsing."""
        from voice_memo_agent import VoiceMemoAgent
        from notion_comment_agent import NotionCommentAgent
        from notion_store import default_store

        # 1. Test Voice Memo Agent
        task = default_store.create_task({
            "title": "Voice Memo Provision Task",
            "details": "Initial scope description.",
            "priority": "normal",
            "status": "Ready for Review",
        })

        voice_note = "Voice memo: Please update budget to $4,500 and escalate priority to critical for Lab Group B."
        ok, summary, updated = VoiceMemoAgent.process_voice_memo_on_task(
            task_id=task["id"],
            audio_input=voice_note,
            operator_name="Aryan Sharma",
            mock_transcript=voice_note,
        )
        self.assertTrue(ok)
        self.assertEqual(updated.get("budget"), "$4,500")
        self.assertEqual(updated.get("priority"), "critical")
        self.assertEqual(updated.get("risk_level"), "CRITICAL")
        self.assertIn("Voice Memo Attachment", updated.get("details"))

        # 2. Test @AI Comment Agent budget command
        c_ok, c_reply = NotionCommentAgent.process_comment(
            task_id=task["id"],
            comment_text="@AI update budget $6,200",
            author_name="Atul Yadav",
        )
        self.assertTrue(c_ok)
        self.assertIn("$6,200", c_reply)
        reloaded = default_store.get_task(task["id"])
        self.assertEqual(reloaded.get("budget"), "$6,200")

    def test_multilingual_notion_typesetting_and_localization(self):
        """Verifies dynamic Notion-native typesetting and localization across multiple languages."""
        from notion_typesetter import NotionTypesetter
        from i18n import t, set_current_language, get_current_language
        from notion_store import default_store

        task_data = {
            "id": "task_i18n_test_101",
            "title": "International Provisioning Task",
            "details": "Dispatch international developer credentials and servers.",
            "priority": "high",
            "category": "Infrastructure",
        }
        audit_res = {
            "risk_level": "HIGH",
            "confidence_score": 0.94,
            "category": "Infrastructure",
            "reasoning_trace": [
                "[Step 1] Ingested and verified payload HMAC-SHA256 signature.",
                "[Step 2] AI Pre-Audit evaluated high infrastructure risk.",
            ],
            "draft_summary": "Infrastructure provisioning summary",
            "draft_teams_text": "Infrastructure provisioning notification",
        }

        # 1. Test Spanish Typesetting (es)
        es_blocks = NotionTypesetter.build_cognitive_audit_blocks(task_data, audit_res, lang="es")
        es_texts = []
        for b in es_blocks:
            b_type = b.get("type")
            if b_type in b:
                for rt in b[b_type].get("rich_text", []):
                    es_texts.append(rt.get("text", {}).get("content", ""))
        es_joined = " ".join(es_texts)
        self.assertIn("EVALUACIÓN DE RIESGO PREVIA: HIGH", es_joined)
        self.assertIn("Especificaciones de Tarea", es_joined)
        self.assertIn("Puntos de Verificación Humana", es_joined)

        # 2. Test German Typesetting (de)
        de_blocks = NotionTypesetter.build_cognitive_audit_blocks(task_data, audit_res, lang="de")
        de_texts = []
        for b in de_blocks:
            b_type = b.get("type")
            if b_type in b:
                for rt in b[b_type].get("rich_text", []):
                    de_texts.append(rt.get("text", {}).get("content", ""))
        de_joined = " ".join(de_texts)
        self.assertIn("RISIKO-VORABPRÜFUNGSEVALUIERUNG", de_joined)
        self.assertIn("Aufgabenspezifikationen", de_joined)

        # 3. Test Japanese Typesetting (ja)
        ja_blocks = NotionTypesetter.build_run_log_page_blocks(
            reasoning_steps=audit_res["reasoning_trace"],
            raw_payload=task_data,
            action="EXECUTION_DISPATCHED",
            operator_name="Aryan Sharma",
            lang="ja",
        )
        ja_texts = []
        for b in ja_blocks:
            b_type = b.get("type")
            if b_type in b:
                for rt in b[b_type].get("rich_text", []):
                    ja_texts.append(rt.get("text", {}).get("content", ""))
        ja_joined = " ".join(ja_texts)
        self.assertIn("AIの思考プロセスをステップ毎に表示", ja_joined)
        self.assertIn("生のJSONペイロードを表示", ja_joined)

        # 4. Test Hindi Typesetting (hi)
        hi_blocks = NotionTypesetter.build_cognitive_audit_blocks(task_data, audit_res, lang="hi")
        hi_texts = []
        for b in hi_blocks:
            b_type = b.get("type")
            if b_type in b:
                for rt in b[b_type].get("rich_text", []):
                    hi_texts.append(rt.get("text", {}).get("content", ""))
        hi_joined = " ".join(hi_texts)
        self.assertIn("जोखिम पूर्व-ऑडिट मूल्यांकन", hi_joined)
        self.assertIn("कार्य विवरण और पेलोड", hi_joined)

    def test_user_profiles_gamification_and_streaks(self):
        """Verifies User Profiles database provisioning, streak tracking, formula rendering, and badge awards."""
        from notion_store import default_store
        from create_databases import provision_sqlite_database, USER_PROFILES_DB_SCHEMA

        # 1. Verify schema definition
        self.assertIn("Tasks Completed", USER_PROFILES_DB_SCHEMA["properties"])
        self.assertIn("Current Streak", USER_PROFILES_DB_SCHEMA["properties"])
        self.assertIn("Unlocked Badges", USER_PROFILES_DB_SCHEMA["properties"])
        self.assertIn("Streak Flame", USER_PROFILES_DB_SCHEMA["properties"])

        # 2. Test database provisioning
        prov_res = provision_sqlite_database()
        self.assertEqual(prov_res["status"], "SUCCESS")

        # 3. Test operator approval recording & streak progression
        test_op = f"TestOperator_{int(time.time())}"
        user_initial = default_store.record_operator_approval(test_op)
        self.assertEqual(user_initial["tasks_completed"], 1)
        self.assertIn("First Review 🏆", user_initial["unlocked_badges"])
        self.assertIn("🔥", user_initial["streak_flame"])
        self.assertEqual(user_initial["level_badge"], "Level 1")

        # Increment up to 5 approvals for Speed Auditor badge
        for _ in range(4):
            updated_user = default_store.record_operator_approval(test_op)

        self.assertEqual(updated_user["tasks_completed"], 5)
        self.assertIn("Speed Auditor ⚡", updated_user["unlocked_badges"])
        self.assertEqual(updated_user["level_badge"], "Level 1")
        self.assertEqual(updated_user["progress_percent"], 50)

    def test_pipeline_templates_and_workflow_execution(self):
        """Verifies visual pipeline templates database, dynamic step execution, and Turn-Off Test compliance."""
        from notion_store import default_store
        from workflow_engine import WorkflowEngine, AVAILABLE_PIPELINE_STEPS
        from create_databases import PIPELINE_TEMPLATES_DB_SCHEMA

        # 1. Verify Notion Schema properties
        self.assertIn("Template Name", PIPELINE_TEMPLATES_DB_SCHEMA["properties"])
        self.assertIn("Execution Pipeline Steps", PIPELINE_TEMPLATES_DB_SCHEMA["properties"])
        self.assertIn("Risk Threshold", PIPELINE_TEMPLATES_DB_SCHEMA["properties"])
        self.assertIn("Status", PIPELINE_TEMPLATES_DB_SCHEMA["properties"])

        # 2. Test template retrieval and creation
        templates = default_store.list_pipeline_templates()
        self.assertGreaterEqual(len(templates), 1)

        custom_tmpl = default_store.create_pipeline_template({
            "name": f"Dynamic Unit Test Pipeline {int(time.time())}",
            "trigger_source": "Webhook Gateway",
            "steps": [
                "1. HMAC Nonce Verify 🛡️",
                "2. Cognitive AI Pre-Audit 🧠",
                "4. Teams Adaptive Card 💬",
                "6. SHA-256 Signature Seal 📊",
            ],
            "risk_threshold": "Strict HITL (All Risks)",
            "status": "Active 🟢",
        })
        self.assertIsNotNone(custom_tmpl)
        self.assertEqual(len(custom_tmpl["steps"]), 4)

        # 3. Test dynamic WorkflowEngine execution
        test_task = {
            "id": f"task_test_wf_{int(time.time())}",
            "title": "Emergency Firewall Rule Revocation",
            "details": "Revoke leaked credentials for compromised server instance immediately.",
            "priority": "critical",
            "source": "Webhook Gateway",
        }
        success, trace, updated_task = WorkflowEngine.execute_pipeline(
            task=test_task,
            template=custom_tmpl,
            operator_name="Aryan Sharma",
            override_biometric=True,
        )
        self.assertTrue(success)
        self.assertEqual(updated_task["status"], "Dispatched")
        self.assertEqual(updated_task["risk_level"], "CRITICAL")
        self.assertTrue(any("HMAC" in s for s in trace))
        self.assertTrue(any("AI Pre-Audit" in s for s in trace))
        self.assertTrue(any("Teams Dispatch" in s for s in trace))

    def test_notion_voice_command_agent_gemini(self):
        """Verifies Gemini 1.5 Flash voice command parsing, Notion typesetting, and OCC budget updates."""
        from notion_voice_agent import NotionVoiceCommandAgent
        from notion_store import default_store

        agent = NotionVoiceCommandAgent()

        # 1. Process mock voice command for approval & budget update
        parsed = agent.process_voice_command("voice_approve_command.wav")
        self.assertTrue(parsed.get("is_command"))
        self.assertEqual(parsed.get("command_type"), "UPDATE_BUDGET")
        self.assertIn("Aryan", parsed.get("transcript", ""))
        self.assertGreaterEqual(parsed.get("confidence_score", 0.0), 0.8)

        # 2. Create task and execute voice command
        test_task_id = f"task_voice_{int(time.time())}"
        default_store.create_task({
            "id": test_task_id,
            "title": "Voice Budget Allocation",
            "details": "Pending voice verification.",
            "priority": "high",
            "status": "Ready for Review",
        }, operator_name="Voice Test")

        res = agent.execute_voice_command_in_notion(test_task_id, parsed, operator_name="Aryan Sharma")
        self.assertEqual(res["status"], "SUCCESS")

        updated_task = default_store.get_task(test_task_id)
        self.assertEqual(updated_task["status"], "Approved")
        self.assertEqual(updated_task["budget"], "$5,000")

    def test_notion_signature_gateway_and_mfa(self):
        """Verifies operator profile-bound signatures, OTP MFA verification, and high-risk task gates."""
        from notion_signature_gateway import (
            calculate_operator_signature,
            verify_log_integrity,
            OTPGateway,
            NotionEnterpriseGuard,
        )

        operator_profile = {
            "name": "Aryan Sharma",
            "email": "aryan.sharma@aiexperts.edu",
            "role": "Lead Developer",
            "phone": "+919876543210",
        }
        task_payload = {
            "task_id": "test_mfa_task_001",
            "title": "Purge Financial Ledgers",
            "action": "Shift $50k USD to priority reserve",
            "risk_level": "HIGH",
            "timestamp": "2026-08-25T00:00:00Z",
        }

        # 1. Signature calculation & non-repudiation
        sig, payload = calculate_operator_signature(
            task_payload["task_id"], task_payload["title"], task_payload["action"],
            operator_profile["email"], operator_profile["role"],
            task_payload["timestamp"], "SUCCESS",
        )
        is_valid, _ = verify_log_integrity(
            sig, task_payload["task_id"], task_payload["title"], task_payload["action"],
            operator_profile["email"], operator_profile["role"],
            task_payload["timestamp"], "SUCCESS",
        )
        self.assertTrue(is_valid)

        # 2. OTP Generation & Verification
        otp_rec = OTPGateway.generate_otp(operator_profile["phone"])
        self.assertTrue(OTPGateway.verify_otp(operator_profile["phone"], otp_rec["raw_otp_debug"], otp_rec))
        self.assertFalse(OTPGateway.verify_otp(operator_profile["phone"], "000000", otp_rec))

        # 3. High-Risk Task Authorization Gate
        # Blocked without OTP
        res_blocked = NotionEnterpriseGuard.authorize_high_risk_task(
            operator_profile, task_payload, otp_verified=False, signature=sig
        )
        self.assertFalse(res_blocked["authorized"])

        # Approved with OTP + Valid Signature
        res_approved = NotionEnterpriseGuard.authorize_high_risk_task(
            operator_profile, task_payload, otp_verified=True, signature=sig
        )
        self.assertTrue(res_approved["authorized"])
        self.assertIsNotNone(res_approved["security_seal"])


class TestEnterpriseBlueprintGaps(unittest.TestCase):
    """Test Suite 5: 3 Blueprint Enterprise Gaps (Draft Staging, DLQ, Deduplication)."""

    def setUp(self):
        from notion_store import default_store
        from deduplication_engine import DeduplicationFingerprinter
        self.store = default_store
        self.dedup = DeduplicationFingerprinter(default_window_seconds=3600)

    def test_deduplication_fingerprinting_1hr_window(self):
        """Stage 1 Gap: Deduplication Fingerprinting blocks redundant submissions within 1-hour window."""
        title = "Provision Lab B Devices"
        details = "15 student workstations"
        source = "Academic Portal"
        sender = "student.affairs@university.edu"
        now = time.time()

        fp1 = self.dedup.compute_fingerprint(title, details, source, sender=sender, timestamp=now)
        fp2 = self.dedup.compute_fingerprint("  provision lab b devices  ", "15 student workstations", source, sender="STUDENT.AFFAIRS@UNIVERSITY.EDU", timestamp=now)

        # Normalized inputs must produce identical SHA-256 fingerprints
        self.assertEqual(fp1, fp2)

        # First ingestion must pass
        is_uniq1, dup_id1, _ = self.dedup.check_and_record(fp1, "task_orig_001", timestamp=now)
        self.assertTrue(is_uniq1)
        self.assertIsNone(dup_id1)

        # Submission within 1-hour window (e.g. 1800s later) must be rejected
        is_uniq2, dup_id2, reason = self.dedup.check_and_record(fp1, "task_duplicate_002", timestamp=now + 1800)
        self.assertFalse(is_uniq2)
        self.assertEqual(dup_id2, "task_orig_001")
        self.assertIn("Duplicate submission blocked", reason)

        # Submission after 1-hour window (e.g. 4000s later) passes
        fp_later = self.dedup.compute_fingerprint(title, details, source, sender=sender, timestamp=now + 4000)
        is_uniq3, _, _ = self.dedup.check_and_record(fp_later, "task_later_003", timestamp=now + 4000)
        self.assertTrue(is_uniq3)

    def test_ai_reasoning_ledger_property(self):
        """Stage 2 Gap: Background agent writes a concise 1-2 sentence justification to AI Reasoning Ledger."""
        from ai_audit_engine import AIAuditEngine
        from notion_typesetter import NotionTypesetter

        title = "Urgent Database Credential Rotation and Firewall Reset"
        details = "Rotate master secret keys on secondary replica cluster."
        audit_res = AIAuditEngine.analyze_task(title=title, details=details, requested_priority="high")

        # Must have concise natural language explanation
        self.assertIsNotNone(audit_res.ai_reasoning_ledger)
        self.assertTrue(len(audit_res.ai_reasoning_ledger) > 20)
        self.assertIn("Classified as HIGH risk", audit_res.ai_reasoning_ledger)

        # Must be persisted in store
        task_id = f"test_ledger_{int(time.time())}"
        created = self.store.create_task({
            "id": task_id,
            "title": title,
            "details": details,
            "priority": audit_res.suggested_priority,
            "category": audit_res.category,
            "status": "Ready for Review",
            "risk_level": audit_res.risk_level,
            "ai_reasoning_ledger": audit_res.ai_reasoning_ledger,
        })
        self.assertEqual(created["ai_reasoning_ledger"], audit_res.ai_reasoning_ledger)

        # Typesetter must output AI Reasoning Ledger callout
        blocks = NotionTypesetter.build_cognitive_audit_blocks(created, audit_res.to_dict())
        ledger_blocks = [b for b in blocks if "AI Reasoning Ledger" in str(b)]
        self.assertGreaterEqual(len(ledger_blocks), 1)

    def test_draft_and_diff_staging(self):
        """Gap 1: Human operator staged revisions override AI proposed draft."""
        from outbound_dispatcher import TeamsAdaptiveCardBuilder
        task_id = f"test_stage_{int(time.time())}"
        task_dict = {
            "id": task_id,
            "title": "Database Schema Migration",
            "details": "Run 042_schema.sql on replica cluster",
            "priority": "high",
            "category": "Infrastructure",
            "status": "Ready for Review",
            "risk_level": "HIGH",
            "confidence_score": 0.92,
            "draft_teams_text": "AI Proposed: Migrate schema on cluster.",
            "proposed_ai_draft": "AI Proposed: Migrate schema on cluster.",
        }
        created = self.store.create_task(task_dict, operator_name="Test Ingest")
        self.assertIsNotNone(created)
        self.assertEqual(created["proposed_ai_draft"], "AI Proposed: Migrate schema on cluster.")

        # Human operator stages custom refined draft
        human_text = "Human Operator Revised: Certified and approved migration for Cluster A with zero downtime."
        updated = self.store.update_staged_draft(task_id, human_text, operator_name="Aryan Sharma")
        self.assertEqual(updated["edited_draft"], human_text)

        # Outbound Teams card must prioritize human-edited draft
        card = TeamsAdaptiveCardBuilder.build_card_payload(updated, "Aryan Sharma")
        card_body = card["attachments"][0]["content"]["body"]
        text_blocks = [b["text"] for b in card_body if b.get("type") == "TextBlock"]
        self.assertIn(human_text, text_blocks)

    def test_dead_letter_queue_quarantine(self):
        """Gap 2: Unprocessable or corrupt payloads are quarantined in DLQ."""
        corrupt_id = f"test_dlq_{int(time.time())}"
        corrupt_task = {
            "id": corrupt_id,
            "title": "Corrupt Payload Ingestion",
            "details": "Malformed payload with schema error",
            "status": "Ready for Review",
        }
        self.store.create_task(corrupt_task, operator_name="Test Ingest")

        # Simulate unexpected processing failure
        mock_traceback = "Traceback (most recent call last):\n  File 'agent.py', line 42, in process\nValueError: Corrupt input"
        dlq_task = self.store.route_to_dlq(
            task_id=corrupt_id,
            error_trace=mock_traceback,
            reason="ValueError: Corrupt input schema",
            operator_name="DLQ Guard",
        )
        self.assertEqual(dlq_task["status"], "DLQ: Needs Technical Review")
        self.assertEqual(dlq_task["dlq_reason"], "ValueError: Corrupt input schema")
        self.assertIn("ValueError: Corrupt input", dlq_task["dlq_error_trace"])

        # DLQ query must list the quarantined task
        dlq_items = self.store.get_dlq_tasks()
        dlq_ids = [t["id"] for t in dlq_items]
        self.assertIn(corrupt_id, dlq_ids)

    def test_dlq_red_callout_typesetting(self):
        """Verifies NotionTypesetter generates high-visibility red warning callout and traceback blocks."""
        task_data = {
            "id": "task_dlq_test_101",
            "title": "Corrupt JSON Ingestion",
            "status": "DLQ: Needs Technical Review",
            "dlq_reason": "JSONDecodeError: Expecting value: line 1 column 1 (char 0)",
            "dlq_error_trace": "Traceback (most recent call last):\n  File 'parser.py', line 12, in parse\nJSONDecodeError",
        }
        blocks = NotionTypesetter.build_cognitive_audit_blocks(
            task_data=task_data,
            audit_result={"risk_level": "CRITICAL", "confidence_score": 0.0, "reasoning_trace": []},
        )
        callouts = [b for b in blocks if b.get("type") == "callout"]
        codes = [b for b in blocks if b.get("type") == "code"]
        
        # Must contain red warning callout
        red_callouts = [c for c in callouts if c.get("callout", {}).get("color") == "red_background"]
        self.assertGreaterEqual(len(red_callouts), 1)
        
        # Dedicated standalone DLQ diagnostic blocks
        diag_blocks = NotionTypesetter.build_dlq_diagnostic_blocks(
            task_data=task_data,
            error_trace=task_data["dlq_error_trace"],
            reason=task_data["dlq_reason"],
        )
        self.assertEqual(len(diag_blocks), 3)
        self.assertEqual(diag_blocks[0]["type"], "callout")
        self.assertEqual(diag_blocks[0]["callout"]["color"], "red_background")
        self.assertEqual(diag_blocks[1]["type"], "code")

    def test_unified_daemon_cycle(self):
        """Feature 1: Verifies the unified daemon orchestrates comments, voice, and approved task dispatches."""
        from main import NotionTrackerDaemon
        from notion_comment_agent import NotionCommentAgent
        from notion_voice_agent import default_voice_agent

        daemon = NotionTrackerDaemon(poll_interval_minutes=60)

        # 1. Seed a task with @AI comment
        t_comm_id = f"task_comm_{int(time.time())}"
        self.store.create_task({
            "id": t_comm_id,
            "title": "Comment Agent Unified Test",
            "details": "Checking @AI budget update integration.",
            "status": "Ready for Review",
            "comment_thread": "@AI update budget $8,500 for Lab Group C",
        })

        # 2. Seed a task with voice memo attachment
        t_voice_id = f"task_voice_{int(time.time())}"
        self.store.create_task({
            "id": t_voice_id,
            "title": "Voice Memo Unified Test",
            "details": "Checking native voice recording integration.",
            "status": "Ready for Review",
            "audio_file": "voice_approve_command.wav",
        })

        # 3. Seed an Approved task for batch dispatch
        t_appr_id = f"task_appr_{int(time.time())}"
        self.store.create_task({
            "id": t_appr_id,
            "title": "Approved Dispatch Unified Test",
            "details": "Batch dispatch execution.",
            "status": "Approved",
            "edited_draft": "Human operator revised notification wording.",
        })

        # Execute single unified daemon cycle
        dispatched_count = daemon.process_cycle()
        self.assertGreaterEqual(dispatched_count, 1)

        # Verify comment task was processed
        updated_comm = self.store.get_task(t_comm_id)
        self.assertEqual(updated_comm["budget"], "$8,500")

        # Verify voice task was processed
        updated_voice = self.store.get_task(t_voice_id)
        self.assertEqual(updated_voice["budget"], "$5,000")

        # Verify approved task was dispatched
        updated_appr = self.store.get_task(t_appr_id)
        self.assertEqual(updated_appr["status"], "Dispatched")


if __name__ == "__main__":
    unittest.main()







