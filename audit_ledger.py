"""Industrial Cryptographic Audit Ledger Module.

Generates deterministic SHA-256 digital signatures creating an immutable hash chain
over tasks, operator actions, timestamps, and execution payloads for non-repudiation.
"""

import hashlib
import json
import time
from typing import Dict, Any, List, Optional, Tuple
import logging

logger = logging.getLogger("notion_tracker.ledger")


class AuditLedger:
    """Tamper-proof cryptographic audit ledger maintaining a SHA-256 signature chain."""

    GENESIS_HASH = "0" * 64

    @staticmethod
    def compute_record_signature(
        record_id: str,
        action: str,
        operator_name: str,
        timestamp: float,
        payload_data: Dict[str, Any],
        prev_signature: str = GENESIS_HASH,
    ) -> str:
        """Calculates a deterministic SHA-256 signature binding all transaction fields.

        Args:
            record_id: Identifier of the task/page.
            action: Action performed (INGESTED, APPROVED, REJECTED, DISPATCHED, etc.).
            operator_name: Name/Role of the authorizing user or daemon.
            timestamp: Epoch timestamp of the transaction.
            payload_data: Normalized dictionary of task attributes.
            prev_signature: Hash of the preceding block in the ledger chain.

        Returns:
            Hexadecimal SHA-256 digital signature string.
        """
        # Canonical JSON serialization of payload data
        canonical_payload = json.dumps(payload_data, sort_keys=True, separators=(",", ":"))
        signing_material = (
            f"RECORD_ID:{record_id}|"
            f"ACTION:{action}|"
            f"OPERATOR:{operator_name}|"
            f"TIMESTAMP:{timestamp:.3f}|"
            f"PREV_HASH:{prev_signature}|"
            f"PAYLOAD:{canonical_payload}"
        )
        return hashlib.sha256(signing_material.encode("utf-8")).hexdigest()

    @classmethod
    def genesis_block_hash(cls) -> str:
        return cls.GENESIS_HASH

    @classmethod
    def hash_log_entry(cls, record_id: str, action: str, operator_name: str, timestamp: float, payload_data: Any, prev_signature: str = GENESIS_HASH) -> str:
        if isinstance(payload_data, str):
            try:
                payload_dict = json.loads(payload_data)
            except Exception:
                payload_dict = {"data": payload_data}
        else:
            payload_dict = payload_data or {}
        return cls.compute_record_signature(record_id, action, operator_name, timestamp, payload_dict, prev_signature)

    @classmethod
    def verify_ledger_chain(cls, log_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Audits an entire sequence of log records to detect tampering or broken hash chains.

        Args:
            log_entries: Chronologically ordered list of audit log records.

        Returns:
            Dictionary matching the API spec:
            {
                "status": "SECURE" | "ALERT",
                "recalculated_records": int,
                "mismatches_detected": int,
                "signature_chain_valid": bool,
                "tampered_pages": list
            }
        """
        recalculated_count = 0
        mismatches: List[Dict[str, Any]] = []
        chain_valid = True
        expected_prev_hash = log_entries[0].get("prev_signature", cls.GENESIS_HASH) if log_entries else cls.GENESIS_HASH

        for idx, entry in enumerate(log_entries):
            recalculated_count += 1
            stored_sig = entry.get("signature", "")
            prev_sig_in_entry = entry.get("prev_signature", cls.GENESIS_HASH)

            # Check chain link
            if idx > 0 and prev_sig_in_entry != expected_prev_hash:
                chain_valid = False

            # Recalculate signature
            calc_sig = cls.compute_record_signature(
                record_id=str(entry.get("record_id") or entry.get("page_id", "")),
                action=str(entry.get("action", "")),
                operator_name=str(entry.get("operator_name", "")),
                timestamp=float(entry.get("timestamp", 0.0)),
                payload_data=entry.get("payload_data", {}),
                prev_signature=prev_sig_in_entry,
            )

            if calc_sig.lower() != stored_sig.lower():
                mismatches.append({
                    "entry_id": entry.get("id", f"entry_{idx}"),
                    "page_id": entry.get("record_id") or entry.get("page_id", ""),
                    "action": entry.get("action", ""),
                    "expected_signature": calc_sig,
                    "recalculated_signature": stored_sig,
                })

            expected_prev_hash = stored_sig

        status = "SECURE" if (len(mismatches) == 0 and chain_valid) else "ALERT"

        result = {
            "status": status,
            "recalculated_records": recalculated_count,
            "mismatches_detected": len(mismatches),
            "signature_chain_valid": chain_valid,
        }
        if mismatches:
            result["tampered_pages"] = mismatches

        return result
