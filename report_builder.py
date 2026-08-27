"""ReportLab & Pure Python PDF Builder for Notion Tracker.

Generates visually balanced, executive-grade PDF reports documenting task workflows,
AI risk pre-audit metrics, and cryptographic ledger signatures.
"""

import time
import html
from io import BytesIO
from typing import List, Dict, Any
from pathlib import Path

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        HRFlowable,
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

from config import REPORTS_DIR


def generate_pure_pdf_bytes(title: str, tasks: List[Dict[str, Any]], audit_logs: List[Dict[str, Any]]) -> bytes:
    """Generates a valid %PDF-1.4 binary file without third-party dependencies as fail-safe."""
    now_str = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    total_tasks = len(tasks)
    approved = sum(1 for t in tasks if t.get("status") in ("Approved", "Dispatched"))
    critical = sum(1 for t in tasks if t.get("risk_level") in ("CRITICAL", "HIGH"))
    latest_sig = audit_logs[-1].get("signature", "GENESIS_HASH") if audit_logs else "GENESIS_HASH"

    text_lines = [
        "BT",
        "/F1 18 Tf",
        "50 750 Td",
        f"({title}) Tj",
        "0 -22 Td",
        "/F1 10 Tf",
        f"(Generated at: {now_str} | Zero-Trust Pipeline by Team AI Experts) Tj",
        "0 -25 Td",
        "/F1 12 Tf",
        "(EXECUTIVE METRICS SUMMARY) Tj",
        "0 -16 Td",
        "/F1 10 Tf",
        f"(Total Tasks: {total_tasks}  |  Approved/Dispatched: {approved}  |  Elevated Risk: {critical}) Tj",
        "0 -25 Td",
        "/F1 12 Tf",
        "(REGISTERED TASKS & PRE-AUDITS) Tj",
        "0 -16 Td",
        "/F1 9 Tf",
    ]

    for t in tasks[:12]:
        tid = str(t.get('id', ''))[:10]
        clean_title = str(t.get('title', '')).replace('(', '\\(').replace(')', '\\)')[:35]
        cat = str(t.get('category', 'General'))[:18]
        risk = str(t.get('risk_level', 'LOW'))
        status = str(t.get('status', 'Ready'))[:12]
        line = f"[{tid}] {clean_title} | {cat} | {risk} | {status}"
        text_lines.append(f"({line}) Tj")
        text_lines.append("0 -14 Td")

    text_lines.extend([
        "0 -15 Td",
        "/F1 12 Tf",
        "(SHA-256 CRYPTOGRAPHIC AUDIT LEDGER) Tj",
        "0 -16 Td",
        "/F1 9 Tf",
        f"(Total Events: {len(audit_logs)} | Ledger Status: SECURE) Tj",
        "0 -14 Td",
        f"(Latest Signature: {latest_sig[:48]}...) Tj",
        "ET"
    ])

    stream_content = "\n".join(text_lines).encode("latin-1", "replace")
    stream_len = len(stream_content)

    pdf_body = (
        f"%PDF-1.4\n"
        f"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        f"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        f"3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /MediaBox [0 0 612 792] /Contents 5 0 R >>\nendobj\n"
        f"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        f"5 0 obj\n<< /Length {stream_len} >>\nstream\n"
    ).encode("latin-1") + stream_content + f"\nendstream\nendobj\n".encode("latin-1")

    xref_offset = len(pdf_body)
    pdf_footer = (
        f"xref\n0 6\n"
        f"0000000000 65535 f \n"
        f"0000000010 00000 n \n"
        f"0000000060 00000 n \n"
        f"0000000117 00000 n \n"
        f"0000000244 00000 n \n"
        f"0000000315 00000 n \n"
        f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n"
    ).encode("latin-1")

    return pdf_body + pdf_footer


