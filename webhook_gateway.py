"""Webhook Ingestion Gateway for Notion Tracker.

FastAPI ASGI server receiving external webhooks, enforcing HMAC-SHA256 signature verification,
nonce replay protection, timestamp drift checks, AI pre-auditing, and Notion typesetting.
"""

import time
import json
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, Response, Header, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from config import WEBHOOK_SECRET, MAX_TIMESTAMP_DRIFT_SECONDS
from notion_enterprise_guard import (
    default_rate_limiter,
    default_nonce_guard,
    verify_hmac_signature,
)
from ai_audit_engine import AIAuditEngine
from notion_store import default_store
from audit_ledger import AuditLedger

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("notion_tracker.gateway")

app = FastAPI(
    title="Notion Tracker Ingestion Gateway",
    description="High-availability zero-trust webhook receiver with HMAC-SHA256 verification and AI Pre-Audits",
    version="5.0.0-beta",
)


class TaskPayload(BaseModel):
    task_title: str = Field(..., description="Title of the task")
    details: str = Field(..., description="Task details or payload")
    priority: str = Field(default="normal", description="Requested priority level")


class WebhookIngestRequest(BaseModel):
    event_id: str = Field(..., description="Unique event identifier")
    source: str = Field(default="Academic Registration Portal", description="Originating source system")
    timestamp: int = Field(..., description="Epoch UTC timestamp of event generation")
    payload: TaskPayload


import sys
import asyncio
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass


from pathlib import Path
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

STATIC_DIR = Path(__file__).resolve().parent / "static"
ASSETS_DIR = STATIC_DIR / "assets"

