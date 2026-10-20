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

### Prerequisites

Install and configure the following before running CFAP:

- Python 3.11+
- Node.js compatible with Next.js 16 and npm
- PostgreSQL 15+ (PostgreSQL 17 is used in the current development environment)
- Redis reachable by the backend and Celery worker
- Git

A working internet connection may be required to download dependencies and AI models or use external services such as email delivery, Google OAuth, and a configured LLM provider.

### 1. Clone or Open the Repository

If the repository is already on your computer:

```powershell
cd C:\Users\DELL\Desktop\CFAP
```

### 2. Configure Environment Variables

Create a local `.env` file from the example if you do not already have one:

```powershell
Copy-Item .env.example .env
```

Configure the required local database, authentication, email, Redis, and AI provider settings in `.env`, as applicable.

**Important security requirements:**

- Never commit `.env`.
- Never publish API keys, OAuth secrets, database passwords, JWT signing secrets, or email credentials.
- Keep `.env.example` limited to configuration names and safe example values.
- Do not replace an existing working `.env` file without first protecting its contents.

### 3. Set Up the Python Environment

Activate the existing virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the project dependencies:

```powershell
python -m pip install -r requirements.txt
```

The root `requirements.txt` references the backend dependency requirements.

### 4. Start PostgreSQL and Redis

Start PostgreSQL and ensure the configured database and database user exist.

Start Redis using the installation method configured for your environment. Redis must be reachable at the URL specified by the backend configuration.

In the current development environment, Redis is installed in WSL Ubuntu, while CFAP's Python backend runs on Windows. Windows-to-WSL Redis connectivity is still undergoing runtime verification. Do not assume that a healthy Redis service inside WSL automatically means that the Windows backend can connect to it.

### 5. Apply Database Migrations

From the repository root:

```powershell
alembic upgrade head
```

This applies the existing Alembic migrations to the configured database.

Do not reset or recreate the database as a routine troubleshooting step.

### 6. Start the FastAPI Backend

Open a PowerShell terminal in the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

The backend should listen at:

`http://127.0.0.1:8000`

The current health endpoints are:

- `GET /health`
- `GET /health/db`

Use these endpoints to check backend and database health.

### 7. Start the Celery Worker

Open a separate PowerShell terminal in the repository root:

```powershell
.\.venv\Scripts\python.exe -m celery -A backend.app.core.celery_app.celery_app worker --loglevel=info --pool=solo
```

The worker requires a working Redis connection. Confirm that it connects to its broker and registers the analysis and report tasks:

- `run_analysis_pipeline`
- `generate_pdf_report`

A worker process opening successfully is not sufficient evidence that background jobs are functioning. Check the worker logs and execute a real background workflow.

### 8. Start the Frontend

Open another PowerShell terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the local frontend address printed by Next.js, normally:

`http://localhost:3000`

The frontend communicates with the backend through the configured API client and application settings.

### 9. Run Backend Tests

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

The tests exercise backend functionality, including authentication, authorization, data processing, analytics, explainability, assistant behavior, reporting, and tenant-isolation protections.

Automated tests do not replace manual verification of external services or live background processing.

### 10. Run Frontend Quality Checks

From the `frontend` directory:

```powershell
npm run lint
npm run build
```

Use the repository's existing scripts for linting and production-build verification.

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

### Last Reported Automated Verification

The local verification report dated October 19, 2026, recorded:

| Check | Reported result |
|---|---|
| Backend automated test suite | 116 passed, 0 failed |
| Frontend ESLint | 0 errors, 0 warnings |
| TypeScript check | 0 errors during production build |
| Frontend production build | Successful |
| Static route generation | 21 routes generated |
| Celery task registration | Analysis and report tasks registered |
| Backend health endpoint | HTTP 200 |
| Database health endpoint | HTTP 200 |

These are the results recorded by the local verification report; they are not a guarantee that every workflow has passed live runtime acceptance.

### Outstanding Runtime Acceptance

The following checks remain necessary:

- Reliable Redis connectivity from the Windows-hosted backend.
- Successful connection of the live Celery worker to Redis.
- Real asynchronous dataset analysis reaching `COMPLETED`.
- Verification that the completed results persist and appear correctly in the dashboard.
- Successful background PDF generation and authorized report download.
- Confirmation that the full application workflow works without relying on mock AI results.

**Current status:** Core application implementation and reported automated checks are in place. Final end-to-end runtime acceptance is still in progress. Production readiness has not yet been established.

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
