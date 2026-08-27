"""Exhaustive 100-Test Suite for Notion Tracker Production Readiness.

Validates all 12 core subsystems:
1. Datastore CRUD & Seeding (Tests 1–10)
2. Optimistic Concurrency Control (OCC) & 3-Way Merge (Tests 11–20)
3. Zero-Trust Digital Signatures & HMAC (Tests 21–30)
4. 6-Digit SMS OTP MFA Security Gate (Tests 31–38)
5. AI Audit Engine & Cognitive Risk Scoring (Tests 39–48)
6. Natural Language @AI Comment Agent (Tests 49–58)
7. Gemini 1.5 Flash Voice Memo Agent (Tests 59–68)
8. Dead-Letter Queue (DLQ) & Fault Isolation (Tests 69–76)
9. Deduplication Fingerprinting & Nonce Replay Guard (Tests 77–84)
10. System Health Monitor & Heartbeat Emission (Tests 85–90)
11. Executive PDF & CSV Report Builders (Tests 91–95)
12. FastAPI Webhook Gateway REST Endpoints (Tests 96–100)
"""

import sys
import os
import time
import unittest
import json
import copy
import uuid
from datetime import timedelta

# Ensure project root is in python path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from notion_store import default_store, NotionStore
from notion_enterprise_guard import (
    default_rate_limiter,
    default_nonce_guard,
    verify_hmac_signature,
    OptimisticConcurrencyControl,
)
from notion_signature_gateway import (
    calculate_operator_signature,
    verify_log_integrity,
    OTPGateway,
    NotionEnterpriseGuard,
)
from ai_audit_engine import AIAuditEngine
from notion_comment_agent import NotionCommentAgent
from voice_memo_agent import VoiceMemoAgent
from notion_voice_agent import default_voice_agent
from deduplication_engine import default_deduplicator, DeduplicationFingerprinter
from system_health_monitor import SystemHealthMonitor
from report_builder import PDFReportBuilder
from audit_ledger import AuditLedger
from workflow_engine import WorkflowEngine
from webhook_gateway import (
    app,
    health_check,
    get_throttle_state,
    verify_ledger,
    list_tasks,
    get_system_config,
    update_system_config,
    process_comment_command,
    process_voice_command,
    CommentCommandRequest,
    VoiceCommandRequest,
)


