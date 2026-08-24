"""Cryptographic Signature Verification Tool for Notion Tracker.

Audits the industrial SHA-256 audit ledger, verifies signature validity, and checks
the integrity of the non-repudiation cryptographic hash chain.
"""

import sys
import json
from audit_ledger import AuditLedger
from notion_store import default_store
from notion_signature_gateway import (
    calculate_operator_signature,
    verify_log_integrity,
    OTPGateway,
    NotionEnterpriseGuard,
)



if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def verify_database_signatures(tamper_test: bool = False) -> int:
    """Verifies all signatures in the audit logs table.

    Args:
        tamper_test: If True, temporarily mutates a record in memory to demonstrate tamper detection.

    Returns:
        0 if SECURE, 1 if ALERT (tampering detected).
    """
    print("=" * 65)
    print(" [AUDIT] NOTION TRACKER INDUSTRIAL AUDIT LEDGER INTEGRITY CHECK")
    print("=" * 65)

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



if __name__ == "__main__":
    is_tamper_test = "--tamper-test" in sys.argv
    exit_code = verify_database_signatures(tamper_test=is_tamper_test)
    sys.exit(exit_code)
