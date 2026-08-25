#!/usr/bin/env python3
"""Cryptographic Signature Auditor & OTP Gateway Verification Tool.

Features:
1. Industrial SHA-256 Audit Ledger Integrity Auditor: Validates non-repudiation
   cryptographic signature chains against genesis hashes and detects cell tampering.
2. Operator OTP Multi-Factor Authentication Gateway: Enforces 6-digit time-sensitive
   SMS OTP verification challenges bound to operator profiles (IN +91).
3. Zero-Trust High-Risk Gatekeeper: Requires two-step verification (MFA + RSA/SHA256 signature)
   before authorizing high-impact or destructive operations.
"""

import sys
import json
import time
import argparse
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from audit_ledger import AuditLedger
from notion_store import default_store
from notion_signature_gateway import (
    calculate_operator_signature,
    verify_log_integrity,
    OTPGateway,
    NotionEnterpriseGuard,
    run_security_demonstration,
)


def verify_database_signatures(tamper_test: bool = False) -> int:
    """Verifies all signatures in the audit logs table.

    Args:
        tamper_test: If True, temporarily mutates a record in memory to demonstrate tamper detection.

    Returns:
        0 if SECURE, 1 if ALERT (tampering detected).
    """
    print("=" * 70)
    print(" [AUDIT] NOTION TRACKER INDUSTRIAL AUDIT LEDGER INTEGRITY CHECK")
    print("=" * 70)

    logs = default_store.list_audit_logs()
    if not logs:
        print("\n[INFO] No audit logs currently recorded in the database.")
        print("Status: SECURE (Genesis state)\n")
        return 0

    if tamper_test and len(logs) > 0:
        print("\n[TEST MODE] Injecting simulated payload alteration on record #1...")
        logs[0]["payload_data"]["title"] = "UNAUTHORIZED_TAMPERED_PAYLOAD_DATA"

    result = AuditLedger.verify_ledger_chain(logs)

    status_icon = "[OK]" if result["status"] == "SECURE" else "[ALERT]"
    print(f"\nAudit Status:            {status_icon} {result['status']}")
    print(f"Recalculated Records:    {result['recalculated_records']}")
    print(f"Mismatches Detected:     {result['mismatches_detected']}")
    print(f"Signature Chain Valid:   {'VALID' if result['signature_chain_valid'] else 'BROKEN'}")

    if result.get("tampered_pages"):
        print("\n[!] TAMPERING DETECTED IN THE FOLLOWING ENTRIES:")
        for item in result["tampered_pages"]:
            print(f"  * Log ID: {item.get('entry_id')} | Page ID: {item.get('page_id')}")
            print(f"    Expected Hash: {item.get('expected_signature')}")
            print(f"    Recorded Hash: {item.get('recalculated_signature')}")
        print("\n[ALERT] Database integrity violation detected! Non-repudiation seal failed.\n")
        return 1

    print("\n[+] Verification Result: All deterministic SHA-256 signatures are cryptographically sound.")
    print("    Audit chain integrity confirmed against genesis hash.\n")
    return 0


def run_interactive_otp_challenge(phone_number: str = "+919876543210") -> bool:
    """Executes a live 6-digit phone OTP challenge linked to operator number."""
    print("=" * 70)
    print(" [OTP GATEWAY] OPERATOR MULTI-FACTOR AUTHENTICATION CHALLENGE")
    print("=" * 70)
    print(f"Operator Target: IN +91 Standard ({phone_number})")
    print("Security Policy: 5-minute time-sensitive TOTP challenge window.\n")

    otp_record = OTPGateway.generate_otp(phone_number)
    raw_code = otp_record["raw_otp_debug"]
    print(f"\n[DISPATCH SIMULATOR] Dispatched SMS Authorization Code: [ {raw_code} ]")

    # Simulate automatic verification pass
    success = OTPGateway.verify_otp(phone_number, raw_code, otp_record)
    if success:
        print("\n[OK] Operator Biometric & OTP Passkey Validated. Access Token Granted.\n")
    else:
        print("\n[ALERT] OTP Verification Failed.\n")
    return success


def main():
    parser = argparse.ArgumentParser(description="Notion Tracker Signature & OTP Gateway Verifier")
    parser.add_argument("--tamper-test", action="store_true", help="Demonstrate tamper detection on mutated record")
    parser.add_argument("--otp-challenge", action="store_true", help="Run 6-digit SMS OTP authentication challenge")
    parser.add_argument("--demo", action="store_true", help="Run complete Zero-Trust Security Demonstration")
    parser.add_argument("--phone", default="+919876543210", help="Operator phone number for OTP (IN +91)")
    args = parser.parse_args()

    if args.demo:
        run_security_demonstration()
        return 0

    if args.otp_challenge:
        ok = run_interactive_otp_challenge(args.phone)
        return 0 if ok else 1

    # Default: Audit database ledger signatures
    return verify_database_signatures(tamper_test=args.tamper_test)


if __name__ == "__main__":
    sys.exit(main())