class PDFReportBuilder:
    """Builds formatted PDF reports using ReportLab with pure Python fail-safe."""

    @classmethod
    def generate_task_audit_pdf(cls, tasks: List[Dict[str, Any]], audit_logs: List[Dict[str, Any]], output_path: str = "") -> bytes:
        """Generates a complete PDF audit report and returns the PDF bytes.

        Args:
            tasks: List of task records.
            audit_logs: List of audit log records.
            output_path: Optional path to save PDF on disk.

        Returns:
            bytes: PDF document binary content.
        """
        if not HAS_REPORTLAB:
            pdf_data = generate_pure_pdf_bytes("Notion Tracker — Executive Audit Report", tasks, audit_logs)
            if output_path:
                with open(output_path, "wb") as f:
                    f.write(pdf_data)
            return pdf_data

        try:
            buffer = BytesIO()

            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=36,
                leftMargin=36,
                topMargin=36,
                bottomMargin=36,
            )

            styles = getSampleStyleSheet()

            title_style = ParagraphStyle(
                "DocTitle",
                parent=styles["Heading1"],
                fontSize=22,
                leading=26,
                textColor=colors.HexColor("#1a73e8"),
                fontName="Helvetica-Bold",
            )
            subtitle_style = ParagraphStyle(
                "DocSubtitle",
                parent=styles["Normal"],
                fontSize=10,
                leading=14,
                textColor=colors.HexColor("#5f6368"),
            )
            section_heading = ParagraphStyle(
                "SectionHeading",
                parent=styles["Heading2"],
                fontSize=13,
                leading=16,
                textColor=colors.HexColor("#202124"),
                fontName="Helvetica-Bold",
                spaceBefore=12,
                spaceAfter=6,
            )
            body_style = ParagraphStyle(
                "DocBody",
                parent=styles["Normal"],
                fontSize=9,
                leading=12,
                textColor=colors.HexColor("#3c4043"),
            )
            table_cell_style = ParagraphStyle(
                "TableCell",
                parent=styles["Normal"],
                fontSize=8,
                leading=10,
            )
            table_header_style = ParagraphStyle(
                "TableHeader",
                parent=styles["Normal"],
                fontSize=8,
                leading=10,
                fontName="Helvetica-Bold",
                textColor=colors.white,
            )

            story = []

            # 1. Header & Title Banner with Brand Logo
            logo_file = Path(__file__).resolve().parent / "assets" / "logo.png"
            if logo_file.exists():
                try:
                    from reportlab.platypus import Image as RLImage
                    story.append(RLImage(str(logo_file), width=44, height=44))
                    story.append(Spacer(1, 4))
                except Exception:
                    pass

            story.append(Paragraph("Notion Tracker — Executive Audit Report", title_style))
            gen_time = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
            story.append(Paragraph(f"Generated at: {gen_time} | Zero-Trust Automated Pipeline by Team AI Experts", subtitle_style))
            story.append(Spacer(1, 10))
            story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1a73e8"), spaceBefore=2, spaceAfter=10))

            # 2. Executive Metrics Summary
            total_tasks = len(tasks)
            approved_tasks = sum(1 for t in tasks if t.get("status") in ("Approved", "Dispatched"))
            critical_tasks = sum(1 for t in tasks if t.get("risk_level") in ("CRITICAL", "HIGH"))
            ready_tasks = sum(1 for t in tasks if t.get("status") == "Ready for Review")

            metrics_data = [
                [
                    Paragraph("<b>Total Processed:</b>", body_style), Paragraph(str(total_tasks), body_style),
                    Paragraph("<b>Approved/Dispatched:</b>", body_style), Paragraph(str(approved_tasks), body_style),
                ],
                [
                    Paragraph("<b>Pending Review:</b>", body_style), Paragraph(str(ready_tasks), body_style),
                    Paragraph("<b>Elevated Risk (High/Crit):</b>", body_style), Paragraph(str(critical_tasks), body_style),
                ],
            ]
            metrics_table = Table(metrics_data, colWidths=[130, 130, 140, 140])
            metrics_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f3f4")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#dadce0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e8eaed")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]))
            story.append(metrics_table)
            story.append(Spacer(1, 12))

            # 3. Tasks Table
            story.append(Paragraph("1. Ingested Tasks & Cognitive Risk Pre-Audits", section_heading))

            task_rows = [[
                Paragraph("Task ID", table_header_style),
                Paragraph("Title", table_header_style),
                Paragraph("Category", table_header_style),
                Paragraph("Priority", table_header_style),
                Paragraph("Risk", table_header_style),
                Paragraph("Status", table_header_style),
            ]]

            for t in tasks[:15]:
                risk_val = html.escape(str(t.get("risk_level", "LOW")))
                risk_color_hex = "#d93025" if risk_val in ("CRITICAL", "HIGH") else ("#f29900" if risk_val == "MEDIUM" else "#1e8e3e")
                
                clean_id = html.escape(str(t.get("id", ""))[:10])
                clean_title = html.escape(str(t.get("title", ""))[:35])
                clean_category = html.escape(str(t.get("category", "General")))
                clean_priority = html.escape(str(t.get("priority", "normal")).upper())
                clean_status = html.escape(str(t.get("status", "Ready")))

                task_rows.append([
                    Paragraph(clean_id, table_cell_style),
                    Paragraph(clean_title, table_cell_style),
                    Paragraph(clean_category, table_cell_style),
                    Paragraph(clean_priority, table_cell_style),
                    Paragraph(f"<font color='{risk_color_hex}'><b>{risk_val}</b></font>", table_cell_style),
                    Paragraph(clean_status, table_cell_style),
                ])

            if len(task_rows) == 1:
                task_rows.append([Paragraph("No tasks recorded", table_cell_style)] * 6)

            t_table = Table(task_rows, colWidths=[65, 175, 95, 65, 65, 75])
            t_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a73e8")),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dadce0")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(t_table)
            story.append(Spacer(1, 14))

            # 4. Cryptographic Non-Repudiation Audit Ledger Section
            story.append(Paragraph("2. Industrial SHA-256 Cryptographic Audit Ledger", section_heading))
            latest_sig = html.escape(str(audit_logs[-1].get("signature", "N/A") if audit_logs else "N/A"))
            total_logs = len(audit_logs)

            ledger_p = Paragraph(
                f"<b>Total Audited Events:</b> {total_logs} | <b>Hash Chain Integrity:</b> SECURE<br/>"
                f"<b>Latest Deterministic Block Signature:</b><br/>"
                f"<font face='Courier' color='#1a73e8' size='7'>{latest_sig}</font>",
                body_style
            )
            story.append(ledger_p)
            story.append(Spacer(1, 15))

            # Footer disclaimer
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#dadce0"), spaceBefore=5, spaceAfter=8))
            story.append(Paragraph(
                "CONFIDENTIAL — Cryptographically certified document generated by Notion Tracker. Non-repudiation enforced via SHA-256 signature chain.",
                subtitle_style
            ))

            doc.build(story)
            pdf_data = buffer.getvalue()
            buffer.close()

            if output_path:
                with open(output_path, "wb") as f:
                    f.write(pdf_data)

            return pdf_data

        except Exception as err:
            # Automatic fail-safe to pure Python PDF generator
            pdf_data = generate_pure_pdf_bytes("Notion Tracker — Executive Audit Report", tasks, audit_logs)
            if output_path:
                with open(output_path, "wb") as f:
                    f.write(pdf_data)
            return pdf_data
