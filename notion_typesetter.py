"""Dynamic Page Typesetting Module for Notion Tracker with Multilingual Localization.

Converts internal task metadata and AI pre-audit results into standard Notion Blocks API structures,
creating an elegant 'Cognitive Audit Panel' directly inside page bodies (supporting the 'Turn-Off Test').
Dynamically typesets blocks into English, Spanish, German, Japanese, Hindi, or French based on active settings.
"""

from typing import Dict, Any, List, Optional
import json
from i18n import t, get_current_language


class NotionTypesetter:
    """Renders structured Notion Block Arrays for task documentation and human review."""

    @staticmethod
    def build_cognitive_audit_blocks(
        task_data: Dict[str, Any],
        audit_result: Dict[str, Any],
        lang: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Constructs the full suite of Notion blocks representing the Cognitive Audit Panel in the active language.

        Args:
            task_data: Dictionary with title, details, priority, source, etc.
            audit_result: Output from AIAuditEngine (risk_level, reasoning_trace, etc.).
            lang: Target language code ('en', 'es', 'de', 'ja', 'hi', 'fr'). Defaults to system config.

        Returns:
            List of Notion Block dictionaries ready for the Notion Pages/Blocks API.
        """
        if not lang:
            lang = get_current_language()

        blocks: List[Dict[str, Any]] = []
        risk_level = audit_result.get("risk_level", "LOW")
        confidence = audit_result.get("confidence_score", 0.85)
        category = audit_result.get("category", "General")
        reasoning_steps = audit_result.get("reasoning_trace", [])
        title = task_data.get("title", "Untitled Task")
        details = task_data.get("details", "No details provided.")
        priority = task_data.get("priority", "normal")

        # 1. Risk Banner Callout Block
        callout_color = "red_background" if risk_level in ("CRITICAL", "HIGH") else ("yellow_background" if risk_level == "MEDIUM" else "gray_background")
        callout_emoji = "🚨" if risk_level == "CRITICAL" else ("⚠️" if risk_level == "HIGH" else ("📋" if risk_level == "MEDIUM" else "✅"))
        banner_text = t("risk_evaluation_banner", lang=lang, emoji=callout_emoji, risk_level=risk_level, confidence=int(confidence * 100))

        blocks.append({
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [{"type": "text", "text": {"content": banner_text}}],
                "icon": {"emoji": callout_emoji},
                "color": callout_color,
            },
        })

        # 2. Section Heading: Executive Overview
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": t("task_specifications", lang=lang)}}],
            },
        })

        # 3. Payload Details Paragraph
        cat_label = t("category_label", lang=lang)
        prio_label = t("requested_priority", lang=lang)
        sum_label = t("task_summary", lang=lang)

        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"type": "text", "text": {"content": f"{cat_label}: {category} | {prio_label}: {priority.upper()}\n"}},
                    {"type": "text", "text": {"content": f"{sum_label}: {details}"}},
                ],
            },
        })

        # 4. Divider Block
        blocks.append({"object": "block", "type": "divider", "divider": {}})

        # 5. Collapsible Reasoning Toggle Block (Chain-of-Thought)
        step_children = []
        for step in reasoning_steps:
            step_children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": step}}],
                },
            })

        blocks.append({
            "object": "block",
            "type": "toggle",
            "toggle": {
                "rich_text": [{"type": "text", "text": {"content": t("cot_reasoning_toggle", lang=lang)}}],
                "children": step_children,
            },
        })

        # 6. Human-in-the-Loop Checklist (To-Do Blocks)
        blocks.append({
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [{"type": "text", "text": {"content": t("human_verification_checkpoints", lang=lang)}}],
            },
        })

        verification_items = [
            t("verify_scope_item", lang=lang, category=category),
            t("verify_accuracy_item", lang=lang),
            t("verify_biometric_item", lang=lang),
        ]

        for item in verification_items:
            blocks.append({
                "object": "block",
                "type": "to_do",
                "to_do": {
                    "rich_text": [{"type": "text", "text": {"content": item}}],
                    "checked": False,
                },
            })

        # 7. Outbound Draft Preview Toggle
        draft_summary = audit_result.get("draft_summary", "")
        teams_lbl = t("teams_message_label", lang=lang)
        blocks.append({
            "object": "block",
            "type": "toggle",
            "toggle": {
                "rich_text": [{"type": "text", "text": {"content": t("outbound_draft_toggle", lang=lang)}}],
                "children": [
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": f"{teams_lbl}:\n{audit_result.get('draft_teams_text', draft_summary)}"}}]
                        }
                    }
                ],
            },
        })

        # 8. Turn-Off Test Footer Callout
        blocks.append({
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [{"type": "text", "text": {"content": t("turn_off_test_badge", lang=lang)}}],
                "icon": {"emoji": "💡"},
                "color": "gray_background",
            },
        })

        return blocks

    @staticmethod
    def build_run_log_page_blocks(
        reasoning_steps: List[str],
        raw_payload: Dict[str, Any],
        action: str = "EXECUTION_DISPATCHED",
        operator_name: str = "Automated Execution Daemon",
        lang: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Programmatically generates native Notion blocks for Run Log page bodies in the target language.

        Generates:
        - Toggle 1: 🔍 View Step-by-Step AI Reasoning Steps (bulleted list of CoT steps)
        - Toggle 2: 📄 View Raw JSON Ingestion Payload (formatted code block with language 'json')
        - Callout: Header execution banner & Turn-Off Test offline badge

        Args:
            reasoning_steps: List of step strings taken by the pre-auditor.
            raw_payload: Dictionary representing raw external webhook payload.
            action: Transaction action name.
            operator_name: Authorizing user or daemon.
            lang: Target language code ('en', 'es', 'de', 'ja', 'hi', 'fr'). Defaults to system config.

        Returns:
            List of Notion block dictionaries ready for the Notion API.
        """
        if not lang:
            lang = get_current_language()

        blocks: List[Dict[str, Any]] = []

        # Header Callout Block
        header_text = t("run_log_audit_header", lang=lang, action=action, operator=operator_name)
        blocks.append({
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [{"type": "text", "text": {"content": header_text}}],
                "icon": {"emoji": "⚡"},
                "color": "blue_background",
            },
        })

        # Toggle 1: 🔍 View Step-by-Step AI Reasoning Steps (bulleted_list_item children)
        bullet_children = []
        if not reasoning_steps:
            reasoning_steps = [
                t("step1_default", lang=lang),
                t("step2_default", lang=lang),
                t("step3_default", lang=lang),
            ]

        for step in reasoning_steps:
            bullet_children.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": step}}],
                },
            })

        toggle1_title = t("run_log_toggle1_reasoning", lang=lang)
        blocks.append({
            "object": "block",
            "type": "toggle",
            "toggle": {
                "rich_text": [{"type": "text", "text": {"content": toggle1_title}}],
                "children": bullet_children,
            },
        })

        # Toggle 2: 📄 View Raw JSON Ingestion Payload (type: "code", language: "json")
        toggle2_title = t("run_log_toggle2_payload", lang=lang)
        json_str = json.dumps(raw_payload, indent=2) if isinstance(raw_payload, dict) else str(raw_payload)
        blocks.append({
            "object": "block",
            "type": "toggle",
            "toggle": {
                "rich_text": [{"type": "text", "text": {"content": toggle2_title}}],
                "children": [
                    {
                        "object": "block",
                        "type": "code",
                        "code": {
                            "rich_text": [{"type": "text", "text": {"content": json_str}}],
                            "language": "json",
                        },
                    }
                ],
            },
        })

        return blocks
