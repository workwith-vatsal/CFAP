# CFAP — Cognitive Feedback Analytics Platform

## Overview

CFAP (**Cognitive Feedback Analytics Platform**) is an AI-powered customer feedback analytics and business intelligence platform designed to help organizations transform customer feedback into actionable insights.

Users can upload CSV and Excel datasets, evaluate data quality, analyze customer sentiment and emotions, discover recurring topics, explore explainable AI results, and generate business intelligence reports.

### Key Features

- **Sentiment Analysis:** BERT-based customer sentiment classification.
- **Emotion Detection:** Seven-class emotion classification using DistilRoBERTa.
- **Topic Discovery:** Unsupervised semantic topic modeling with BERTopic.
- **Explainable AI:** SHAP-based model explanations and token-level attribution.
- **Business Intelligence:** Interactive dashboards, sentiment distributions, cross-dimensional analysis, and aggregated insights.
- **Dataset-Grounded AI Assistant:** Conversational analysis based on authorized dataset and analysis results.
- **PDF Reporting:** Structured business reports with analytical summaries, visualizations, and explainability results.
- **Dataset Management:** CSV/XLSX upload, data quality assessment, previews, and dataset lifecycle management.
- **Anonymized Benchmarking:** Aggregate comparisons subject to minimum cohort eligibility requirements.
- **Administration and Auditing:** Role-based administrative functionality, audit logs, and operational metrics.
- **Authentication and Account Security:** Email OTP verification, password recovery, secure session cookies, and Google OAuth 2.0.
- **Internationalization:** English and Hindi interfaces.

CFAP is designed for multi-user operation, with server-side authorization and tenant isolation protecting private datasets and associated analytical results.

---

## Technology Stack

### Backend

- **Framework:** FastAPI
- **Language:** Python 3.11+
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy 2.0
- **Database Migrations:** Alembic
- **Validation:** Pydantic
- **Authentication:** JWT, bcrypt, email OTP verification, and Google OAuth 2.0
- **Background Processing:** Celery
- **Message Broker and Result Backend:** Redis
- **Data Processing:** Pandas and NumPy
- **Testing:** Pytest

### AI and Machine Learning

- **Sentiment Analysis:** `nlptown/bert-base-multilingual-uncased-sentiment`
- **Emotion Detection:** `j-hartmann/emotion-english-distilroberta-base`
- **Text Embeddings:** `sentence-transformers/all-MiniLM-L6-v2`
- **Topic Modeling:** BERTopic, UMAP, and HDBSCAN
- **Explainable AI:** SHAP
- **Business Intelligence:** Python-based analytical processing and visualization
- **PDF Generation:** ReportLab and Matplotlib

The sentiment model's five-star output is mapped into CFAP's positive, neutral, and negative sentiment categories. The emotion model is English-oriented, so its results should be interpreted with that limitation in mind.

### Frontend

- **Framework:** Next.js 16 with App Router
- **UI Library:** React 19
- **Language:** TypeScript
- **Styling:** Tailwind CSS v4
- **Icons:** Lucide React
- **Internationalization:** Centralized English (`en`) and Hindi (`hi`) translations
- **Build and Quality Checks:** Next.js production build and ESLint

---

## Architecture

CFAP follows a modular application architecture.

```text
CFAP
├── Frontend
│   ├── Next.js App Router
│   ├── Authentication and Profile
│   ├── Dataset Management
│   ├── Analysis Dashboards
│   ├── Explainable AI
│   ├── AI Assistant
│   ├── Benchmarking
│   └── Reports and Administration
│
├── FastAPI Backend
│   ├── Authentication and Authorization
│   ├── Dataset Ingestion and Data Quality
│   ├── AI/NLP Analysis Services
│   ├── Explainability and Analytics
│   ├── Dataset-Grounded Assistant
│   ├── PDF Reporting
│   ├── Benchmarking
│   └── Audit Logging
│
├── Background Processing
│   ├── Celery Analysis Tasks
│   └── Celery Report Tasks
│
└── Data and Infrastructure
    ├── PostgreSQL
    ├── Redis
    └── Local Dataset and Report Storage
```

The backend exposes REST APIs to the frontend. PostgreSQL stores application metadata and analytical results, while Redis supports background job processing through Celery.

Long-running analysis and report-generation operations are designed to execute as background tasks instead of blocking normal API requests.

---

## Getting Started

### One-Click Local Startup (Recommended)

You can launch the complete CFAP application with all dependencies by double-clicking:

`run.bat`

located in the project root directory (`C:\Users\DELL\Desktop\CFAP\run.bat`), or by executing it from a terminal:

```cmd
.\run.bat
```