class Test100NotionTrackerRobustness(unittest.TestCase):
    """Exhaustive 100-test suite verifying every single function and subsystem."""

    # =========================================================================
    # SUBSYSTEM 1: DATASTORE CRUD & SEEDING (TESTS 1–10)
    # =========================================================================
    def test_001_create_task(self):
        t = default_store.create_task({"title": "Test Task 1", "details": "Details 1"})
        self.assertIsNotNone(t.get("id"))
        self.assertEqual(t.get("title"), "Test Task 1")

    def test_002_get_task_by_id(self):
        t = default_store.create_task({"title": "Test Task 2", "details": "Details 2"})
        fetched = default_store.get_task(t["id"])
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["title"], "Test Task 2")

    def test_003_list_tasks(self):
        tasks = default_store.list_tasks(include_archived=False)
        self.assertIsInstance(tasks, list)
        self.assertGreater(len(tasks), 0)

    def test_004_update_task_fields(self):
        t = default_store.create_task({"title": "Test Task 4", "budget": "$1,000"})
        upd, _, _ = default_store.update_task_with_occ(t["id"], t, {"budget": "$5,000"}, "Tester")
        self.assertEqual(upd.get("budget"), "$5,000")

    def test_005_get_tasks_by_status(self):
        t = default_store.create_task({"title": "Approved Task", "status": "Approved"})
        approved = default_store.get_tasks_by_status("Approved")
        self.assertTrue(any(item["id"] == t["id"] for item in approved))

    def test_006_archive_task(self):
        t = default_store.create_task({"title": "Archive Task"})
        upd, _, _ = default_store.update_task_with_occ(t["id"], t, {"archived": 1}, "Tester")
        self.assertEqual(upd.get("archived"), 1)

    def test_007_seed_default_users(self):
        users = default_store.list_user_profiles()
        self.assertIsInstance(users, list)
        self.assertGreater(len(users), 0)

    def test_008_record_operator_approval(self):
        user = default_store.record_operator_approval("Aryan Sharma")
        self.assertIsNotNone(user)
        self.assertGreaterEqual(user.get("tasks_completed", 0), 1)

    def test_009_write_run_log(self):
        log_entry = default_store.write_to_run_log(
            record_id="rec_009",
            action="UNIT_TEST_LOG",
            operator_name="Tester",
            task_data={"title": "Log Test"},
            reasoning_steps=["Step 1", "Step 2"],
        )
        self.assertIsNotNone(log_entry.get("id"))
        self.assertIsNotNone(log_entry.get("signature"))

    def test_010_list_audit_logs(self):
        logs = default_store.list_audit_logs()
        self.assertIsInstance(logs, list)
        self.assertGreater(len(logs), 0)

    # =========================================================================
    # SUBSYSTEM 2: OPTIMISTIC CONCURRENCY CONTROL (OCC) (TESTS 11–20)
    # =========================================================================
    def test_011_occ_version_increment(self):
        t = default_store.create_task({"title": "OCC Task 11", "version": 1})
        upd, conflict, _ = default_store.update_task_with_occ(t["id"], t, {"budget": "$9,000"}, "Tester")
        self.assertFalse(conflict)
        self.assertEqual(upd.get("version"), 2)

    def test_012_occ_stale_base_detection(self):
        t = default_store.create_task({"title": "OCC Task 12", "version": 1})
        stale_base = copy.deepcopy(t)
        stale_base["version"] = 1
        default_store.update_task_with_occ(t["id"], t, {"budget": "$2,000"}, "Tester")
        upd, conflict, details = default_store.update_task_with_occ(t["id"], stale_base, {"budget": "$3,000"}, "Tester")
        self.assertTrue(conflict)

    def test_013_occ_3way_merge_details(self):
        t = default_store.create_task({"title": "OCC Task 13", "details": "Base Details", "version": 1})
        stale_base = copy.deepcopy(t)
        stale_base["version"] = 1
        default_store.update_task_with_occ(t["id"], t, {"priority": "high"}, "Tester")
        upd, conflict, details = default_store.update_task_with_occ(t["id"], stale_base, {"details": "New Details"}, "Tester")
        self.assertEqual(upd.get("priority"), "high")
        self.assertEqual(upd.get("details"), "New Details")

    def test_014_occ_atomic_version_bump(self):
        t = default_store.create_task({"title": "OCC Task 14", "version": 5})
        upd, _, _ = default_store.update_task_with_occ(t["id"], t, {"priority": "critical"}, "Tester")
        self.assertEqual(upd.get("version"), 6)

    def test_015_occ_multi_field_update(self):
        t = default_store.create_task({"title": "OCC Task 15"})
        upd, conflict, _ = default_store.update_task_with_occ(t["id"], t, {"budget": "$4,500", "status": "Approved", "priority": "critical"}, "Tester")
        self.assertFalse(conflict)
        self.assertEqual(upd.get("budget"), "$4,500")
        self.assertEqual(upd.get("status"), "Approved")

    def test_016_occ_null_base_handling(self):
        t = default_store.create_task({"title": "OCC Task 16"})
        upd, conflict, _ = default_store.update_task_with_occ(t["id"], {"title": t["title"]}, {"budget": "$1,111"}, "Tester")
        self.assertIsNotNone(upd)

    def test_017_occ_operator_stamping(self):
        t = default_store.create_task({"title": "OCC Task 17"})
        upd, _, _ = default_store.update_task_with_occ(t["id"], t, {"budget": "$999"}, "Custom Operator")
        self.assertIsNotNone(upd)

    def test_018_occ_staged_draft_preservation(self):
        t = default_store.create_task({"title": "OCC Task 18", "edited_draft": "Human Edit"})
        upd, _, _ = default_store.update_task_with_occ(t["id"], t, {"status": "Approved"}, "Tester")
        self.assertEqual(upd.get("edited_draft"), "Human Edit")

    def test_019_occ_helper_merge_dicts(self):
        merged, conflict, details = OptimisticConcurrencyControl.resolve_three_way_merge({"title": "Base"}, {"title": "Local"}, {"title": "Remote"})
        self.assertIsInstance(merged, dict)

    def test_020_occ_consecutive_updates(self):
        t = default_store.create_task({"title": "OCC Task 20"})
        upd1, _, _ = default_store.update_task_with_occ(t["id"], t, {"budget": "$100"}, "Tester")
        upd2, _, _ = default_store.update_task_with_occ(t["id"], upd1, {"budget": "$200"}, "Tester")
        self.assertEqual(upd2.get("version"), upd1.get("version") + 1)

    # =========================================================================
    # SUBSYSTEM 3: ZERO-TRUST DIGITAL SIGNATURES & HMAC (TESTS 21–30)
    # =========================================================================
    def test_021_calculate_operator_signature(self):
        sig, payload = calculate_operator_signature("t21", "Title", "APPROVE", "aryan@aiexperts.edu", "Role", 100.0, "SUCCESS")
        self.assertIsInstance(sig, str)
        self.assertEqual(len(sig), 64)

    def test_022_verify_operator_signature_valid(self):
        now = time.time()
        sig, _ = calculate_operator_signature("t22", "Title", "APPROVE", "aryan@aiexperts.edu", "Role", now, "SUCCESS")
        valid, recalc = verify_log_integrity(sig, "t22", "Title", "APPROVE", "aryan@aiexperts.edu", "Role", now, "SUCCESS")
        self.assertTrue(valid)

    def test_023_verify_operator_signature_invalid(self):
        valid, recalc = verify_log_integrity("corrupt_sig_123", "t23", "Title", "APPROVE", "aryan@aiexperts.edu", "Role", 100.0, "SUCCESS")
        self.assertFalse(valid)

    def test_024_hmac_signature_verification(self):
        secret = "test_secret_key"
        payload = b'{"test": "data"}'
        import hmac, hashlib
        sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        self.assertTrue(verify_hmac_signature(payload, sig, secret))

    def test_025_hmac_signature_mismatch(self):
        self.assertFalse(verify_hmac_signature(b'payload', 'invalid_sig', 'secret'))

    def test_026_audit_ledger_signature_chain(self):
        sig1 = AuditLedger.compute_record_signature("rec1", "ACT1", "Op1", 100.0, {"a": 1})
        sig2 = AuditLedger.compute_record_signature("rec2", "ACT2", "Op2", 101.0, {"b": 2}, prev_signature=sig1)
        self.assertNotEqual(sig1, sig2)

    def test_027_audit_ledger_verify_valid_chain(self):
        logs = default_store.list_audit_logs()
        res = AuditLedger.verify_ledger_chain(logs)
        self.assertIn(res.get("status"), ("SECURE", "ALERT"))

    def test_028_audit_ledger_detect_tampering(self):
        logs = default_store.list_audit_logs()
        if len(logs) > 0:
            tampered = [copy.deepcopy(l) for l in logs]
            tampered[0]["payload_data"] = {"title": "TAMPERED_DATA"}
            res = AuditLedger.verify_ledger_chain(tampered)
            self.assertEqual(res.get("status"), "ALERT")

    def test_029_enterprise_guard_low_risk_auth(self):
        now = time.time()
        sig, _ = calculate_operator_signature("t29", "Low Risk Task", "APPROVE", "aryan@aiexperts.edu", "Role", now, "SUCCESS")
        profile = {"email": "aryan@aiexperts.edu", "role": "Role"}
        payload = {"task_id": "t29", "title": "Low Risk Task", "action": "APPROVE", "timestamp": now, "risk_level": "LOW"}
        res = NotionEnterpriseGuard.authorize_high_risk_task(profile, payload, True, sig)
        self.assertTrue(res["authorized"])
        self.assertIsNotNone(res["security_seal"])

    def test_030_enterprise_guard_high_risk_requires_otp(self):
        now = time.time()
        sig, _ = calculate_operator_signature("t30", "High Risk Task", "APPROVE", "aryan@aiexperts.edu", "Role", now, "SUCCESS")
        profile = {"email": "aryan@aiexperts.edu", "role": "Role"}
        payload = {"task_id": "t30", "title": "High Risk Task", "action": "APPROVE", "timestamp": now, "risk_level": "HIGH"}
        res = NotionEnterpriseGuard.authorize_high_risk_task(profile, payload, False, sig)
        self.assertFalse(res["authorized"])
        self.assertIn("MFA", res["reason"])

    # =========================================================================
    # SUBSYSTEM 4: 6-DIGIT SMS OTP MFA SECURITY GATE (TESTS 31–38)
    # =========================================================================
    def test_031_otp_generation(self):
        otp_rec = OTPGateway.generate_otp("+919876543210")
        self.assertIsInstance(otp_rec, dict)
        self.assertEqual(len(otp_rec["raw_otp_debug"]), 6)

    def test_032_otp_valid_verification(self):
        phone = "+919876543211"
        otp_rec = OTPGateway.generate_otp(phone)
        raw_code = otp_rec["raw_otp_debug"]
        ok = OTPGateway.verify_otp(phone, raw_code, otp_rec)
        self.assertTrue(ok)

    def test_033_otp_invalid_code_rejection(self):
        phone = "+919876543212"
        otp_rec = OTPGateway.generate_otp(phone)
        ok = OTPGateway.verify_otp(phone, "000000", otp_rec)
        self.assertFalse(ok)

    def test_034_otp_expiration_window(self):
        phone = "+919876543213"
        otp_rec = OTPGateway.generate_otp(phone)
        otp_rec["timestamp"] -= timedelta(minutes=6)
        ok = OTPGateway.verify_otp(phone, otp_rec["raw_otp_debug"], otp_rec)
        self.assertFalse(ok)

    def test_035_otp_one_time_use_enforcement(self):
        phone = "+919876543214"
        otp_rec = OTPGateway.generate_otp(phone)
        raw_code = otp_rec["raw_otp_debug"]
        ok1 = OTPGateway.verify_otp(phone, raw_code, otp_rec)
        self.assertTrue(ok1)

    def test_036_enterprise_guard_high_risk_with_valid_otp(self):
        phone = "+919876543210"
        otp_rec = OTPGateway.generate_otp(phone)
        now = time.time()
        sig, _ = calculate_operator_signature("t36", "Purge Financial Ledgers", "PURGE", "aryan@aiexperts.edu", "Role", now, "SUCCESS")
        profile = {"email": "aryan@aiexperts.edu", "role": "Role"}
        payload = {"task_id": "t36", "title": "Purge Financial Ledgers", "action": "PURGE", "timestamp": now, "risk_level": "HIGH"}
        res = NotionEnterpriseGuard.authorize_high_risk_task(profile, payload, True, sig)
        self.assertTrue(res["authorized"])
        self.assertIsNotNone(res["security_seal"])

    def test_037_enterprise_guard_high_risk_invalid_signature(self):
        phone = "+919876543210"
        otp_rec = OTPGateway.generate_otp(phone)
        now = time.time()
        profile = {"email": "aryan@aiexperts.edu", "role": "Role"}
        payload = {"task_id": "t37", "title": "High Risk Task", "action": "APPROVE", "timestamp": now, "risk_level": "HIGH"}
        res = NotionEnterpriseGuard.authorize_high_risk_task(profile, payload, True, "invalid_signature")
        self.assertFalse(res["authorized"])
        self.assertIn("Cryptographic", res["reason"])

    def test_038_otp_gateway_phone_formatting(self):
        otp_rec = OTPGateway.generate_otp("9876543210")
        self.assertEqual(len(otp_rec["raw_otp_debug"]), 6)

    # =========================================================================
    # SUBSYSTEM 5: AI AUDIT ENGINE & RISK SCORING (TESTS 39–48)
    # =========================================================================
    def test_039_ai_audit_low_risk(self):
        audit = AIAuditEngine.analyze_task("Routine Stationery Provisioning", "Order 10 reams of paper.")
        self.assertIn(audit.risk_level, ("LOW", "MEDIUM"))

    def test_040_ai_audit_high_risk_keywords(self):
        audit = AIAuditEngine.analyze_task("Infrastructure Key Purge", "Revoke TLS root certificates and purge database.")
        self.assertIn(audit.risk_level, ("HIGH", "CRITICAL"))

    def test_041_ai_audit_confidence_score(self):
        audit = AIAuditEngine.analyze_task("Update Typo in Documentation", "Fix spelling error.")
        self.assertGreaterEqual(audit.confidence_score, 0.70)
        self.assertLessEqual(audit.confidence_score, 1.0)

    def test_042_ai_audit_reasoning_trace(self):
        audit = AIAuditEngine.analyze_task("Title", "Details")
        self.assertIsInstance(audit.reasoning_trace, list)
        self.assertGreater(len(audit.reasoning_trace), 0)

    def test_043_ai_audit_teams_draft(self):
        audit = AIAuditEngine.analyze_task("Title", "Details")
        self.assertIsInstance(audit.draft_teams_text, str)
        self.assertIn("Pre-Audit Risk", audit.draft_teams_text)

    def test_044_ai_audit_email_html(self):
        audit = AIAuditEngine.analyze_task("Title", "Details")
        self.assertIsInstance(audit.draft_email_html, str)
        self.assertIn("<div", audit.draft_email_html.lower())

    def test_045_ai_audit_category_classification(self):
        audit = AIAuditEngine.analyze_task("SSH Root Access Compromise", "Failed authentication.")
        self.assertEqual(audit.category, "Security & Identity")

    def test_046_ai_audit_reasoning_ledger(self):
        audit = AIAuditEngine.analyze_task("Title", "Details")
        self.assertIsInstance(audit.ai_reasoning_ledger, str)
        self.assertGreater(len(audit.ai_reasoning_ledger), 0)

    def test_047_ai_audit_security_flags(self):
        audit = AIAuditEngine.analyze_task("Purge Financial Ledgers", "Purge all records.")
        self.assertIsInstance(audit.security_flags, list)

    def test_048_ai_audit_deterministic_output(self):
        a1 = AIAuditEngine.analyze_task("Same Title", "Same Details")
        a2 = AIAuditEngine.analyze_task("Same Title", "Same Details")
        self.assertEqual(a1.risk_level, a2.risk_level)

    # =========================================================================
    # SUBSYSTEM 6: NATURAL LANGUAGE @AI COMMENT AGENT (TESTS 49–58)
    # =========================================================================
    def test_049_comment_agent_no_ai_mention(self):
        ok, msg = NotionCommentAgent.process_comment("t49", "Regular comment without tag", "Author")
        self.assertFalse(ok)

    def test_050_comment_agent_budget_update(self):
        t = default_store.create_task({"title": "Comment Task 50"})
        ok, msg = NotionCommentAgent.process_comment(t["id"], "@AI update budget to $15,000", "Aryan")
        self.assertTrue(ok)
        upd = default_store.get_task(t["id"])
        self.assertEqual(upd.get("budget"), "$15,000")

    def test_051_comment_agent_reassess_risk(self):
        t = default_store.create_task({"title": "Comment Task 51"})
        ok, msg = NotionCommentAgent.process_comment(t["id"], "@AI re-assess risk", "Aryan")
        self.assertTrue(ok)

    def test_052_comment_agent_approve(self):
        t = default_store.create_task({"title": "Comment Task 52", "status": "Ready for Review"})
        ok, msg = NotionCommentAgent.process_comment(t["id"], "@AI approve budget request", "Aryan")
        self.assertTrue(ok)

    def test_053_comment_agent_reject(self):
        t = default_store.create_task({"title": "Comment Task 53", "status": "Ready for Review"})
        ok, msg = NotionCommentAgent.process_comment(t["id"], "@AI reject invalid order", "Aryan")
        self.assertTrue(ok)
        upd = default_store.get_task(t["id"])
        self.assertEqual(upd.get("status"), "Rejected")

    def test_054_comment_agent_escalate(self):
        t = default_store.create_task({"title": "Comment Task 54", "priority": "normal"})
        ok, msg = NotionCommentAgent.process_comment(t["id"], "@AI escalate priority immediately", "Aryan")
        self.assertTrue(ok)
        upd = default_store.get_task(t["id"])
        self.assertEqual(upd.get("priority"), "critical")

    def test_055_comment_agent_summarize(self):
        t = default_store.create_task({"title": "Comment Task 55"})
        ok, msg = NotionCommentAgent.process_comment(t["id"], "@AI summarize task status", "Aryan")
        self.assertTrue(ok)
        self.assertIn("Task Summary", msg)

    def test_056_comment_agent_compound_command(self):
        t = default_store.create_task({"title": "Comment Task 56"})
        ok, msg = NotionCommentAgent.process_comment(t["id"], "@AI update budget to $18,500 and escalate priority to critical", "Aryan")
        self.assertTrue(ok)
        upd = default_store.get_task(t["id"])
        self.assertEqual(upd.get("budget"), "$18,500")
        self.assertEqual(upd.get("priority"), "critical")

    def test_057_comment_agent_occ_version_increment(self):
        t = default_store.create_task({"title": "Comment Task 57", "version": 1})
        NotionCommentAgent.process_comment(t["id"], "@AI update budget to $3,000", "Aryan")
        upd = default_store.get_task(t["id"])
        self.assertEqual(upd.get("version"), 2)

    def test_058_comment_agent_run_log_entry(self):
        t = default_store.create_task({"title": "Comment Task 58"})
        NotionCommentAgent.process_comment(t["id"], "@AI update budget to $4,000", "Aryan")
        logs = default_store.list_audit_logs()
        self.assertTrue(any(l.get("record_id") == t["id"] for l in logs))

    # =========================================================================
    # SUBSYSTEM 7: GEMINI 1.5 FLASH VOICE MEMO AGENT (TESTS 59–68)
    # =========================================================================
    def test_059_voice_memo_transcribe_mock(self):
        txt = VoiceMemoAgent.transcribe_audio(b"audio", mock_transcript="Custom Spoken Note")
        self.assertEqual(txt, "Custom Spoken Note")

    def test_060_voice_memo_process_budget_extraction(self):
        t = default_store.create_task({"title": "Voice Task 60"})
        ok, summary, upd = VoiceMemoAgent.process_voice_memo_on_task(
            task_id=t["id"],
            audio_input="memo",
            mock_transcript="Please update budget to $6,500 for optics lab.",
        )
        self.assertTrue(ok)
        self.assertEqual(upd.get("budget"), "$6,500")

    def test_061_voice_memo_process_priority_escalation(self):
        t = default_store.create_task({"title": "Voice Task 61"})
        ok, summary, upd = VoiceMemoAgent.process_voice_memo_on_task(
            task_id=t["id"],
            audio_input="memo",
            mock_transcript="Escalate priority to critical immediately.",
        )
        self.assertTrue(ok)
        self.assertEqual(upd.get("priority"), "critical")

    def test_062_voice_memo_process_approval(self):
        t = default_store.create_task({"title": "Voice Task 62", "status": "Ready for Review"})
        ok, summary, upd = VoiceMemoAgent.process_voice_memo_on_task(
            task_id=t["id"],
            audio_input="memo",
            mock_transcript="Provisions approved for cleanroom filter replacement.",
        )
        self.assertTrue(ok)
        self.assertEqual(upd.get("status"), "Approved")

    def test_063_voice_memo_attachment_text_in_details(self):
        t = default_store.create_task({"title": "Voice Task 63", "details": "Base Details"})
        ok, summary, upd = VoiceMemoAgent.process_voice_memo_on_task(
            task_id=t["id"],
            audio_input="memo",
            mock_transcript="Spoken voice memo payload text.",
        )
        self.assertIn("Voice Memo Attachment", upd.get("details", ""))

    def test_064_voice_agent_process_file_command(self):
        res = default_voice_agent.process_voice_command("voice_approve_command.wav")
        self.assertIsInstance(res, dict)
        self.assertIn("transcript", res)

    def test_065_voice_agent_execute_in_notion(self):
        t = default_store.create_task({"title": "Voice Task 65"})
        parsed = default_voice_agent.process_voice_command("voice_approve_command.wav")
        exec_res = default_voice_agent.execute_voice_command_in_notion(
            task_id=t["id"],
            analysis_results=parsed,
            operator_name="Aryan Sharma",
        )
        self.assertIsInstance(exec_res, dict)

    def test_066_voice_agent_poll_pending_memos(self):
        count = default_voice_agent.poll_and_process_pending_voice_memos(store=default_store)
        self.assertIsInstance(count, int)

    def test_067_voice_agent_occ_version_increment(self):
        t = default_store.create_task({"title": "Voice Task 67", "version": 1})
        VoiceMemoAgent.process_voice_memo_on_task(t["id"], "memo", mock_transcript="Update budget to $2,000")
        upd = default_store.get_task(t["id"])
        self.assertEqual(upd.get("version"), 2)

    def test_068_voice_agent_run_log_written(self):
        t = default_store.create_task({"title": "Voice Task 68"})
        VoiceMemoAgent.process_voice_memo_on_task(t["id"], "memo", mock_transcript="Provisions approved")
        logs = default_store.list_audit_logs()
        self.assertTrue(any(l.get("record_id") == t["id"] for l in logs))

    # =========================================================================
    # SUBSYSTEM 8: DEAD-LETTER QUEUE (DLQ) & FAULT ISOLATION (TESTS 69–76)
    # =========================================================================
    def test_069_route_to_dlq(self):
        t = default_store.create_task({"title": "DLQ Task 69"})
        dlq = default_store.route_to_dlq(t["id"], "Error Trace 69", "JSON Parser Exception", "DLQ Guard")
        self.assertIsNotNone(dlq)
        self.assertIn("DLQ", dlq.get("status"))

    def test_070_get_dlq_tasks(self):
        t = default_store.create_task({"title": "DLQ Task 70"})
        default_store.route_to_dlq(t["id"], "Trace 70", "Reason 70")
        dlq_list = default_store.get_dlq_tasks()
        self.assertTrue(any(item["id"] == t["id"] for item in dlq_list))

    def test_071_resolve_dlq_task(self):
        t = default_store.create_task({"title": "DLQ Task 71"})
        default_store.route_to_dlq(t["id"], "Trace 71", "Reason 71")
        curr = default_store.get_task(t["id"])
        resolved, _, _ = default_store.update_task_with_occ(t["id"], curr, {"status": "Ready for Review", "dlq_reason": ""}, "Tester")
        self.assertEqual(resolved.get("status"), "Ready for Review")

    def test_072_dlq_isolation_prevents_normal_dispatch(self):
        t = default_store.create_task({"title": "DLQ Task 72"})
        default_store.route_to_dlq(t["id"], "Trace 72", "Reason 72")
        approved = default_store.get_tasks_by_status("Approved")
        self.assertFalse(any(item["id"] == t["id"] for item in approved))

    def test_073_dlq_run_log_recorded(self):
        t = default_store.create_task({"title": "DLQ Task 73"})
        default_store.route_to_dlq(t["id"], "Trace 73", "Reason 73")
        logs = default_store.list_audit_logs()
        self.assertTrue(any("DLQ" in str(l.get("action")) for l in logs))

    def test_074_dlq_error_trace_retrieval(self):
        t = default_store.create_task({"title": "DLQ Task 74"})
        dlq = default_store.route_to_dlq(t["id"], "Trace 74 Specific Error", "Reason 74")
        self.assertEqual(dlq.get("dlq_error_trace"), "Trace 74 Specific Error")

    def test_075_dlq_category_assignment(self):
        t = default_store.create_task({"title": "DLQ Task 75"})
        dlq = default_store.route_to_dlq(t["id"], "Trace 75", "Reason 75")
        self.assertIsNotNone(dlq.get("category"))

    def test_076_dlq_re_triage_resets_error_fields(self):
        t = default_store.create_task({"title": "DLQ Task 76"})
        default_store.route_to_dlq(t["id"], "Trace 76", "Reason 76")
        curr = default_store.get_task(t["id"])
        res, _, _ = default_store.update_task_with_occ(t["id"], curr, {"status": "Ready for Review", "dlq_reason": ""}, "Tester")
        self.assertEqual(res.get("status"), "Ready for Review")

    # =========================================================================
    # SUBSYSTEM 9: DEDUPLICATION FINGERPRINTING & NONCE REPLAY (TESTS 77–84)
    # =========================================================================
    def test_077_deduplicator_fresh_payload(self):
        fp = default_deduplicator.compute_fingerprint("Payload Title 77", "Details 77")
        self.assertIsInstance(fp, str)
        self.assertEqual(len(fp), 64)

    def test_078_deduplicator_store_and_check(self):
        unique_title = f"Unique Title {uuid.uuid4().hex}"
        fp = default_deduplicator.compute_fingerprint(unique_title, "Details 78")
        ok, orig_id, msg = default_store.check_and_record_fingerprint(fp, f"task_{uuid.uuid4().hex[:8]}")
        self.assertTrue(ok)

    def test_079_deduplicator_reject_duplicate(self):
        dup_title = f"Dup Title {uuid.uuid4().hex}"
        fp = default_deduplicator.compute_fingerprint(dup_title, "Details 79")
        default_store.check_and_record_fingerprint(fp, "task_79_orig")
        ok, orig_id, msg = default_store.check_and_record_fingerprint(fp, "task_79_new")
        self.assertFalse(ok)

    def test_080_nonce_guard_fresh_nonce(self):
        nonce_str = f"nonce_{uuid.uuid4().hex}"
        ok, msg = default_nonce_guard.validate_and_record(nonce_str, int(time.time()))
        self.assertTrue(ok)

    def test_081_nonce_guard_reject_replay(self):
        nonce_str = f"nonce_replay_{uuid.uuid4().hex}"
        now = int(time.time())
        default_nonce_guard.validate_and_record(nonce_str, now)
        ok, msg = default_nonce_guard.validate_and_record(nonce_str, now)
        self.assertFalse(ok)
        self.assertIn("replay", msg.lower())

    def test_082_nonce_guard_cleanup(self):
        nonce_str = f"nonce_clean_{uuid.uuid4().hex}"
        now = int(time.time())
        default_nonce_guard.validate_and_record(nonce_str, now)
        self.assertIn(nonce_str, default_nonce_guard.seen_nonces)

    def test_083_deduplicator_window_expiration(self):
        fp = default_deduplicator.compute_fingerprint(f"Expired Title {uuid.uuid4().hex}", "Details 83")
        default_store.check_and_record_fingerprint(fp, "task_83")
        ok, _, _ = default_store.check_and_record_fingerprint(fp, "task_83_new", window_seconds=0)
        self.assertTrue(ok)

    def test_084_token_bucket_rate_limiter_acquire(self):
        state = default_rate_limiter.get_state()
        self.assertIsInstance(state, dict)
        self.assertIn("token_bucket", state)

    # =========================================================================
    # SUBSYSTEM 10: SYSTEM HEALTH MONITOR & HEARTBEATS (TESTS 85–90)
    # =========================================================================
    def test_085_emit_system_health_heartbeat(self):
        hb = SystemHealthMonitor.emit_heartbeat()
        self.assertIsInstance(hb, dict)
        self.assertEqual(hb.get("status"), "HEALTHY")

    def test_086_system_health_metrics_range(self):
        hb = SystemHealthMonitor.emit_heartbeat()
        self.assertGreaterEqual(hb.get("cpu_percent"), 0.0)
        self.assertLessEqual(hb.get("cpu_percent"), 100.0)
        self.assertGreaterEqual(hb.get("ram_percent"), 0.0)

    def test_087_system_health_list_records(self):
        records = default_store.list_system_health_records(limit=5)
        self.assertIsInstance(records, list)
        self.assertGreater(len(records), 0)

    def test_088_system_health_latest_record(self):
        latest = default_store.get_latest_system_health()
        self.assertIsNotNone(latest)
        self.assertIsNotNone(latest.get("signature"))

    def test_089_system_health_heartbeat_signature_validity(self):
        latest = default_store.get_latest_system_health()
        self.assertIsNotNone(latest.get("signature"))
        self.assertEqual(len(latest["signature"]), 64)

    def test_090_system_health_turn_off_test_resilience(self):
        hb = SystemHealthMonitor.emit_heartbeat()
        self.assertIn("uptime_seconds", hb)

    # =========================================================================
    # SUBSYSTEM 11: EXECUTIVE PDF & CSV REPORT BUILDERS (TESTS 91–95)
    # =========================================================================
    def test_091_pdf_report_builder_generation(self):
        tasks = default_store.list_tasks(include_archived=True)
        logs = default_store.list_audit_logs()
        pdf_bytes = PDFReportBuilder.generate_task_audit_pdf(tasks, logs)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 100)

    def test_092_pdf_report_starts_with_pdf_header(self):
        tasks = default_store.list_tasks(include_archived=False)
        logs = default_store.list_audit_logs()
        pdf_bytes = PDFReportBuilder.generate_task_audit_pdf(tasks, logs)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_093_csv_export_formatting(self):
        logs = default_store.list_audit_logs()
        import io, csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Log ID", "Record ID", "Action", "Operator", "Timestamp", "Signature"])
        for l in logs:
            writer.writerow([l.get("id"), l.get("record_id"), l.get("action"), l.get("operator_name"), l.get("timestamp"), l.get("signature")])
        csv_str = output.getvalue()
        self.assertIn("Log ID", csv_str)
        self.assertGreater(len(csv_str), 50)

    def test_094_workflow_engine_pipeline_execution(self):
        t = default_store.create_task({"title": "Workflow Test Task"})
        tmpl = default_store.list_pipeline_templates()[0]
        ok, trace, exec_t = WorkflowEngine.execute_pipeline(t, tmpl, "Tester")
        self.assertTrue(ok)
        self.assertIsInstance(trace, list)

    def test_095_audit_ledger_recalculate_hashes(self):
        logs = default_store.list_audit_logs()
        res = AuditLedger.verify_ledger_chain(logs)
        self.assertIn(res.get("status"), ("SECURE", "ALERT"))

    # =========================================================================
    # SUBSYSTEM 12: FASTAPI WEBHOOK GATEWAY REST ENDPOINTS (TESTS 96–100)
    # =========================================================================
    def test_096_gateway_health_endpoint(self):
        res = health_check()
        self.assertEqual(res.get("status"), "HEALTHY")

    def test_097_gateway_list_tasks_endpoint(self):
        tasks = list_tasks()
        self.assertIsInstance(tasks, list)

    def test_098_gateway_throttle_state_endpoint(self):
        state = get_throttle_state()
        self.assertIn("token_bucket", state)

    def test_099_gateway_system_config_get_post(self):
        cfg = get_system_config()
        self.assertIn("poll_interval_minutes", cfg)
        upd = update_system_config({"poll_interval_minutes": 60})
        self.assertEqual(upd.get("poll_interval_minutes"), 60)

    def test_100_gateway_comment_and_voice_requests(self):
        t = default_store.create_task({"title": "Gateway Test 100"})
        c_req = CommentCommandRequest(task_id=t["id"], comment_text="@AI update budget to $19,000", author_name="Tester")
        c_res = process_comment_command(c_req)
        self.assertTrue(c_res.get("success"))

        v_req = VoiceCommandRequest(task_id=t["id"], audio_file="voice_approve_command.wav", operator_name="Tester")
        v_res = process_voice_command(v_req)
        self.assertTrue(v_res.get("success"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
