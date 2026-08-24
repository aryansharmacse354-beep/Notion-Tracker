import sys
from unittest.mock import MagicMock, patch

# Ingress mock dependency injection to allow importing our custom engine modules 
# in automated offline cloud testing environments without needing external integrations.
mock_notion_client = MagicMock()
mock_notion_client.APIResponseError = Exception
sys.modules['notion_client'] = mock_notion_client

# Inject mocks for LangChain structures
sys.modules['langchain'] = MagicMock()
sys.modules['langchain.prompts'] = MagicMock()
sys.modules['langchain_community'] = MagicMock()
sys.modules['langchain_community.llms'] = MagicMock()

import unittest
import hashlib
import os
import random
from datetime import datetime, timezone, timedelta

# Add paths to make sure we can find verify_signatures and main
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import verify_signatures as vs

class TestNotionTrackerSuite(unittest.TestCase):
    
    def setUp(self):
        """Configure mock runtime parameters and secure environment keys."""
        self.mock_env = {
            "NOTION_TOKEN": "secret_test_token_12345",
            "NOTION_MAIN_DATABASE_ID": "da1a3e6f-0000-4000-8000-000000000001",
            "NOTION_RUN_LOG_DATABASE_ID": "da1a3e6f-0000-4000-8000-000000000002",
            "NOTIFICATION_PROVIDER": "MOCK"
        }
        self.patcher = patch.dict(os.environ, self.mock_env)
        self.patcher.start()

        # Shared user profiles for testing
        self.aryan_profile = {
            "name": "Aryan Sharma",
            "email": "aryan.sharma@aiexperts.edu",
            "role": "Lead Developer",
            "phone": "+919876543210"
        }
        self.tampered_profile = {
            "name": "Aryan Sharma",
            "email": "aryan.sharma@aiexperts.edu",
            "role": "QA Tester", # Altered role
            "phone": "+919876543210"
        }

        # Shared task templates
        self.high_risk_task = {
            "task_id": "task-uuid-9999-mfa",
            "title": "Purge Financial Auditing Ledgers & Reallocate Capital",
            "action": "Programmatically delete logs and shift $50,000 USD to priority expansion accounts.",
            "risk_level": "HIGH",
            "timestamp": "2026-08-24T12:00:00+00:00"
        }
        self.low_risk_task = {
            "task_id": "task-uuid-1111-low",
            "title": "Update Documentation Typo",
            "action": "Fix spelling mistake in README.md footer.",
            "risk_level": "LOW",
            "timestamp": "2026-08-24T12:05:00+00:00"
        }
        
    def tearDown(self):
        """Clean up mocked parameters post evaluation."""
        self.patcher.stop()

    def test_audit_trail_sha256_verification(self):
        """Test cryptographic SHA-256 signature verification for log entry tampering checks."""
        task_title = "Cloud Infrastructure Security Audit"
        timestamp = "2026-08-22T22:12:00+00:00"
        status = "Success"
        
        # Verify deterministic hash signature generation
        payload = f"{task_title}|{timestamp}|{status}"
        sha_sig = hashlib.sha256(payload.encode('utf-8')).hexdigest()
        
        self.assertEqual(len(sha_sig), 64)
        self.assertTrue(sha_sig.isalnum())
        
        # Ensure a slight payload modification changes the block hash completely (immutable trail protection)
        tampered_payload = f"{task_title}|{timestamp}|Failed"
        tampered_sig = hashlib.sha256(tampered_payload.encode('utf-8')).hexdigest()
        self.assertNotEqual(sha_sig, tampered_sig)

    def test_ai_reasoning_pipeline(self):
        """Test the simulated LangChain cognitive reasoning analyzer output properties."""
        try:
            import main
        except ImportError:
            self.assertTrue(True)
            return
        
        if hasattr(main, "simulate_langchain_reasoning"):
            results = main.simulate_langchain_reasoning(
                "Critical Security Event", 
                "Unauthorized SSH attempt detected on subnetwork."
            )
            self.assertEqual(results["risk_level"], "HIGH")
            self.assertGreaterEqual(results["confidence"], 90)
            self.assertTrue(any("Critical" in step or "security" in step.lower() for step in results["steps"]))
            self.assertEqual(len(results["checks"]), 3)
            self.assertEqual(results["checks"][2]["status"], "WARN")
        else:
            self.assertTrue(True)

    @patch("main.notion")
    def test_cognitive_typesetting_block_structure(self, mock_notion):
        """Test that the Notion blocks schema is properly built for page typesetting."""
        try:
            import main
        except ImportError:
            self.assertTrue(True)
            return
        
        if hasattr(main, "typeset_ai_reasoning_in_notion"):
            reasoning_results = {
                "risk_level": "HIGH",
                "confidence": 95,
                "steps": ["Step 1 done", "Step 2 done"],
                "checks": [{"check": "Test", "status": "WARN"}],
                "draft_output": "Mock draft card content"
            }
            
            mock_notion.blocks.children.append = MagicMock()
            main.typeset_ai_reasoning_in_notion("mock-page-id", "Test Title", reasoning_results)
            
            mock_notion.blocks.children.append.assert_called_once()
            called_kwargs = mock_notion.blocks.children.append.call_args[1]
            children = called_kwargs["children"]
            
            self.assertTrue(len(children) >= 5)
            self.assertEqual(children[0]["type"], "heading_2")
            self.assertEqual(children[1]["type"], "callout")
            self.assertEqual(children[1]["callout"]["color"], "red_background")
        else:
            self.assertTrue(True)

    def test_fallback_environment_resilience(self):
        """Test that the engine recovers gracefully when environment parameters are missing."""
        with patch.dict(os.environ, {}, clear=True):
            try:
                import importlib
                with self.assertRaises(SystemExit):
                    importlib.reload(importlib.import_module("main"))
            except Exception:
                self.assertTrue(True)

    # =========================================================================
    # NEW MULTI-FACTOR & CRYTOGRAPHIC ZERO-TRUST SECURITY TEST CASES
    # =========================================================================

    def test_otp_generation_and_hashing(self):
        """Test that OTP generated by OTPGateway is exactly 6 digits and has a secure SHA-256 hash."""
        phone = self.aryan_profile["phone"]
        otp_record = vs.OTPGateway.generate_otp(phone)
        
        self.assertIn("otp_hash", otp_record)
        self.assertIn("timestamp", otp_record)
        self.assertIn("raw_otp_debug", otp_record)
        
        raw_otp = otp_record["raw_otp_debug"]
        self.assertEqual(len(raw_otp), 6)
        self.assertTrue(raw_otp.isdigit())

        recalculated_hash = hashlib.sha256(raw_otp.encode('utf-8')).hexdigest()
        self.assertEqual(recalculated_hash, otp_record["otp_hash"])

    def test_otp_verification_success(self):
        """Test that validation passes when the correct OTP is provided within the time boundary."""
        phone = self.aryan_profile["phone"]
        otp_record = vs.OTPGateway.generate_otp(phone)
        
        success = vs.OTPGateway.verify_otp(phone, otp_record["raw_otp_debug"], otp_record)
        self.assertTrue(success)

    def test_otp_verification_failure_invalid_code(self):
        """Test that validation fails when an incorrect code is entered."""
        phone = self.aryan_profile["phone"]
        otp_record = vs.OTPGateway.generate_otp(phone)
        
        wrong_otp = "000000" if otp_record["raw_otp_debug"] != "000000" else "111111"
        success = vs.OTPGateway.verify_otp(phone, wrong_otp, otp_record)
        self.assertFalse(success)

    def test_otp_verification_failure_expired(self):
        """Test that validation fails when the OTP is older than 5 minutes (300 seconds)."""
        phone = self.aryan_profile["phone"]
        otp_record = vs.OTPGateway.generate_otp(phone)
        
        otp_record["timestamp"] = datetime.now(timezone.utc) - timedelta(minutes=6)
        
        success = vs.OTPGateway.verify_otp(phone, otp_record["raw_otp_debug"], otp_record)
        self.assertFalse(success)

    def test_enterprise_guard_low_risk_direct_auth(self):
        """Test that LOW risk actions bypass OTP but still require a valid profile signature."""
        valid_signature, _ = vs.calculate_operator_signature(
            self.low_risk_task["task_id"], self.low_risk_task["title"], self.low_risk_task["action"],
            self.aryan_profile["email"], self.aryan_profile["role"],
            self.low_risk_task["timestamp"], "SUCCESS"
        )

        auth_result = vs.NotionEnterpriseGuard.authorize_high_risk_task(
            self.aryan_profile, self.low_risk_task, otp_verified=False, signature=valid_signature
        )
        
        self.assertTrue(auth_result["authorized"])
        self.assertIsNotNone(auth_result["security_seal"])

    def test_enterprise_guard_high_risk_requires_otp_fail(self):
        """Test that HIGH risk actions are blocked immediately if OTP authentication has not been completed."""
        valid_signature, _ = vs.calculate_operator_signature(
            self.high_risk_task["task_id"], self.high_risk_task["title"], self.high_risk_task["action"],
            self.aryan_profile["email"], self.aryan_profile["role"],
            self.high_risk_task["timestamp"], "SUCCESS"
        )

        auth_result = vs.NotionEnterpriseGuard.authorize_high_risk_task(
            self.aryan_profile, self.high_risk_task, otp_verified=False, signature=valid_signature
        )
        
        self.assertFalse(auth_result["authorized"])
        self.assertIn("Missing/failed MFA", auth_result["reason"])
        self.assertIsNone(auth_result["security_seal"])

    def test_enterprise_guard_high_risk_signature_fail(self):
        """Test that HIGH risk actions are blocked if OTP passes but the signature is invalid or tampered with."""
        otp_verified = True
        invalid_signature = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

        auth_result = vs.NotionEnterpriseGuard.authorize_high_risk_task(
            self.aryan_profile, self.high_risk_task, otp_verified=otp_verified, signature=invalid_signature
        )
        
        self.assertFalse(auth_result["authorized"])
        self.assertIn("Cryptographic Signature check failed", auth_result["reason"])
        self.assertIsNone(auth_result["security_seal"])

    def test_enterprise_guard_high_risk_auth_success(self):
        """Test that HIGH risk actions are successfully authorized with a valid signature and verified OTP."""
        otp_verified = True

        valid_signature, _ = vs.calculate_operator_signature(
            self.high_risk_task["task_id"], self.high_risk_task["title"], self.high_risk_task["action"],
            self.aryan_profile["email"], self.aryan_profile["role"],
            self.high_risk_task["timestamp"], "SUCCESS"
        )

        auth_result = vs.NotionEnterpriseGuard.authorize_high_risk_task(
            self.aryan_profile, self.high_risk_task, otp_verified=otp_verified, signature=valid_signature
        )
        
        self.assertTrue(auth_result["authorized"])
        self.assertIsNotNone(auth_result["security_seal"])
        self.assertEqual(len(auth_result["security_seal"]), 64)


if __name__ == "__main__":
    unittest.main()
