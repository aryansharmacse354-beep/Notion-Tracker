# Changelog

All notable changes to the **Notion Tracker** project will be documented in this file. This project strictly adheres to **Semantic Versioning (SemVer)** principles.

---

## [5.0.0-beta] — 2026-08-23
### Added
*   **Distributed Queueing & Throttling**: Added a thread-safe Token-Bucket Rate Limiter (`notion_enterprise_guard.py`) to safely limit API requests to $\le 2$ writes/second.
*   **Optimistic Concurrency Control (OCC)**: Built a row-level versioning system with cryptographic nonces and a Three-Way Merge Resolution Protocol to handle background race condition conflicts gracefully.
*   **HMAC-SHA256 Ingestion Verification**: Hardened webhook endpoints with strict HMAC validations and time-drift nonce guard filters to block replay and spoofing exploits.
*   **Bi-Directional Comment Hooks**: Created a secondary conversational daemon (`notion_comment_agent.py`) capable of parsing natural language `@AI` commands natively inside Notion comments.
*   **Workspace Auto-Recovery (Self-Healing)**: Added a state synchronization loop to automatically reconstruct accidentally archived or deleted Notion rows from a local cache.

---

## [4.0.0] — 2026-08-22
### Added
*   **Role-Based Access Control (RBAC)**: Integrated a third Notion database for user profiles, mapping cryptographic permissions and operator roles (e.g. Lead Developer, QA Tester).
*   **OpenCV Webcam facial Verification**: Built a localized webcam face-mapping mesh checkpoint on the Streamlit dashboard to authenticate administrative users.
*   **Multi-Factor SMS OTP Gating**: Added a randomized 6-digit cryptographic verification pin gate.
*   **SHA-256 Non-Repudiation Ledger**: Implemented deterministic digital log signing and a diagnostic verifier script (`verify_signatures.py`).

---

## [3.0.0] — 2026-08-15
### Added
*   **Dynamic Page Typesetting**: Shifted from raw JSON logs to programmatic body formatting using Notion's Blocks API to design elegant **Cognitive Audit Panels**.
*   **LangChain AI Risk Analyzer**: Embedded LLM cognitive risk scoring (LOW, MEDIUM, HIGH, CRITICAL) and automatic outbound communication draft compilers.
*   **ReportLab PDF Builder**: Added on-demand visually balanced document reporting.

---

## [2.0.0] — 2026-08-01
### Added
*   **Persistent Polling Daemon**: Replaced basic cron triggers with a persistent, container-ready python daemon.
*   **Dockerization**: Containerized the application using a customized multi-stage Dockerfile and docker-compose orchestration.

---

## [1.0.0] — 2026-07-15
### Added
*   **Initial Prototype Release**: Basic polling loops connecting manual Notion status updates with Teams hooks.
