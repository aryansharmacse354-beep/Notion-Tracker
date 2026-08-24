# Contributing to Notion Tracker

First off, thank you for considering contributing to **Notion Tracker**! It is developers like you who make this a production-grade enterprise platform.

---

## 👥 Our Core Roles

*   **Aryan Sharma (Lead Developer & Architect)**: Oversees database connectors, webhook ingestion pipelines, LangChain integrations, and core worker polling routines.
*   **Atul Yadav (Code Quality Testing & Security)**: Manages our testing suites, mock schemas, security hardening, and Docker containerizations.

---

## 🛠️ Coding Guidelines

### Python Coding Style
*   All code must adhere strictly to **PEP 8** style guidelines.
*   Use descriptive, snake_case naming conventions for functions and variables.
*   Every public-facing module, class, and function must include descriptive docstrings using Google Style formatting.

### Robust Logging
*   Never use standard `print()` statements inside production automation workers. Always use python’s standard `logging` library.
*   Ensure that log levels are set appropriately: `INFO` for trace points, `WARNING` for human-in-the-loop gates, and `ERROR` or `CRITICAL` for database retry failures.

---

## 🧪 Quality Assurance & Testing

Before submitting any Pull Request, developers must verify that their changes do not break our zero-network, mocked test suite:

### 1. Run the Test Suite Locally
```bash
python -m unittest test_tracker.py
```

### 2. Verify Resiliencies
All test runs must return a perfect **`OK` passing rating (4/4 tests passed)**. The suite verifies:
*   Cryptographic HMAC and SHA-256 signatures.
*   Optimistic Concurrency Control (OCC) data merges.
*   Token-Bucket rate-limiting throttling behaviors.
*   LangChain classification and risk pre-audit mock outputs.

---

## 🔀 Branch Strategy

We adhere to a clean, structured git branching workflow:
1.  **`main`**: Our production-ready release branch. Never commit directly to `main`.
2.  **`develop`**: The primary integration branch for team verification.
3.  **Feature Branches** (`feature/your-feature-name`): Isolated branches for individual tasks or bug fixes. Always create a feature branch off `develop`.
