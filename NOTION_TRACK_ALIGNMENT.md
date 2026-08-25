# Notion Tracker: Complete Alignment with Hackathon Problem Statement & Rubric

## 1. The Problem We Are Killing Cleanly
### Real-World Job: College Lab Provisions & Logistics Dispatches
- Inbound Trigger: Messy requests from forms, WhatsApp, or emails arrive at /v1/webhook/ingest.
- AI Pre-Audit: NLP extracts fields, computes risk level, and drafts outbound replies.
- Typesetting in Notion: Formats human-readable Notion page blocks (Callout risk banner, reasoning trace, draft preview, checklist).
- Human-in-the-Loop (HITL): High-risk tasks pause at Ready for Review for coordinator status toggle.
- Real Outbound Action: Dispatches MS Teams Adaptive Cards, SendGrid HTML emails, and PDF invoices.
- Proof in Run Log: Every action writes an immutable, timestamped SHA-256 sealed record to the Run Log.

## 2. Core Pillars & Tests
- Autonomous Engine: Persistent worker daemon (main.py) runs continuously.
- The Turn-Off Test (PASSED): Notion pages are styled with native blocks. When servers are off, the workspace remains 100% structured and readable.
- The Delete-Repo Test (PASSED): Custom logic, OCC 3-way merge, token-bucket throttling, and cryptographic seals live in Python code.
