"""Bi-Directional Notion Comment Agent.

Processes natural language @AI comment commands on Notion pages and executes
corresponding state transitions, re-assessments, escalations, or summaries.
"""

import re
import logging
from typing import Dict, Any, Tuple, Optional
from ai_audit_engine import AIAuditEngine
from notion_store import default_store

logger = logging.getLogger("notion_tracker.comment_agent")


class NotionCommentAgent:
    """Conversational AI agent that responds to @AI triggers in Notion page comments."""

    @classmethod
    def process_comment(
        cls,
        task_id: str,
        comment_text: str,
        author_name: str = "Aryan Sharma",
    ) -> Tuple[bool, str]:
        """Parses and executes an @AI command on a specified task.

        Args:
            task_id: The ID of the task to interact with.
            comment_text: The full text of the user comment (e.g. '@AI re-assess risk').
            author_name: The operator submitting the comment.

        Returns:
            Tuple of (success: bool, response_message: str).
        """
        task = default_store.get_task(task_id)
        if not task:
            return False, f"Task '{task_id}' not found in store."

        clean_comment = comment_text.strip()
        if not re.search(r"@AI\b", clean_comment, re.IGNORECASE):
            return False, "No @AI mention found in comment."

        # Extract the command after @AI
        match = re.search(r"@AI\s+(.*)", clean_comment, re.IGNORECASE | re.DOTALL)
        command_body = match.group(1).strip() if match else ""
        lower_cmd = command_body.lower()

        # 1. Re-assess Risk
        if "re-assess" in lower_cmd or "reassess" in lower_cmd or "re-audit" in lower_cmd:
            audit_res = AIAuditEngine.analyze_task(
                title=task.get("title", ""),
                details=task.get("details", ""),
                requested_priority=task.get("priority", "normal"),
            )
            updated, conflict, _ = default_store.update_task_with_occ(
                task_id=task_id,
                base_record=task,
                local_updates={
                    "risk_level": audit_res.risk_level,
                    "confidence_score": audit_res.confidence_score,
                    "reasoning_trace": audit_res.reasoning_trace,
                    "draft_summary": audit_res.draft_summary,
                    "ai_reasoning_ledger": audit_res.ai_reasoning_ledger,
                },
                operator_name=f"{author_name} [@AI Comment Agent]",
            )
            default_store.write_to_run_log(
                record_id=task_id,
                action="AI_RISK_REASSESSED",
                operator_name=author_name,
                task_data=updated,
                reasoning_steps=audit_res.reasoning_trace,
                raw_payload={"command": comment_text, "risk_level": audit_res.risk_level},
            )
            msg = f"🤖 **AI Risk Re-Assessment Completed**\n• Evaluated Risk: **{audit_res.risk_level}** (Confidence: {int(audit_res.confidence_score*100)}%)\n• Category: {audit_res.category}\n• Status: {updated.get('status')}"
            return True, msg

        # 2. Update Budget (e.g. '@AI update budget $4,500 for Lab Group B')
        elif "budget" in lower_cmd:
            budget_match = re.search(r"(?:\$)?(\d[\d,.]*)", command_body)
            budget_str = f"${budget_match.group(1)}" if budget_match else "$5,000"
            updated, conflict, _ = default_store.update_task_with_occ(
                task_id=task_id,
                base_record=task,
                local_updates={"budget": budget_str},
                operator_name=f"{author_name} [@AI Budget Update]",
            )
            reasoning = [
                f"[Step 1] Parsed @AI comment command: '{clean_comment}'.",
                f"[Step 2] Extracted budget specification: {budget_str}.",
                f"[Step 3] Updated Notion task page properties with OCC v{updated.get('version')}."
            ]
            default_store.write_to_run_log(
                record_id=task_id,
                action="BUDGET_UPDATED",
                operator_name=author_name,
                task_data=updated,
                reasoning_steps=reasoning,
                raw_payload={"command": comment_text, "new_budget": budget_str},
            )
            return True, f"💰 **Budget Property Updated**\n• Authorized by: {author_name}\n• New Budget Allocation: **{budget_str}**\n• OCC State: `v{updated.get('version')}`"

        # 3. Approve
        elif lower_cmd.startswith("approve"):
            reason = command_body[7:].strip() or "Approved via @AI comment"
            updated, conflict, _ = default_store.update_task_with_occ(
                task_id=task_id,
                base_record=task,
                local_updates={"status": "Approved"},
                operator_name=f"{author_name} [@AI Approval]",
            )
            default_store.write_to_run_log(
                record_id=task_id,
                action="APPROVED_VIA_COMMENT",
                operator_name=author_name,
                task_data=updated,
                reasoning_steps=[f"[Step 1] @AI command '{clean_comment}' parsed.", "[Step 2] State transitioned to Approved."],
                raw_payload={"command": comment_text, "reason": reason},
            )
            return True, f"✅ **Task Approved via Comment Command**\n• Authorized by: {author_name}\n• Reason: {reason}\n• Status updated to `Approved`."

        # 4. Reject
        elif lower_cmd.startswith("reject"):
            reason = command_body[6:].strip() or "Rejected via @AI comment"
            updated, conflict, _ = default_store.update_task_with_occ(
                task_id=task_id,
                base_record=task,
                local_updates={"status": "Rejected"},
                operator_name=f"{author_name} [@AI Rejection]",
            )
            default_store.write_to_run_log(
                record_id=task_id,
                action="REJECTED_VIA_COMMENT",
                operator_name=author_name,
                task_data=updated,
                reasoning_steps=[f"[Step 1] @AI command '{clean_comment}' parsed.", "[Step 2] State transitioned to Rejected."],
                raw_payload={"command": comment_text, "reason": reason},
            )
            return True, f"❌ **Task Rejected via Comment Command**\n• Authorized by: {author_name}\n• Reason: {reason}\n• Status updated to `Rejected`."

        # 5. Escalate
        elif "escalate" in lower_cmd:
            updated, conflict, _ = default_store.update_task_with_occ(
                task_id=task_id,
                base_record=task,
                local_updates={"priority": "critical", "risk_level": "CRITICAL"},
                operator_name=f"{author_name} [@AI Escalation]",
            )
            default_store.write_to_run_log(
                record_id=task_id,
                action="ESCALATED_VIA_COMMENT",
                operator_name=author_name,
                task_data=updated,
                reasoning_steps=[f"[Step 1] @AI escalation trigger received.", "[Step 2] Priority set to CRITICAL and flagged for biometric lock."],
                raw_payload={"command": comment_text, "new_priority": "critical"},
            )
            return True, f"🚨 **Task Escalated to CRITICAL Priority**\n• Updated by: {author_name}\n• Priority: `CRITICAL` | Risk: `CRITICAL`"

        # 6. Summarize
        elif "summarize" in lower_cmd or "summary" in lower_cmd:
            title = task.get("title", "")
            cat = task.get("category", "")
            risk = task.get("risk_level", "")
            status = task.get("status", "")
            details = task.get("details", "")
            budget = task.get("budget", "$0")
            msg = f"📊 **Task Summary for #{task_id[:8]}**\n• Title: **{title}**\n• Category: {cat} | Risk: **{risk}** | Status: `{status}` | Budget: `{budget}`\n• Scope: {details[:120]}..."
            return True, msg

        # Default Help
        else:
            return True, (
                "🤖 **Available @AI Commands:**\n"
                "• `@AI update budget <amount>` — Updates budget property and logs to Run Log\n"
                "• `@AI re-assess risk` — Re-evaluates risk score and CoT trace\n"
                "• `@AI approve [reason]` — Authorizes task and triggers outbound dispatch\n"
                "• `@AI reject [reason]` — Declines task and logs audit reason\n"
                "• `@AI escalate` — Sets priority to Critical and Risk to CRITICAL\n"
                "• `@AI summarize` — Generates a concise status breakdown"
            )

    @classmethod
    def poll_and_process_pending_comments(cls, store=default_store, notion_client=None) -> int:
        """Polls active tasks for comments containing @AI and executes them.

        Args:
            store: The NotionStore instance.
            notion_client: Optional Notion SDK client.

        Returns:
            Number of @AI comments processed in this cycle.
        """
        from notion_enterprise_guard import default_rate_limiter
        processed_count = 0
        all_tasks = store.list_tasks(include_archived=False)

        for task in all_tasks:
            task_id = task.get("id")
            # 1. If Notion Client is configured, query page comments
            if notion_client and hasattr(notion_client, "comments"):
                try:
                    default_rate_limiter.acquire(1.0)
                    comments_resp = notion_client.comments.list(block_id=task_id)
                    for comment_obj in comments_resp.get("results", []):
                        rich_texts = comment_obj.get("rich_text", [])
                        full_text = "".join(r.get("plain_text", "") for r in rich_texts)
                        if "@AI" in full_text:
                            author = comment_obj.get("created_by", {}).get("name", "Notion Operator")
                            ok, reply = cls.process_comment(task_id, full_text, author)
                            if ok:
                                processed_count += 1
                                # Post AI response back to Notion comment thread
                                default_rate_limiter.acquire(1.0)
                                notion_client.comments.create(
                                    parent={"page_id": task_id},
                                    rich_text=[{"text": {"content": reply}}]
                                )
                except Exception as e:
                    logger.debug(f"Comment polling skipped for {task_id}: {e}")

            # 2. Check locally queued or task-level comments
            comment_thread = task.get("comment_thread") or task.get("comments")
            if comment_thread and isinstance(comment_thread, str) and "@AI" in comment_thread and not comment_thread.startswith("[Processed]"):
                ok, reply = cls.process_comment(task_id, comment_thread, "Aryan Sharma")
                if ok:
                    processed_count += 1
                    latest_rec = store.get_task(task_id) or task
                    store.update_task_with_occ(
                        task_id=task_id,
                        base_record=latest_rec,
                        local_updates={"comment_thread": f"[Processed] {comment_thread}"},
                        operator_name="Comment Agent Daemon",
                    )
        return processed_count

