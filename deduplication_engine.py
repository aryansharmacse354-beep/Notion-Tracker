"""Deduplication Fingerprinting Engine (Stage 1: Multi-Modal Ingestion).

Computes deterministic SHA-256 ingestion fingerprints based on normalized payload
attributes (e.g. lowercase text, collapsed whitespace, sender, and timestamp bucketing).
Blocks rapid double-clicks, network retry duplicates, and redundant submissions
before touching Notion API quotas or SQLite write locks.
"""

import hashlib
import re
import time
from typing import Tuple, Optional, Dict, Any, Set
import logging

logger = logging.getLogger("notion_tracker.deduplication")


class DeduplicationFingerprinter:
    """Enterprise Deduplication Fingerprint Authority."""

    def __init__(self, default_window_seconds: int = 600):
        self.default_window_seconds = default_window_seconds
        # In-memory fast cache: fingerprint -> (timestamp, task_id)
        self._seen_cache: Dict[str, Tuple[float, str]] = {}

    @staticmethod
    def normalize_text(text: Optional[str]) -> str:
        """Normalizes text by lowercasing, stripping whitespace, and normalizing punctuation."""
        if not text:
            return ""
        # Lowercase and collapse multiple whitespaces
        normalized = re.sub(r"\s+", " ", str(text).strip().lower())
        return normalized

    def compute_fingerprint(
        self,
        title: str,
        details: str = "",
        source: str = "",
        sender: Optional[str] = None,
        timestamp: Optional[float] = None,
        window_seconds: Optional[int] = None,
    ) -> str:
        """Computes a deterministic SHA-256 fingerprint for the given task attributes.

        Args:
            title: Task title.
            details: Unstructured details or instructions.
            source: Source system identifier (e.g. "Academic Portal").
            sender: Optional sender email or phone number.
            timestamp: Epoch UTC seconds (defaults to current time).
            window_seconds: Sliding deduplication window in seconds.

        Returns:
            A 64-character hexadecimal SHA-256 fingerprint string.
        """
        ts = timestamp if timestamp is not None else time.time()
        win = window_seconds if window_seconds is not None else self.default_window_seconds

        # Time window bucket (e.g. 10-minute quantization)
        time_bucket = int(ts // win) if win > 0 else 0

        norm_title = self.normalize_text(title)
        norm_details = self.normalize_text(details)
        norm_source = self.normalize_text(source)
        norm_sender = self.normalize_text(sender) if sender else ""

        raw_canonical = f"{norm_title}|{norm_details}|{norm_source}|{norm_sender}|{time_bucket}"
        fingerprint = hashlib.sha256(raw_canonical.encode("utf-8")).hexdigest()
        return fingerprint

    def check_and_record(
        self,
        fingerprint: str,
        task_id: str,
        timestamp: Optional[float] = None,
        window_seconds: Optional[int] = None,
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Checks if a fingerprint was already seen within the deduplication window.

        Args:
            fingerprint: The calculated SHA-256 fingerprint.
            task_id: Identifier of the incoming task.
            timestamp: Ingestion timestamp.
            window_seconds: Sliding window.

        Returns:
            Tuple of (is_unique: bool, duplicate_task_id: Optional[str], rejection_reason: Optional[str])
        """
        now = timestamp if timestamp is not None else time.time()
        win = window_seconds if window_seconds is not None else self.default_window_seconds

        # Purge stale fingerprints older than 2x window
        cutoff = now - (win * 2)
        stale_keys = [k for k, (seen_time, _) in self._seen_cache.items() if seen_time < cutoff]
        for k in stale_keys:
            self._seen_cache.pop(k, None)

        if fingerprint in self._seen_cache:
            seen_time, existing_task_id = self._seen_cache[fingerprint]
            age_sec = int(now - seen_time)
            msg = (
                f"Duplicate submission blocked by Ingestion Fingerprinter. "
                f"Identical payload already recorded as Task '{existing_task_id}' {age_sec}s ago."
            )
            logger.warning(f"[DEDUPLICATION] Rejected fingerprint {fingerprint[:16]}...: {msg}")
            return False, existing_task_id, msg

        # Record fresh fingerprint
        self._seen_cache[fingerprint] = (now, task_id)
        logger.info(f"[DEDUPLICATION] Stored fresh fingerprint {fingerprint[:16]}... for task {task_id}")
        return True, None, None

    def clear(self):
        """Clears in-memory fingerprint cache (used for unit testing)."""
        self._seen_cache.clear()


# Default singleton instance
default_deduplicator = DeduplicationFingerprinter(default_window_seconds=600)