#### What `run.bat` Does Automatically:
1. **Resolves Project Root:** Automatically determines absolute paths independent of working directory.
2. **Validates Prerequisites:** Checks availability of Python virtual environment, Node.js/npm, curl, and WSL 2.
3. **Enforces Process Environment:** Sets `REDIS_URL=redis://127.0.0.1:6380/0`, `CELERY_BROKER_URL=redis://127.0.0.1:6380/0`, and `CELERY_RESULT_BACKEND=redis://127.0.0.1:6380/0`.
4. **Verifies PostgreSQL:** Confirms the `postgresql-x64-17` Windows service is running and validates database query execution from Python.
5. **Initializes Persistent Redis:** Verifies Redis on `127.0.0.1:6380`. If WSL is stopped or idle, launches a keepalive session (`CFAP - Redis (WSL)`) to keep the Ubuntu WSL distribution active and ensures `service redis-server` is running.
6. **Starts FastAPI Backend:** Launches the backend in a dedicated console window (`CFAP - Backend (FastAPI)`) and probes `http://127.0.0.1:8000/health` with bounded retry.
7. **Starts Celery Worker:** Launches Celery in a dedicated window (`CFAP - Celery Worker`) with `--pool=solo`, connects to Redis on 6380, and verifies registered tasks (`run_analysis_pipeline`, `generate_pdf_report`).
8. **Starts Next.js Frontend:** Verifies `frontend/node_modules` (runs `npm ci` with lockfile if missing) and launches `npm run dev` in a dedicated window (`CFAP - Frontend (Next.js)`).
9. **Opens Web Browser:** Once the frontend is responsive, automatically opens `http://localhost:3000` in the default browser.
10. **Idempotent:** Running `run.bat` a second time safely detects running services and does not create duplicate processes.

#### Safe Shutdown:

To safely stop all CFAP application processes, double-click:

`stop.bat`

or run:

```cmd
.\stop.bat
```

`stop.bat` targets only CFAP console windows and application processes (FastAPI backend, Celery worker, Next.js server, and WSL keepalive session). It does **not** terminate PostgreSQL or general WSL processes.

---

### Application URLs and Endpoints

- **Web Dashboard:** `http://localhost:3000`
- **Backend API:** `http://127.0.0.1:8000`
- **Backend Health Check:** `http://127.0.0.1:8000/health`
- **Database Health Check:** `http://127.0.0.1:8000/health/db`
- **Interactive API Documentation (Swagger):** `http://127.0.0.1:8000/docs`

---

### Manual / Step-by-Step Startup

If running components manually in separate terminals:

#### 1. Redis Configuration & Startup
In the local development environment, Redis runs persistently inside Ubuntu WSL on port `6380`:
- **Configuration File:** `/etc/redis/redis.conf`
- **Active Backup (Port 6380):** `/var/backups/redis.conf.backup_20261022` (captures the verified port 6380 configuration)
- **Binding:** `127.0.0.1 -::1` with `protected-mode yes` (safe loopback only, never exposed to LAN)
- **Start Command:**
  ```powershell
  wsl -d Ubuntu -u root -- service redis-server start
  ```
- **Reverting to Port 6379 (if ever needed):**
  > [!NOTE]
  > `/var/backups/redis.conf.backup_20261022` is a backup of the port 6380 configuration, not the original port 6379 default. To revert to the original port 6379, modify the port directive directly:
  ```powershell
  wsl -d Ubuntu -u root -- sed -i 's/^port 6380/port 6379/' /etc/redis/redis.conf
  wsl -d Ubuntu -u root -- systemctl restart redis-server
  ```
- **Restoring Port 6380 Configuration:**
  ```powershell
  wsl -d Ubuntu -u root -- cp /var/backups/redis.conf.backup_20261022 /etc/redis/redis.conf
  wsl -d Ubuntu -u root -- systemctl restart redis-server
  ```

#### 2. Start PostgreSQL
Ensure Windows service `postgresql-x64-17` is running:
```powershell
sc query postgresql-x64-17
```

#### 3. Start Backend (Terminal 1)
```powershell
$env:REDIS_URL="redis://127.0.0.1:6380/0"
$env:CELERY_BROKER_URL="redis://127.0.0.1:6380/0"
$env:CELERY_RESULT_BACKEND="redis://127.0.0.1:6380/0"
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

#### 4. Start Celery Worker (Terminal 2)
```powershell
$env:REDIS_URL="redis://127.0.0.1:6380/0"
$env:CELERY_BROKER_URL="redis://127.0.0.1:6380/0"
$env:CELERY_RESULT_BACKEND="redis://127.0.0.1:6380/0"
.\.venv\Scripts\python.exe -m celery -A backend.app.core.celery_app.celery_app worker --loglevel=info --pool=solo
```

#### 5. Start Frontend (Terminal 3)
```powershell
cd frontend
npm run dev
```

#### 6. Run Test Suite
```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

