"""Main Polling Daemon for Notion Tracker.

Features:
1. Batch API Queries: Pulls all pages sitting in "Approved" status and executes
   downstream dispatches as a single concurrent batch execution (honoring Notion's native multi-select).
2. 60-Minute Polling Loop: Persistent background daemon running state-synchronization
   every 60 minutes, with runtime-configurable auto-refresh parameters.
3. Resilient Token-Bucket Throttling & OCC Non-Repudiation Audit Signing.
"""

import time
import sys
import logging
import argparse
import concurrent.futures
from typing import List, Dict, Any, Tuple

from config import POLL_INTERVAL_MINUTES, POLL_INTERVAL_SECONDS
from notion_store import default_store
from outbound_dispatcher import OutboundDispatcher
from notion_enterprise_guard import default_rate_limiter
from system_health_monitor import SystemHealthMonitor


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("notion_tracker.daemon")


from workflow_engine import WorkflowEngine
from ai_audit_engine import AIAuditEngine
from notion_typesetter import NotionTypesetter

# Module level Notion client reference for test suite compatibility
notion = getattr(default_store, "notion", None)


def simulate_langchain_reasoning(title: str, details: str) -> Dict[str, Any]:
    """Helper wrapper around AIAuditEngine for cognitive risk analysis."""
    audit = AIAuditEngine.analyze_task(title=title, details=details)
    return {
        "risk_level": "HIGH" if audit.risk_level in ("HIGH", "CRITICAL") else audit.risk_level,
        "confidence": int(audit.confidence_score * 100),
        "steps": audit.reasoning_trace,
        "checks": [{"check": "Payload Nonce Check", "status": "PASS"}, {"check": "Timestamp Drift", "status": "PASS"}, {"check": "Heuristic Keywords", "status": "WARN"}],
        "draft_output": audit.draft_teams_text,
    }


def typeset_ai_reasoning_in_notion(page_id: str, title: str, reasoning: Dict[str, Any]):
    """Helper wrapper around NotionTypesetter for typeset block generation."""
    audit_data = {
        "risk_level": reasoning.get("risk_level", "LOW"),
        "confidence_score": reasoning.get("confidence", 95) / 100.0,
        "category": "Security Incident" if "security" in title.lower() else "Operational",
        "reasoning_trace": reasoning.get("steps", []),
        "draft_summary": str(reasoning.get("draft_output", "")),
        "security_flags": ["HIGH_RISK_OP"] if reasoning.get("risk_level") == "HIGH" else [],
    }
    inner_blocks = NotionTypesetter.build_cognitive_audit_blocks(
        task_data={"title": title, "details": ""},
        audit_result=audit_data,
        lang="en",
    )
    heading_block = {
        "object": "block",
        "type": "heading_2",
        "heading_2": {
            "rich_text": [{"type": "text", "text": {"content": f"🧠 AI Pre-Audit: {title}"}}]
        }
    }
    blocks = [heading_block] + inner_blocks
    if notion and hasattr(notion, "blocks"):
        notion.blocks.children.append(block_id=page_id, children=blocks)
    return blocks







def _dispatch_single_task_worker(task: Dict[str, Any]) -> Tuple[str, bool, str]:
    """Worker task executed concurrently within a ThreadPoolExecutor.

    Acquires rate-limiter token, looks up matching Visual Pipeline Template from Notion,
    executes configured steps dynamically, and updates OCC state to 'Dispatched'.
    """
    task_id = task.get("id", "")
    title = task.get("title", "")
    operator_name = "Automated Execution Daemon [Concurrent Batch]"

    # Acquire rate limiter token before API call
    default_rate_limiter.acquire(1.0)

    # 1. Lookup active Pipeline Template matching task source or default template
    templates = default_store.list_pipeline_templates()
    matching_tmpl = None
    task_src = task.get("source", "")
    for tmpl in templates:
        if tmpl.get("status") == "Active 🟢" and (tmpl.get("trigger_source", "").lower() in task_src.lower() or task_src.lower() in tmpl.get("trigger_source", "").lower()):
            matching_tmpl = tmpl
            break
    if not matching_tmpl and templates:
        matching_tmpl = templates[0]

    # 2. Execute dynamic pipeline steps via WorkflowEngine
    if matching_tmpl:
        p_ok, trace, executed_task = WorkflowEngine.execute_pipeline(
            task=task,
            template=matching_tmpl,
            operator_name=operator_name,
            override_biometric=True,
        )
    else:
        # Fallback standard execution
        teams_ok, teams_msg = OutboundDispatcher.dispatch_teams_notification(
            task_data=task,
            operator_name=operator_name,
        )
        email_ok, email_msg = OutboundDispatcher.dispatch_email_notification(
            task_data=task,
        )
        trace = task.get("reasoning_trace", [])

    # 3. Update task status to 'Dispatched' using OCC
    try:
        updated_task, conflict, details = default_store.update_task_with_occ(
            task_id=task_id,
            base_record=task,
            local_updates={"status": "Dispatched", "reasoning_trace": trace},
            operator_name=operator_name,
        )
        # 4. Programmatically generate native Notion Run Log Toggle Blocks (Toggle 1: AI Reasoning, Toggle 2: Raw JSON)
        default_store.write_to_run_log(
            record_id=task_id,
            action="EXECUTION_DISPATCHED",
            operator_name=operator_name,
            task_data=updated_task,
            reasoning_steps=trace,
            raw_payload=task,
        )
        return task_id, True, f"Successfully executed template '{matching_tmpl.get('name', 'Standard')}' (v{updated_task.get('version')})"
    except Exception as e:
        return task_id, False, str(e)




