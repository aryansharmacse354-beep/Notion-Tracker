"""Outbound Dispatcher Module for Notion Tracker.

Formats and dispatches notifications to Microsoft Teams (Adaptive Cards),
SendGrid (Transactional HTML Emails), and exports Excel audit logs.
"""

import json
import logging
from typing import Dict, Any, List, Optional
try:
    import requests
except ImportError:
    requests = None

try:
    import pandas as pd
except ImportError:
    pd = None
from io import BytesIO

from config import (
    TEAMS_WEBHOOK_URL,
    SENDGRID_API_KEY,
    SENDGRID_FROM_EMAIL,
    NOTIFICATION_RECIPIENT_EMAIL,
)

logger = logging.getLogger("notion_tracker.outbound")


class TeamsAdaptiveCardBuilder:
    """Constructs Microsoft Teams Fluent Adaptive Cards."""

    @staticmethod
    def build_card_payload(task_data: Dict[str, Any], operator_name: str) -> Dict[str, Any]:
        """Builds a standard Adaptive Card JSON payload.

        Args:
            task_data: Task dictionary.
            operator_name: Authorizing operator name.

        Returns:
            Adaptive Card payload dictionary.
        """
        title = task_data.get("title", "Untitled Task")
        details = task_data.get("details", "No details provided.")
        category = task_data.get("category", "General")
        priority = str(task_data.get("priority", "normal")).upper()
        risk_level = task_data.get("risk_level", "LOW")
        task_id = task_data.get("id", "N/A")

        # Stage 3 HITL: Prioritize human-edited wording over raw AI draft
        outbound_content = (
            task_data.get("edited_draft")
            or task_data.get("proposed_ai_draft")
            or task_data.get("draft_teams_text")
            or task_data.get("details", "No details provided.")
        )
        is_human_edited = bool(task_data.get("edited_draft"))

        card = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "contentUrl": None,
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "body": [
                            {
                                "type": "TextBlock",
                                "size": "Large",
                                "weight": "Bolder",
                                "text": f"🚀 Notion Tracker: {title}",
                                "wrap": True,
                            },
                            {
                                "type": "FactSet",
                                "facts": [
                                    {"title": "Task ID:", "value": str(task_id)},
                                    {"title": "Category:", "value": str(category)},
                                    {"title": "Priority:", "value": priority},
                                    {"title": "Pre-Audit Risk:", "value": f"{risk_level}"},
                                    {"title": "Approved By:", "value": str(operator_name)},
                                    {"title": "Draft Version:", "value": "Human-Edited ✍️" if is_human_edited else "AI Proposed 🤖"},
                                    {"title": "Status:", "value": "APPROVED & DISPATCHED"},
                                ],
                            },
                            {
                                "type": "TextBlock",
                                "text": "Outbound Content (Authorized by Operator):",
                                "weight": "Bolder",
                                "spacing": "Medium",
                            },
                            {
                                "type": "TextBlock",
                                "text": str(outbound_content),
                                "wrap": True,
                            },
                        ],
                    },
                }
            ],
        }
        return card



class OutboundDispatcher:
    """Handles multi-channel outbound notification dispatches."""

    @classmethod
    def dispatch_teams_notification(
        cls,
        task_data: Dict[str, Any],
        operator_name: str,
        webhook_url: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """Dispatches an Adaptive Card to Microsoft Teams webhook."""
        url = webhook_url or TEAMS_WEBHOOK_URL
        card = TeamsAdaptiveCardBuilder.build_card_payload(task_data, operator_name)

        if not url or url.startswith("https://outlook.office.com/webhook/your-teams"):
            logger.info("Teams Webhook not configured. Simulated dispatch successful.")
            return True, "Simulated MS Teams Adaptive Card dispatch (No live URL provided)"

        try:
            resp = requests.post(url, json=card, headers={"Content-Type": "application/json"}, timeout=10)
            if resp.status_code in (200, 201, 202):
                return True, f"MS Teams dispatch succeeded (HTTP {resp.status_code})"
            return False, f"MS Teams dispatch failed: HTTP {resp.status_code} - {resp.text}"
        except Exception as e:
            logger.error(f"Error dispatching to Teams: {e}")
            return False, str(e)

    @classmethod
    def dispatch_email_notification(
        cls,
        task_data: Dict[str, Any],
        recipient: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """Dispatches HTML email notification via SendGrid API or simulated sink."""
        to_email = recipient or NOTIFICATION_RECIPIENT_EMAIL
        subject = f"[Notion Tracker] Approved: {task_data.get('title', 'Task')}"
        html_content = task_data.get("draft_email_html") or f"<p>{task_data.get('details', '')}</p>"

        if not SENDGRID_API_KEY or SENDGRID_API_KEY.startswith("SG.your_sendgrid"):
            logger.info(f"SendGrid API Key not configured. Simulated email dispatch to {to_email}.")
            return True, f"Simulated SendGrid email dispatch to {to_email}"

        try:
            url = "https://api.sendgrid.com/v3/mail/send"
            headers = {
                "Authorization": f"Bearer {SENDGRID_API_KEY}",
                "Content-Type": "application/json",
            }
            payload = {
                "personalizations": [{"to": [{"email": to_email}]}],
                "from": {"email": SENDGRID_FROM_EMAIL, "name": "Notion Tracker"},
                "subject": subject,
                "content": [{"type": "text/html", "value": html_content}],
            }
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            if resp.status_code in (200, 202):
                return True, f"SendGrid email dispatched (HTTP {resp.status_code})"
            return False, f"SendGrid email failed: HTTP {resp.status_code} - {resp.text}"
        except Exception as e:
            logger.error(f"Error dispatching SendGrid email: {e}")
            return False, str(e)

    @classmethod
    def export_tasks_to_excel(cls, tasks: List[Dict[str, Any]]) -> bytes:
        """Exports a list of tasks into an Excel .xlsx binary buffer or CSV fallback."""
        if pd is not None:
            try:
                df = pd.DataFrame(tasks)
                if "reasoning_trace" in df.columns:
                    df["reasoning_trace"] = df["reasoning_trace"].apply(lambda x: "\n".join(x) if isinstance(x, list) else str(x))

                output = BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False, sheet_name="Notion_Tracker_Tasks")
                return output.getvalue()
            except Exception:
                pass

        # Clean fallback: CSV in BytesIO
        output = BytesIO()
        if tasks:
            headers = list(tasks[0].keys())
            output.write((",".join(headers) + "\n").encode("utf-8"))
            for t in tasks:
                row = [str(t.get(h, "")).replace(",", ";") for h in headers]
                output.write((",".join(row) + "\n").encode("utf-8"))
        return output.getvalue()

