"""Notion Enterprise Guard Module.

Provides thread-safe Token-Bucket Rate Limiting, Optimistic Concurrency Control (OCC)
with Three-Way Merge Conflict Resolution, HMAC-SHA256 Ingestion Verification with
Nonce Replay Guards, and Workspace Auto-Recovery (Self-Healing).
"""

import hmac
import hashlib
import time
import threading
import uuid
import copy
from typing import Dict, Any, Tuple, Optional, List
import logging
from config import (
    WEBHOOK_SECRET,
    MAX_TIMESTAMP_DRIFT_SECONDS,
    RATE_LIMIT_CAPACITY,
    RATE_LIMIT_REPLENISH_RATE,
)

logger = logging.getLogger("notion_tracker.guard")


class TokenBucketRateLimiter:
    """Thread-safe Token Bucket Rate Limiter for Notion API throttling.

    Maintains capacity and replenishes tokens linearly over time. Ensures API calls
    comply with Notion's rate limits (<= 2 writes/sec by default).
    """

    def __init__(self, capacity: float = RATE_LIMIT_CAPACITY, replenish_rate: float = RATE_LIMIT_REPLENISH_RATE):
        self.capacity = float(capacity)
        self.replenish_rate = float(replenish_rate)  # tokens added per second
        self.tokens = float(capacity)
        self.last_update = time.monotonic()
        self.lock = threading.RLock()
        self.queued_count = 0

    def _replenish(self) -> None:
        """Internal helper to calculate newly accumulated tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self.last_update
        if elapsed > 0:
            self.tokens = min(self.capacity, self.tokens + (elapsed * self.replenish_rate))
            self.last_update = now

    def acquire(self, tokens: float = 1.0, block: bool = True, timeout: Optional[float] = None) -> bool:
        """Acquires the specified number of tokens.

        Args:
            tokens: Number of tokens requested.
            block: If True, waits until sufficient tokens are available or timeout expires.
            timeout: Maximum seconds to wait if blocking.

        Returns:
            True if tokens were acquired, False otherwise.
        """
        start_wait = time.monotonic()
        with self.lock:
            while True:
                self._replenish()
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return True

                if not block:
                    return False

                # Calculate wait time needed for missing tokens
                needed = tokens - self.tokens
                wait_time = needed / self.replenish_rate

                if timeout is not None:
                    elapsed = time.monotonic() - start_wait
                    if elapsed + wait_time > timeout:
                        return False

                self.queued_count += 1
                try:
                    self.lock.release()
                    time.sleep(min(wait_time, 0.1))
                finally:
                    self.lock.acquire()
                    self.queued_count = max(0, self.queued_count - 1)

    def get_state(self) -> Dict[str, Any]:
        """Returns the current telemetry status of the token bucket."""
        with self.lock:
            self._replenish()
            status = "NOMINAL" if self.tokens >= 1.0 else "THROTTLED"
            return {
                "token_bucket": {
                    "capacity": round(self.capacity, 2),
                    "available_tokens": round(self.tokens, 2),
                    "leak_rate_seconds": round(1.0 / self.replenish_rate if self.replenish_rate > 0 else 0.0, 2),
                    "status": status,
                },
                "queued_tasks_count": self.queued_count,
            }


class NonceGuard:
    """Replay attack guard maintaining an in-memory cache of nonces and timestamp drift."""

    def __init__(self, max_drift_seconds: int = MAX_TIMESTAMP_DRIFT_SECONDS):
        self.max_drift_seconds = max_drift_seconds
        self.seen_nonces: Dict[str, float] = {}
        self.lock = threading.Lock()

    def validate_and_record(self, nonce: str, timestamp: int) -> Tuple[bool, str]:
        """Validates that a nonce has not been reused and timestamp is within acceptable window.

        Args:
            nonce: Cryptographic unique nonce string.
            timestamp: Epoch UTC seconds from request header.

        Returns:
            Tuple of (is_valid, error_reason).
        """
        now = time.time()
        # 1. Check timestamp drift
        drift = abs(now - float(timestamp))
        if drift > self.max_drift_seconds:
            return False, f"Timestamp drift {drift:.1f}s exceeds limit of {self.max_drift_seconds}s"

        with self.lock:
            # Purge expired nonces older than 2x max drift
            cutoff = now - (self.max_drift_seconds * 2)
            self.seen_nonces = {k: v for k, v in self.seen_nonces.items() if v >= cutoff}

            # 2. Check if nonce was already used
            if nonce in self.seen_nonces:
                return False, f"Replay attack detected: Nonce '{nonce}' has already been processed"

            # Record nonce
            self.seen_nonces[nonce] = now
            return True, "Nonce validated successfully"


def generate_hmac_signature(payload_bytes: bytes, secret: str = WEBHOOK_SECRET) -> str:
    """Generates an HMAC-SHA256 hexadecimal digest for request verification."""
    return hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()


def verify_hmac_signature(payload_bytes: bytes, signature_hex: str, secret: str = WEBHOOK_SECRET) -> bool:
    """Performs constant-time HMAC-SHA256 signature verification."""
    expected = generate_hmac_signature(payload_bytes, secret)
    return hmac.compare_digest(expected.lower(), signature_hex.lower().strip())


# Global singletons
default_rate_limiter = TokenBucketRateLimiter()
default_nonce_guard = NonceGuard()


class OptimisticConcurrencyControl:
    """Optimistic Concurrency Control (OCC) manager for Notion row-level state sync.

    Tracks version numbers and cryptographic nonces. Employs a Three-Way Merge
    Resolution Protocol when concurrent human/daemon edits are detected.
    """

    @staticmethod
    def generate_nonce() -> str:
        """Generates a secure cryptographic nonce for row-level version tagging."""
        return uuid.uuid4().hex[:16]

    @staticmethod
    def check_conflict(current_version: int, target_version: int) -> bool:
        """Returns True if there is a version mismatch indicating a concurrent modification."""
        return current_version != target_version

    @classmethod
    def resolve_three_way_merge(
        cls,
        base_record: Dict[str, Any],
        local_record: Dict[str, Any],
        remote_record: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], bool, List[str]]:
        """Performs a 3-way merge between base snapshot, local edit, and remote record.

        Args:
            base_record: The state when the current session started reading the record.
            local_record: The modified state attempted to be saved by the current worker/user.
            remote_record: The current state actively stored in the database.

        Returns:
            Tuple of (merged_record, had_conflict, list_of_conflict_details)
        """
        merged = copy.deepcopy(remote_record)
        had_conflict = False
        conflict_details: List[str] = []

        all_keys = set(base_record.keys()) | set(local_record.keys()) | set(remote_record.keys())
        # Internal fields to handle specially
        skip_keys = {"version", "nonce", "updated_at", "id", "page_id"}

        for key in all_keys:
            if key in skip_keys:
                continue

            base_val = base_record.get(key)
            local_val = local_record.get(key)
            remote_val = remote_record.get(key)

            local_changed = local_val != base_val
            remote_changed = remote_val != base_val

            if local_changed and not remote_changed:
                # Local modified it, remote did not touch it -> accept local
                merged[key] = local_val
            elif not local_changed and remote_changed:
                # Remote modified it, local did not touch it -> keep remote
                merged[key] = remote_val
            elif local_changed and remote_changed:
                if local_val == remote_val:
                    # Both made the identical change
                    merged[key] = local_val
                else:
                    # True Conflict!
                    had_conflict = True
                    # Conflict resolution rules:
                    # 1. If key is 'status' and local is terminal ('Approved'/'Rejected'), local human decision wins
                    if key == "status" and local_val in ("Approved", "Rejected"):
                        merged[key] = local_val
                        conflict_details.append(f"Status conflict: Operator decision '{local_val}' took precedence over remote '{remote_val}'")
                    # 2. If local has higher priority or human edit, prioritize local
                    elif key == "priority" and local_val in ("critical", "high"):
                        merged[key] = local_val
                        conflict_details.append(f"Priority conflict: Escalated local priority '{local_val}' selected over '{remote_val}'")
                    else:
                        # Default resolution: remote wins or combine text
                        if isinstance(local_val, str) and isinstance(remote_val, str) and key in ("details", "comments", "reasoning"):
                            merged[key] = f"{remote_val}\n[Merged Note]: {local_val}"
                            conflict_details.append(f"Content merge: Appended local notes to remote '{key}'")
                        else:
                            merged[key] = local_val
                            conflict_details.append(f"Field '{key}' conflict resolved in favor of incoming update: '{local_val}'")

        # Increment version and issue new nonce
        new_version = max(remote_record.get("version", 1), local_record.get("version", 1), base_record.get("version", 1)) + 1
        merged["version"] = new_version
        merged["nonce"] = cls.generate_nonce()
        merged["updated_at"] = time.time()

        return merged, had_conflict, conflict_details


class WorkspaceSelfHealing:
    """Workspace Auto-Recovery engine that reconstructs corrupted/deleted records."""

    def __init__(self):
        self._local_cache: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()

    def snapshot(self, record_id: str, data: Dict[str, Any]) -> None:
        """Stores an authoritative snapshot of a record."""
        with self.lock:
            self._local_cache[record_id] = copy.deepcopy(data)

    def verify_and_recover(self, current_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identifies missing records from the cache and produces restored records.

        Returns list of recovered records to be re-inserted.
        """
        with self.lock:
            existing_ids = {r.get("id") or r.get("page_id") for r in current_records}
            recovered: List[Dict[str, Any]] = []

            for rec_id, cached in self._local_cache.items():
                if rec_id and rec_id not in existing_ids:
                    logger.warning(f"Self-Healing: Detected missing record '{rec_id}'. Auto-recovering from cache.")
                    restored_rec = copy.deepcopy(cached)
                    restored_rec["auto_recovered"] = True
                    restored_rec["recovered_at"] = time.time()
                    recovered.append(restored_rec)

            return recovered