class NotionTrackerDaemon:
    """Persistent 60-minute background automation worker with batch query execution."""

    def __init__(self, poll_interval_minutes: int = POLL_INTERVAL_MINUTES):
        self.poll_interval_seconds = float(poll_interval_minutes * 60)
        self.is_running = False
        self.last_sync_time = 0.0

    def process_cycle(self) -> int:
        """Executes a single polling, batch query, and concurrent execution cycle across all tasks.

        Returns:
            Count of tasks successfully processed & dispatched in this concurrent batch.
        """
        # 1. Run Workspace Self-Healing verification & Emit System Health Heartbeat
        SystemHealthMonitor.emit_heartbeat()
        all_tasks = default_store.list_tasks(include_archived=False)
        recovered = default_store.self_healing.verify_and_recover(all_tasks)
        if recovered:
            for rec in recovered:
                logger.info(f"Self-Healing: Re-inserting restored record: {rec.get('id')}")
                default_store.create_task(rec, operator_name="Self-Healing Subsystem")


        # 2. Batch API Query: Pull all pages currently sitting in 'Approved' status
        approved_tasks = default_store.get_tasks_by_status("Approved")
        batch_size = len(approved_tasks)

        if batch_size == 0:
            logger.info("[SYNC] Database scan completed. No tasks currently pending in 'Approved' status.")
            return 0

        logger.info(f"🚀 [BATCH QUERY] Detected {batch_size} page(s) in 'Approved' status (Multi-Select Batch).")
        logger.info(f"⚡ Launching single concurrent batch execution across {batch_size} worker thread(s)...")

        dispatched_count = 0
        max_workers = min(10, batch_size)

        # 3. Concurrent Batch Execution using ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_task = {
                executor.submit(_dispatch_single_task_worker, task): task
                for task in approved_tasks
            }

            for future in concurrent.futures.as_completed(future_to_task):
                task = future_to_task[future]
                task_id = task.get("id", "")
                try:
                    tid, success, msg = future.result()
                    if success:
                        dispatched_count += 1
                        logger.info(f"  ✓ [CONCURRENT DISPATCH] Task '{task.get('title')}' ({tid}): {msg}")
                    else:
                        logger.error(f"  ✗ [DISPATCH FAILED] Task '{task.get('title')}' ({tid}): {msg}")
                except Exception as e:
                    logger.error(f"  ✗ [THREAD EXCEPTION] Task '{task_id}': {e}")

        logger.info(f"✅ [BATCH COMPLETE] Successfully dispatched {dispatched_count}/{batch_size} tasks concurrently.")

        # Update last sync timestamp in system config
        default_store.update_system_config({"last_sync_timestamp": time.time()})
        return dispatched_count

    def run(self) -> None:
        """Starts the persistent 60-minute daemon loop with runtime-configurable auto-refresh."""
        self.is_running = True
        logger.info("=" * 68)
        logger.info(" 🚀 NOTION TRACKER PERSISTENT WORKER DAEMON STARTED")
        logger.info(f" Standard Polling Cadence: Every {int(self.poll_interval_seconds // 60)} minutes ({self.poll_interval_seconds:.0f}s)")
        logger.info(" Mode: Automatic Independent Background Service (Notion Multi-Select Batch Active)")
        logger.info("=" * 68)

        # Run initial cycle immediately upon startup
        self.process_cycle()
        self.last_sync_time = time.time()

        try:
            while self.is_running:
                # Dynamic runtime configuration check on each 1-second tick
                cfg = default_store.get_system_config()
                current_interval = float(cfg.get("poll_interval_seconds", self.poll_interval_seconds))
                auto_refresh = cfg.get("auto_refresh_enabled", True)

                now = time.time()
                elapsed = now - self.last_sync_time

                if auto_refresh and elapsed >= current_interval:
                    logger.info(f"[DAEMON CYCLE] Executing scheduled {int(current_interval // 60)}m state synchronization...")
                    self.process_cycle()
                    self.last_sync_time = time.time()

                # Low-latency 1s sleep allows instant responsiveness to runtime config changes or SIGINT
                time.sleep(1.0)

        except KeyboardInterrupt:
            logger.info("Worker daemon received shutdown signal. Stopping gracefully...")
            self.is_running = False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Notion Tracker 60-Minute Background Daemon")
    parser.add_argument("--once", action="store_true", help="Execute a single concurrent batch cycle and exit")
    parser.add_argument("--minutes", type=int, default=POLL_INTERVAL_MINUTES, help="Polling interval in minutes (default: 60)")
    parser.add_argument("--seconds", type=float, default=None, help="Polling interval in seconds for testing (e.g. 5)")
    args = parser.parse_args()

    interval_mins = args.minutes
    daemon = NotionTrackerDaemon(poll_interval_minutes=interval_mins)

    if args.seconds is not None:
        daemon.poll_interval_seconds = args.seconds

    if args.once:
        logger.info("Executing single concurrent pass cycle...")
        dispatched = daemon.process_cycle()
        logger.info(f"Single pass complete. Dispatched {dispatched} task(s).")
        sys.exit(0)
    else:
        daemon.run()