#### 7. Run Frontend Quality Checks
```powershell
cd frontend
npm run lint
npm run build
```

---

## Architecture and Authentication

### Registration and Email Verification

Registration uses a six-digit, time-limited email OTP. OTP verification and account state are enforced by the backend.

### Session Management

The authentication flow uses JWTs and secure, HttpOnly cookies with SameSite settings. Bearer authentication is also supported for compatible API clients.

Cookie settings and allowed origins must be configured appropriately when deploying beyond localhost.

### Password Recovery

The platform includes password recovery and reset flows designed to avoid unnecessary account enumeration and to validate verification challenges before sensitive account changes.

### Password Modification

Authenticated users can change their passwords after validating their current password.

### Google OAuth 2.0

Google OAuth uses a server-side token exchange, state validation, ID-token verification, and a cookie-based session handoff.

OAuth redirect URIs and credentials must match the configuration of the Google Cloud project. Never expose OAuth client secrets in frontend code.

---

## Dataset Management and Analysis

CFAP is designed to analyze datasets supplied by individual users rather than relying on a single hard-coded research dataset.

The dataset workflow includes:

1. CSV/XLSX upload and validation.
2. Dataset metadata extraction and preview.
3. Feedback-column detection.
4. Data quality assessment.
5. Analysis initiation and background processing.
6. Sentiment, emotion, embedding, and topic analysis.
7. Persisted analytical results and visualizations.
8. Explainability, reporting, and dataset-grounded questions.

Upload size, row count, column count, and related ingestion limits are configurable through application settings.

### Analytical Interpretation

Analytical results should be interpreted according to the capabilities and limitations of the underlying models and source dataset.

In particular:

- Sentiment classification is mapped from the model's five-star output.
- The emotion classifier is English-oriented.
- Topic modeling depends on the content, size, and diversity of the dataset.
- SHAP explanations describe model behavior; they do not establish causality.
- Net Sentiment Score (NSS) and CFAP-derived composite scores should be interpreted using their documented calculation rules.
- Benchmarking describes aggregate comparisons and should not be presented as evidence of causal relationships.

---

## Dataset-Grounded AI Assistant

The AI Assistant is designed to answer questions using the user's authorized, completed analysis results and relevant dataset context.

Its architecture includes question routing, context construction, analytics retrieval, model-provider integration, grounding validation, and response generation.

The assistant must not be treated as the source of truth for numerical metrics. CFAP's persisted analytical results remain authoritative.

Provider selection and model settings are configurable. A valid provider credential and a supported model are required for live provider access. Mock providers are intended for testing or offline scenarios and must not be presented as live production AI.

Assistant responses should distinguish observed associations from causal conclusions and should not disclose information belonging to another user.

---

## Reports and Export

The reporting system is designed to generate structured PDF reports from authorized datasets and completed analyses.

Depending on report type and available analysis results, the reporting workflow can include:

- Executive summaries and key performance indicators.
- Sentiment and emotion distributions.
- Topic analysis.
- Business intelligence visualizations.
- Explainability findings.
- Dataset-grounded assistant content where available.
- Appropriate reporting limitations for unavailable analytical dimensions.

Report generation is implemented as a background-task workflow. End-to-end runtime verification of live Celery report generation and authorized report downloads remains part of the current acceptance work.

---

## Administration, Benchmarking, and Audit Logging

### Administrative Portal

The administrative functionality includes role-based access control, aggregated system metrics, user governance, and audit-log access.

Authorization must be enforced by the backend rather than relying on frontend navigation or visibility.

Administrative capabilities are intended to operate on authorized operational metadata without granting unrestricted access to private customer feedback.

### Anonymized Benchmarking

Benchmarking is designed to compare eligible aggregate metrics across distinct tenant datasets and completed analyses.

The configured minimum sample threshold is intended to suppress outputs when the eligible cohort is too small. The README's documented threshold is five, subject to confirmation against the current effective configuration.

Benchmarking must not expose individual customer comments, dataset names, filenames, or competitor identities. Aggregate comparisons are descriptive and should not be interpreted as causal findings.

### Audit Logging

Audit logs record selected security-sensitive and operational events.

The implementation is designed to filter sensitive data from audit metadata and support configurable retention. Audit logs should never contain passwords, OTP values, signing secrets, API keys, or raw customer feedback.

---

## Security and Data Isolation

Security is a core design requirement for CFAP.

The implementation includes:

