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


@app.post("/v1/webhook/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_webhook(
    request: Request,
    x_signature_hmac: Optional[str] = Header(None, alias="X-Signature-HMAC"),
    x_webhook_nonce: Optional[str] = Header(None, alias="X-Webhook-Nonce"),
    x_webhook_timestamp: Optional[str] = Header(None, alias="X-Webhook-Timestamp"),
):
    """Secure webhook ingestion endpoint.

    Validates HMAC signature, checks nonce uniqueness & timestamp drift,
    runs cognitive AI pre-audit, and persists task into the Notion store.
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Malformed JSON payload or invalid schema: {str(e)}",
        )

    # 5. Stage 2: AI Pre-Audit Engine Evaluation
    audit_res = AIAuditEngine.analyze_task(
        title=req_obj.payload.task_title,
        details=req_obj.payload.details,
        requested_priority=req_obj.payload.priority,
    )

    # 6. Stage 3: Dynamic Store Insertion
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
        "draft_summary": audit_res.draft_summary,
        "draft_email_html": audit_res.draft_email_html,
        "draft_teams_text": audit_res.draft_teams_text,
        "source": req_obj.source,
    }

    created_record = default_store.create_task(task_dict, operator_name=f"{req_obj.source} [Gateway]")

    logger.info(f"Task Ingested Successfully: {req_obj.event_id} - '{req_obj.payload.task_title}' (Risk: {audit_res.risk_level})")

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "status": "ACCEPTED",
            "message": "Signature verified, payload pre-audited and queued for human review.",
            "event_id": req_obj.event_id,
            "risk_evaluation": {
                "risk_level": audit_res.risk_level,
                "confidence_score": audit_res.confidence_score,
                "category": audit_res.category,
            },
        },
    )


if __name__ == "__main__":
    import uvicorn
    from config import GATEWAY_HOST, GATEWAY_PORT
    uvicorn.run(app, host=GATEWAY_HOST, port=GATEWAY_PORT)