@app.get("/")
def get_spa_root():
    """Serves the 100vh single-page web application."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Notion Tracker Gateway Active", "portal": "/static/index.html"}

@app.get("/styles.css")
def get_styles():
    f = STATIC_DIR / "styles.css"
    if f.exists():
        return FileResponse(f, media_type="text/css")
    raise HTTPException(status_code=404, detail="File not found")

@app.get("/app.js")
def get_app_js():
    f = STATIC_DIR / "app.js"
    if f.exists():
        return FileResponse(f, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="File not found")

@app.get("/assets/{file_path:path}")
def get_asset_file(file_path: str):
    f = ASSETS_DIR / file_path
    if f.exists():
        return FileResponse(f)
    raise HTTPException(status_code=404, detail="Asset not found")

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/health")
def health_check():
    """Returns basic service health."""
    return {"status": "HEALTHY", "service": "Notion Tracker Gateway", "timestamp": time.time()}


@app.get("/api/v1/throttle-state")
def get_throttle_state():
    """Exposes current token bucket rate limiter telemetry."""
    return default_rate_limiter.get_state()



@app.post("/api/v1/verify-ledger")
def verify_ledger():
    """Runs on-demand cryptographic verification of the SHA-256 audit ledger."""
    logs = default_store.list_audit_logs()
    return AuditLedger.verify_ledger_chain(logs)


from report_builder import PDFReportBuilder
import io
import csv


@app.get("/api/v1/export/pdf")
def export_audit_pdf():
    """Generates and downloads the executive-grade PDF audit report."""
    tasks = default_store.list_tasks(include_archived=True)
    logs = default_store.list_audit_logs()
    pdf_bytes = PDFReportBuilder.generate_task_audit_pdf(tasks, logs)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=notion_tracker_audit_report.pdf"},
    )


@app.get("/api/v1/export/csv")
def export_audit_csv():
    """Exports audit logs and tasks as formatted CSV for Excel."""
    logs = default_store.list_audit_logs()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Log ID", "Record ID", "Run Name", "Action / Status", "Operator", "Timestamp", "SHA-256 Signature", "Prev Signature"])
    for l in logs:
        p_title = l.get("payload_data", {}).get("title", l.get("record_id", ""))
        writer.writerow([
            l.get("id"),
            l.get("record_id"),
            p_title,
            l.get("action"),
            l.get("operator_name"),
            l.get("timestamp"),
            l.get("signature"),
            l.get("prev_signature"),
        ])
    csv_bytes = output.getvalue().encode("utf-8")
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=notion_tracker_audit_ledger.csv"},
    )


@app.post("/api/v1/ledger/tamper-test")
def simulate_tamper_test():
    """Injects a simulated in-memory signature corruption to test tamper detection."""
    logs = default_store.list_audit_logs()
    if not logs:
        return {"status": "ALERT", "recalculated_records": 0, "mismatches_detected": 1, "tampered_pages": [{"entry_id": 1, "expected_signature": "tampered_mock", "recalculated_signature": "corrupt"}]}
    
    # Clone and mutate record #1
    tampered_logs = [dict(entry) for entry in logs]
    tampered_logs[0]["payload_data"] = dict(tampered_logs[0].get("payload_data", {}))
    tampered_logs[0]["payload_data"]["title"] = "UNAUTHORIZED_TAMPERED_PAYLOAD_DATA"
    return AuditLedger.verify_ledger_chain(tampered_logs)


from deduplication_engine import default_deduplicator
import traceback


class StageDraftRequest(BaseModel):
    edited_draft: str
    operator_name: Optional[str] = "Operator"



@app.get("/api/v1/dlq")
def get_dead_letter_queue():
    """Stage 5 DLQ: Returns all tasks currently isolated in the Dead-Letter Queue."""
    return default_store.get_dlq_tasks()


@app.post("/api/v1/dlq/{task_id}/resolve")
def resolve_dlq_task(task_id: str, operator_name: str = "Technical Auditor"):
    """Stage 5 DLQ: Re-triages a quarantined DLQ task back to Ready for Review."""
    task = default_store.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found in DLQ.")
    
    updated, _, _ = default_store.update_task_with_occ(
        task_id=task_id,
        base_record=task,
        local_updates={"status": "Ready for Review", "dlq_reason": "Resolved by Technical Auditor"},
        operator_name=operator_name,
    )
    return {"status": "RESOLVED", "task": updated}


@app.get("/api/v1/tasks")
def list_tasks():
    """Returns all active registered tasks from the live Notion store."""
    return default_store.list_tasks(include_archived=False)


@app.get("/api/v1/tasks/{task_id}")
def get_task(task_id: str):
    """Retrieves a specific task record."""
    task = default_store.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    return task


class ApproveTaskRequest(BaseModel):
    operator_name: Optional[str] = "Aryan Sharma"
    edited_draft: Optional[str] = None


@app.post("/api/v1/tasks/{task_id}/approve")
def approve_task(task_id: str, req: ApproveTaskRequest = ApproveTaskRequest()):
    """Stage 3 HITL: Approves a task with OCC, prioritizing human-edited draft wording."""
    task = default_store.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    
    local_updates = {"status": "Approved"}
    if req.edited_draft:
        local_updates["edited_draft"] = req.edited_draft
        local_updates["draft_teams_text"] = req.edited_draft

    updated, conflict, details = default_store.update_task_with_occ(
        task_id=task_id,
        base_record=task,
        local_updates=local_updates,
        operator_name=req.operator_name or "Aryan Sharma",
    )
    return {"status": "APPROVED", "task": updated, "conflict": conflict, "details": details}


@app.post("/api/v1/tasks/{task_id}/reject")
def reject_task(task_id: str, reason: str = "Rejected by Operator", operator_name: str = "Aryan Sharma"):
    """Rejects a task with OCC state transition."""
    task = default_store.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    
    updated, conflict, details = default_store.update_task_with_occ(
        task_id=task_id,
        base_record=task,
        local_updates={"status": "Rejected"},
        operator_name=operator_name,
    )
    return {"status": "REJECTED", "task": updated, "conflict": conflict}


class BatchApproveRequest(BaseModel):
    task_ids: list[str]
    operator_name: Optional[str] = "Aryan Sharma"


@app.post("/api/v1/tasks/batch-approve")
def batch_approve_tasks(req: BatchApproveRequest):
    """Notion Native Multi-Select Batch Approvals."""
    results = []
    for tid in req.task_ids:
        task = default_store.get_task(tid)
        if task:
            updated, conflict, _ = default_store.update_task_with_occ(
                task_id=tid,
                base_record=task,
                local_updates={"status": "Approved"},
                operator_name=req.operator_name or "Aryan Sharma [Batch]",
            )
            results.append({"task_id": tid, "status": "Approved", "version": updated.get("version")})
    return {"status": "BATCH_APPROVED", "count": len(results), "items": results}


@app.get("/api/v1/audit-logs")
def list_audit_logs():
    """Returns cryptographic audit log ledger entries."""
    return default_store.list_audit_logs()


@app.get("/api/v1/system-config")
def get_system_config():
    """Returns runtime daemon configuration."""
    return default_store.get_system_config()


@app.post("/api/v1/system-config")
def update_system_config(cfg: Dict[str, Any]):
    """Updates runtime daemon configuration."""
    return default_store.update_system_config(cfg)


@app.post("/api/v1/daemon/sync-now")
def trigger_daemon_sync():
    """Triggers an immediate unified daemon process cycle."""
    from main import NotionTrackerDaemon
    daemon = NotionTrackerDaemon()
    dispatched = daemon.process_cycle()
    return {"status": "SYNC_COMPLETE", "dispatched_count": dispatched}


class CommentCommandRequest(BaseModel):
    task_id: str
    comment_text: str
    author_name: Optional[str] = "Aryan Sharma"


@app.post("/api/v1/comment/process")
def process_comment_command(req: CommentCommandRequest):
    """Processes natural language @AI comment command."""
    from notion_comment_agent import NotionCommentAgent
    ok, response_msg = NotionCommentAgent.process_comment(
        task_id=req.task_id,
        comment_text=req.comment_text,
        author_name=req.author_name or "Aryan Sharma",
    )
    task = default_store.get_task(req.task_id)
    return {"success": ok, "response": response_msg, "task": task}


class VoiceCommandRequest(BaseModel):
    task_id: str
    audio_file: str
    operator_name: Optional[str] = "Aryan Sharma"


@app.post("/api/v1/voice/process")
def process_voice_command(req: VoiceCommandRequest):
    """Processes native Gemini 1.5 Flash voice command."""
    from notion_voice_agent import default_voice_agent
    parsed = default_voice_agent.process_voice_command(req.audio_file)
    exec_res = default_voice_agent.execute_voice_command_in_notion(
        task_id=req.task_id,
        command_data=parsed,
        operator_name=req.operator_name or "Aryan Sharma",
    )
    task = default_store.get_task(req.task_id)
    return {"success": True, "analysis": parsed, "execution": exec_res, "task": task}


@app.post("/api/v1/tasks/{task_id}/stage-draft")
def stage_human_draft(task_id: str, req: StageDraftRequest):
    """Stage 3 HITL: Stages a human operator edit for the AI draft before final approval."""
    task = default_store.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    
    updated = default_store.update_staged_draft(
        task_id=task_id,
        edited_draft=req.edited_draft,
        operator_name=req.operator_name or "Operator",
    )
    return {"status": "DRAFT_STAGED", "task": updated}


@app.post("/v1/webhook/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_webhook(
    request: Request,
    x_signature_hmac: Optional[str] = Header(None, alias="X-Signature-HMAC"),
    x_webhook_nonce: Optional[str] = Header(None, alias="X-Webhook-Nonce"),
    x_webhook_timestamp: Optional[str] = Header(None, alias="X-Webhook-Timestamp"),
):
    """Secure webhook ingestion endpoint.

    Validates HMAC signature, checks nonce uniqueness & timestamp drift,
    applies Deduplication Fingerprinting, runs cognitive AI pre-audit,
    and isolates unprocessable items into the Dead-Letter Queue (DLQ).
    """
    body_bytes = await request.body()

    # 1. Check for missing required security headers
    if not x_signature_hmac:
        logger.warning("Ingest Rejected: Missing X-Signature-HMAC header.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid X-Signature-HMAC authentication header.",
        )

    if not x_webhook_nonce or not x_webhook_timestamp:
        logger.warning("Ingest Rejected: Missing Nonce or Timestamp header.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required X-Webhook-Nonce or X-Webhook-Timestamp header.",
        )

    try:
        ts_int = int(x_webhook_timestamp)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Webhook-Timestamp header must be an integer epoch timestamp.",
        )

    # 2. Nonce Replay & Timestamp Drift Guard
    nonce_valid, nonce_reason = default_nonce_guard.validate_and_record(x_webhook_nonce, ts_int)
    if not nonce_valid:
        logger.warning(f"Ingest Forbidden: {nonce_reason}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Security Guard Rejection: {nonce_reason}",
        )

    # 3. HMAC-SHA256 Signature Verification
    if not verify_hmac_signature(body_bytes, x_signature_hmac, WEBHOOK_SECRET):
        logger.warning("Ingest Unauthorized: HMAC signature mismatch.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid HMAC signature. Request signature does not match pre-shared secret.",
        )

    # 4. Parse JSON Body
    try:
        data_json = json.loads(body_bytes.decode("utf-8"))
        req_obj = WebhookIngestRequest(**data_json)
    except Exception as e:
        logger.warning(f"Ingest Bad Request: Malformed JSON or invalid schema: {e}")
        # Stage 5 DLQ: Quarantine malformed payload rather than crashing silently
        err_id = f"dlq_malformed_{int(time.time())}"
        default_store.route_to_dlq(
            task_id=err_id,
            error_trace=f"Schema parsing error:\n{str(e)}\nRaw Body: {body_bytes.decode('utf-8', errors='ignore')[:300]}",
            reason="Malformed JSON or Schema Error",
            operator_name="DLQ Schema Guard",
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Malformed JSON payload or invalid schema: {str(e)}. Quarantined to DLQ.",
        )

    # 5. Stage 1: Deduplication Fingerprinting Check
    fingerprint = default_deduplicator.compute_fingerprint(
        title=req_obj.payload.task_title,
        details=req_obj.payload.details,
        source=req_obj.source,
        timestamp=float(ts_int),
    )
    is_unique, dup_task_id, rej_msg = default_deduplicator.check_and_record(
        fingerprint=fingerprint,
        task_id=req_obj.event_id,
        timestamp=float(ts_int),
    )
    if not is_unique:
        logger.warning(f"[DEDUPLICATION] Blocked duplicate submission for '{req_obj.payload.task_title}'")
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "status": "DUPLICATE_IGNORED",
                "message": rej_msg,
                "fingerprint": fingerprint,
                "original_task_id": dup_task_id,
            },
        )
    default_store.check_and_record_fingerprint(fingerprint, req_obj.event_id, req_obj.payload.task_title)

    # 6. Stage 2: AI Pre-Audit & DLQ Resilient Execution
    try:
        audit_res = AIAuditEngine.analyze_task(
            title=req_obj.payload.task_title,
            details=req_obj.payload.details,
            requested_priority=req_obj.payload.priority,
        )

        task_dict = {
            "id": req_obj.event_id,
            "title": req_obj.payload.task_title,
            "details": req_obj.payload.details,
            "priority": audit_res.suggested_priority,
            "category": audit_res.category,
            "status": "Ready for Review",
            "risk_level": audit_res.risk_level,
            "confidence_score": audit_res.confidence_score,
            "reasoning_trace": audit_res.reasoning_trace,
            "ai_reasoning_ledger": audit_res.ai_reasoning_ledger,
            "draft_summary": audit_res.draft_summary,
            "draft_email_html": audit_res.draft_email_html,
            "draft_teams_text": audit_res.draft_teams_text,
            "proposed_ai_draft": audit_res.proposed_ai_draft,
            "ingestion_fingerprint": fingerprint,
            "source": req_obj.source,
        }

        created_record = default_store.create_task(task_dict, operator_name=f"{req_obj.source} [Gateway]")
        logger.info(f"Task Ingested Successfully: {req_obj.event_id} - '{req_obj.payload.task_title}' (Risk: {audit_res.risk_level})")

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "status": "ACCEPTED",
                "message": "Signature verified, deduplicated, pre-audited and staged for human review.",
                "event_id": req_obj.event_id,
                "fingerprint": fingerprint,
                "risk_evaluation": {
                    "risk_level": audit_res.risk_level,
                    "confidence_score": audit_res.confidence_score,
                    "category": audit_res.category,
                },
                "ai_reasoning_ledger": audit_res.ai_reasoning_ledger,
                "proposed_ai_draft": audit_res.proposed_ai_draft,
            },
        )
    except Exception as exc:
        err_trace = traceback.format_exc()
        logger.error(f"[DLQ] Unhandled processing error during ingestion of {req_obj.event_id}: {exc}")
        
        # Route to DLQ rather than crashing or losing data
        dlq_task_dict = {
            "id": req_obj.event_id,
            "title": f"FAILED_INGEST: {req_obj.payload.task_title}",
            "details": req_obj.payload.details,
            "priority": req_obj.payload.priority or "normal",
            "category": "DLQ Exception",
            "status": "DLQ: Needs Technical Review",
            "risk_level": "CRITICAL",
            "confidence_score": 0.0,
            "reasoning_trace": [f"[DLQ Error] {str(exc)}"],
            "draft_summary": "Task processing failed. Quarantined in Dead-Letter Queue.",
            "draft_email_html": "",
            "draft_teams_text": "",
            "proposed_ai_draft": "",
            "ingestion_fingerprint": fingerprint,
            "dlq_error_trace": err_trace,
            "dlq_reason": str(exc),
            "source": req_obj.source,
        }
        default_store.create_task(dlq_task_dict, operator_name="DLQ Exception Quarantine")
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "status": "ROUTED_TO_DLQ",
                "message": "Processing exception occurred. Task quarantined in 'DLQ: Needs Technical Review'.",
                "event_id": req_obj.event_id,
                "error": str(exc),
            },
        )


if __name__ == "__main__":
    import uvicorn
    from config import GATEWAY_HOST, GATEWAY_PORT
    uvicorn.run(app, host=GATEWAY_HOST, port=GATEWAY_PORT)