- Password hashing and time-limited verification codes.
- Authenticated API access and server-side authorization.
- Tenant-scoped dataset, analysis, assistant, and report access.
- Protected file-storage operations and validation.
- Sanitized health-check responses.
- Audit logging for selected events.
- Configuration-based secrets management.
- Automated security and authorization tests.

Cross-tenant access must be denied even when a user knows another resource's identifier. Frontend restrictions alone are not an authorization boundary.

Before external deployment, review cookie security, HTTPS, CORS, secrets management, storage permissions, database access, background worker configuration, logging, monitoring, backups, and retention policies.

---

## Testing and Verification Status

### Verified Runtime Verification

The runtime verification conducted on October 22, 2026, confirmed:

| Check | Verified Result | Details |
|---|---|---|
| Persistent WSL Redis | PASS | Configured on port `6380` in `/etc/redis/redis.conf`, backup saved |
| Windows TCP & Python Redis | PASS | Windows connects to `127.0.0.1:6380`, Python client returns `PONG` (`True`) |
| Celery Worker & Tasks | PASS | Connected to `redis://127.0.0.1:6380/0`, registered `run_analysis_pipeline` and `generate_pdf_report` |
| Live Background Tasks (PDF) | PASS | Queued into Celery broker on 6380, rendered PDF, persisted file, validated `%PDF-1.4` |
| Multi-Tenant Isolation | PASS | Cross-user report access & download blocked with 404 / ValueError |
| Backend automated test suite | PASS (116/116) | 116 passed, 0 failed in 46.67s |
| Frontend ESLint | PASS | 0 errors, 0 warnings |
| TypeScript Check | PASS | 0 errors (`npx tsc --noEmit`) |
| Frontend Production Build | PASS | Next.js 16.3.5 built 21 static and dynamic routes cleanly |
| One-Click Startup (`run.bat`) | PASS | Launches PostgreSQL check, Redis on 6380, Backend, Celery, and Frontend |
| Safe Shutdown (`stop.bat`) | PASS | Terminates only CFAP console windows and child processes without killing OS services |
| Idempotency | PASS | Second invocation reuses active services without conflict |

### Verified End-to-End Acceptance

The following workflows have been verified with live execution evidence:
- **Persistent Redis on 6380:** Enabled and active in Ubuntu WSL under systemd, persistent across reboots and idle periods via keepalive session.
- **FastAPI Backend & Database:** `/health` returns `healthy` and `/health/db` confirms PostgreSQL query execution.
- **Celery Worker Execution:** Connected to `127.0.0.1:6380`, accepts dispatched tasks from FastAPI.
- **Live PDF Report Workflow:** Generated valid ReportLab PDF via background Celery task, saved to tenant-isolated storage path, verified PDF header bytes, and confirmed multi-tenant isolation.
- **Automated Test Coverage:** Full suite of 116 unit and integration tests passing.

---

## Project Status

The project is organized into eight implementation phases:

1. **Authentication and Database Foundation:** User models, authentication, account verification, and security foundations.
2. **Frontend and Authentication UI:** Next.js application, authentication pages, and protected application routes.
3. **Dataset Management and Data Quality:** Uploads, previews, quality analysis, and dataset lifecycle management.
4. **AI/NLP Analysis Engine:** Sentiment, emotion, embeddings, topic modeling, and analytical aggregation.
5. **Explainable AI and Business Intelligence:** SHAP-based explanations and advanced analytical dashboards.
6. **Dataset-Grounded AI Assistant:** Question routing, context building, provider integration, and grounding validation.
7. **PDF Reporting and Export:** Report data assembly, visualization, and PDF generation.
8. **Administration, Benchmarking, and Hardening:** Administrative functionality, aggregate benchmarking, audit logging, and security checks.

The eight phases have been implemented according to the current project reports. Runtime stabilization and end-to-end acceptance remain outstanding.

---

## Development Principles

CFAP follows these principles:

- **Dataset independence:** Results should be derived from uploaded data and actual analytical outputs.
- **Tenant isolation:** Users may access only resources for which they are authorized.
- **Evidence-based analytics:** Metrics should originate from persisted analytical results, not hard-coded examples.
- **Explainability:** Model explanations must be presented with appropriate limitations.
- **Privacy:** Raw customer feedback and secrets must not leak into logs, benchmarks, or unauthorized reports.
- **Incremental development:** Changes should preserve completed functionality and be validated with relevant tests.
- **Transparent status reporting:** Automated tests, local runtime checks, and production-readiness claims must remain distinct.

---

## License and Contributions

No license or contribution policy is specified in this README. Add the applicable project license and contribution guidelines before distributing the project publicly.
