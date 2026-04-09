# FarmIQ - AI-Powered Agricultural Intelligence Platform

> **Status**: ✅ Core backend production-ready (v4.0) | 🚧 Frontend Hedera Integration (in development) | **Phase 2 In Progress**

**FarmIQ** is a comprehensive **production-grade agricultural intelligence platform** combining **AI, blockchain, and real-time data** to transform farming economics for Kenyan smallholder farmers. It delivers three integrated AI systems for agricultural intelligence:

| System | Purpose | Technology | Status |
|--------|---------|-----------|--------|
| **FarmGrow** | RAG-powered agricultural Q&A chatbot | Ollama + Embeddings + BM25 | ✅ Live |
| **FarmScore** | AI credit scoring for farmer loan eligibility | Ensemble ML + SHAP | ✅ Live |
| **FarmSuite** | Predictive farm intelligence & optimization | Time-series + Prophet | ✅ Live |

### Key Capabilities
- ✅ Real-time agricultural Q&A with document retrieval (RAG pipeline)
- ✅ ML-based credit scoring (Gradient Boosting + Random Forest + Logistic Regression)
- ✅ Predictive analytics (yield, expenses, disease risk, market prices)
- ✅ M-Pesa payment integration (token purchases, escrow management)
- ✅ USSD/SMS multi-channel support (Africa's Talking)
- ✅ Token quota management (FIQ utility tokens with burning/minting)
- ✅ Blockchain integration (Hedera for immutable audit logging)
- ✅ PWA offline capability with real-time sync
- ✅ Role-based access control (8 user roles: farmer, worker, admin, lender, agent, vendor, cooperative, auditor)

## Technology Stack

### Frontend
- **Framework**: Angular 21.1.1 (standalone components, server-side rendering)
- **Language**: TypeScript 5.9.2 (strict mode enabled)
- **Package Manager**: npm 11+ | Node.js 18+
- **Mobile**: Ionic Angular for native apps
- **Build Tool**: Vite with Angular integration
- **Testing**: Vitest 4.0.8, Karma/Jasmine for unit tests
- **State Management**: Angular Signals (v21), RxJS 7.8
- **UI Components**: Custom components + Ionic
- **Styling**: SCSS with CSS custom properties, responsive design (mobile-first)
- **Maps**: MapLibre-GL for geo-spatial features
- **Blockchain**: Hedera SDK, Web3.js, Ethers.js for DeFi integration
- **Real-time**: Supabase realtime subscriptions
- **Messaging**: Africa's Talking SDK, Firebase Cloud Messaging
- **HTTP Client**: Angular HttpClient with interceptors
- **PWA**: Service Worker for offline support, web manifest

### Backend (FastAPI Python)
- **Framework**: FastAPI 0.109.0 (async-first, auto OpenAPI docs)
- **Language**: Python 3.10+ (type hints throughout)
- **ASGI Server**: Uvicorn 0.27.0 (production: Gunicorn + Uvicorn workers)
- **ORM**: SQLAlchemy 1.4.48 (async driver)
- **Database Driver**: Psycopg2 2.9.10 (PostgreSQL)
- **Database Migrations**: Alembic 1.12.1
- **Authentication**: PyJWT, python-jose, Passlib (bcrypt hashing)
- **Validation**: Pydantic 2.0+ (FastAPI integration)
- **AI/ML**: 
  - **LLM**: Ollama (local models: Mistral 7B, Llama 2/3.2)
  - **Embeddings**: Sentence Transformers (BAAI/bge-m3)
  - **ML Models**: scikit-learn, XGBoost, LightGBM
  - **Explainability**: SHAP (model interpretation)
  - **Feature Engineering**: pandas, numpy
  - **Time Series**: Prophet (forecasting)
- **RAG Pipeline**: Custom (BM25 retrieval, vector similarity, hybrid ranking)
- **Payment Integration**: M-Pesa Daraja API client
- **SMS/USSD**: Africa's Talking SDK
- **Blockchain**: Hedera Python SDK
- **Logging**: structlog, python-json-logger (structured JSON logs)
- **Monitoring**: Prometheus metrics, Grafana integration
- **Caching**: Local embedding cache (numpy files), Redis (optional)
- **API Documentation**: FastAPI auto-generated OpenAPI (Swagger UI, ReDoc)

### Database & Storage
- **Primary**: PostgreSQL 14+ (managed via Supabase)
- **Extensions**: pgvector (vector similarity search), PostGIS (geographic queries)
- **Connection Pooling**: Psycopg2 connection pool, async support
- **Embeddings Cache**: Local .npy files with metadata.json
- **Blockchain Ledger**: Hedera Hashgraph (immutable audit trail)
- **Metrics Storage**: Cortex time-series database
- **File Storage**: Supabase Storage (PDFs, images, documents)

### Deployment & Infrastructure
- **Hosting**: Azure VM (Ubuntu 22.04 LTS)
- **Web Server**: Apache reverse proxy (frontend) + FastAPI backend
- **Containerization**: Docker + Docker Compose (optional)
- **CI/CD**: GitHub Actions (planned)
- **Monitoring**: Grafana 9.0+, Prometheus metrics
- **Logging**: Structured JSON via Python JSON Logger
- **Type Safety**: Strict TypeScript (frontend), Python type hints (backend)

## Architecture Overview

### Layered Architecture (Domain-Driven Design v4.0)

FarmIQ Backend uses a **proven 4-layer DDD architecture** for maintainability, testability, and scalability:

```
┌──────────────────────────────────────────────────┐
│  API LAYER (Presentation)                        │
│  ├─ Routes & HTTP Handlers (/api/v1/...)        │
│  ├─ Request/Response Validation                 │
│  ├─ Exception → HTTP Status Mapping             │
│  └─ OpenAPI/Swagger Documentation              │
└──────────────────┬───────────────────────────────┘
                   ↓
┌──────────────────────────────────────────────────┐
│ APPLICATION LAYER (Orchestration)                │
│  ├─ Application Services (Business Logic)       │
│  ├─ Repositories (Data Access Abstraction)      │
│  ├─ DTOs / Pydantic Schemas (Validation)        │
│  ├─ Error Handling & Custom Exceptions          │
│  └─ Dependency Injection                        │
└──────────────────┬───────────────────────────────┘
                   ↓
┌──────────────────────────────────────────────────┐
│ DOMAIN LAYER (Pure Business Logic)               │
│  ├─ Domain Entities (Farmer, CreditScore)       │
│  ├─ Domain Services (no external deps)          │
│  ├─ Value Objects & Business Rules              │
│  └─ Domain Exceptions                           │
└──────────────────┬───────────────────────────────┘
                   ↓
┌──────────────────────────────────────────────────┐
│ INFRASTRUCTURE LAYER (Technical Implementation)  │
│  ├─ ML Models & Training Pipelines              │
│  ├─ LLM & Embeddings (Ollama)                   │
│  ├─ Database Clients (Supabase)                 │
│  ├─ External Service Integrations               │
│  ├─ Feature Engineering & Preprocessing         │
│  └─ Caching & Performance Optimization          │
└──────────────────────────────────────────────────┘
```

**Benefits of This Architecture**:
- ✅ **Testability**: Domain logic has zero dependencies
- ✅ **Maintainability**: Changes isolated to their layer
- ✅ **Scalability**: Easy to add features or split into microservices
- ✅ **Consistency**: Same pattern across all modules (FarmGrow, FarmScore, FarmSuite)

### Frontend Architecture (Angular 21)

```
┌─────────────────────────────────────────┐
│ Routes & Guards                         │
│ ├─ 8 Role-Based Lazy Modules           │
│ ├─ Auth Guards + FarmIQ ID Guard       │
│ └─ Protected Routes with RedirectTo    │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│ Services (Core & Feature)               │
│ ├─ Supabase Service (Auth + Signals)   │
│ ├─ FarmIQ ID Service                   │
│ ├─ RAG Chatbot Service                 │
│ ├─ Farm Suite Service                  │
│ └─ Payment & Integration Services      │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│ Components (Feature Modules)            │
│ ├─ Farmer Dashboard (10+ components)   │
│ ├─ Admin Console (12+ components)      │
│ ├─ Worker Interface (10+ components)   │
│ ├─ FarmGrow Chatbot Component          │
│ └─ Maps & Visualizations               │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│ HTTP Interceptors & Guards             │
│ ├─ API Interceptor (X-FarmIQ-ID header)│
│ ├─ Auth Guard (token validation)       │
│ ├─ Error Handling                      │
│ └─ Request/Response Transformation     │
└─────────────────────────────────────────┘
```

## Project Structure

```
farmintelligencequotient/
├── farmiq/                          # 🎨 Angular 21 Frontend (PWA + SSR)
│   ├── src/
│   │   ├── app/
│   │   │   ├── app.routes.ts        # Main routing (8 lazy modules)
│   │   │   ├── app.config.ts        # Build config
│   │   │   ├── app.config.server.ts # Server config
│   │   │   ├── app.html             # Root template
│   │   │   ├── app.ts               # Main component
│   │   │   │
│   │   │   ├── modules/             # 8 Feature modules
│   │   │   │   ├── farmer/          # Farmer dashboard
│   │   │   │   ├── admin/           # Admin console
│   │   │   │   ├── worker/          # Worker interface
│   │   │   │   ├── lender/          # Lender portal
│   │   │   │   ├── agent/           # Field agent tools
│   │   │   │   ├── vendor/          # Vendor management
│   │   │   │   ├── cooperative/     # Coop operations
│   │   │   │   └── auditor/         # Audit trails
│   │   │   │
│   │   │   ├── components/          # Shared components
│   │   │   │   ├── farmgrow-chatbot/ # RAG chatbot UI
│   │   │   │   ├── header/
│   │   │   │   ├── footer/
│   │   │   │   ├── sidebar/
│   │   │   │   └── common/
│   │   │   │
│   │   │   ├── services/
│   │   │   │   ├── core/
│   │   │   │   │   ├── supabase.service.ts       # Auth + Signals
│   │   │   │   │   ├── farmiq-id.service.ts     # FarmIQ ID generation
│   │   │   │   │   ├── error-handler.service.ts
│   │   │   │   │   └── hedera.service.ts
│   │   │   │   ├── rag/
│   │   │   │   │   └── farmgrow-chatbot.service.ts # RAG integration
│   │   │   │   ├── payment/        # M-Pesa + tokens
│   │   │   │   └── analytics/      # Metrics
│   │   │   │
│   │   │   ├── guards/
│   │   │   │   ├── auth.guard.ts    # Route protection
│   │   │   │   ├── farmiq-id.guard.ts
│   │   │   │   └── role/*.guard.ts  # Role-based guards
│   │   │   │
│   │   │   ├── interceptors/
│   │   │   │   └── core/
│   │   │   │       ├── api-interceptor.ts # X-FarmIQ-ID injection
│   │   │   │       ├── auth-interceptor.ts
│   │   │   │       └── error-interceptor.ts
│   │   │   │
│   │   │   ├── models/              # TypeScript interfaces
│   │   │   ├── pipes/               # Custom pipes
│   │   │   └── directives/          # Custom directives
│   │   │
│   │   ├── environments/            # Multi-environment config
│   │   │   ├── environment.ts       # Production
│   │   │   └── environment.development.ts
│   │   │
│   │   ├── assets/                  # Static assets
│   │   │   └── images/
│   │   │
│   │   ├── public/                  # PWA assets
│   │   │   ├── manifest.webmanifest
│   │   │   ├── browserconfig.xml
│   │   │   └── icons/
│   │   │
│   │   ├── styles.scss              # Global styles (CSS variables)
│   │   ├── main.ts                  # Bootstrap (SSR)
│   │   ├── main.server.ts           # Server entrypoint
│   │   ├── server.ts                # Express server
│   │   └── index.html               # Root HTML
│   │
│   ├── package.json                 # npm dependencies
│   ├── angular.json                 # Angular CLI config
│   ├── tsconfig.json                # TypeScript config
│   ├── tsconfig.app.json            # App-specific TS config
│   ├── tsconfig.spec.json           # Test TS config
│   ├── ngsw-config.json             # PWA config
│   └── README.md                    # Frontend docs
│
├── farmiq-backend/                  # 🚀 FastAPI Backend (Python)
│   ├── main.py                      # 🚀 Entry point - start here
│   ├── requirements.txt             # Python dependencies
│   ├── README.md                    # Backend docs
│   │
│   ├── auth/
│   │   ├── farmiq_id.py             # FarmIQ ID (FQ + 4 chars) generation
│   │   ├── dependencies.py          # FastAPI auth dependencies
│   │   └── __init__.py
│   │
│   ├── config/
│   │   ├── settings.py              # Environment-based config (50+ settings)
│   │   ├── models.py                # LLM model configurations
│   │   └── __init__.py
│   │
│   ├── core/                        # Infrastructure & Shared Services
│   │   ├── database.py              # Supabase client + connection pooling
│   │   ├── db_pool.py               # Async connection pool
│   │   ├── ollama_service.py        # Ollama LLM interface
│   │   ├── schemas.py               # Shared Pydantic models
│   │   ├── security.py              # Input validation + XSS/SQL injection protection
│   │   ├── middleware.py            # RequestID, security headers, audit logging
│   │   ├── logging_config.py        # Structured JSON logging
│   │   ├── metrics.py               # Performance monitoring
│   │   ├── embedding_cache.py       # Local embedding storage
│   │   ├── hedera_service.py        # Blockchain integration
│   │   ├── cortex.py                # Model orchestration
│   │   ├── app_config.py
│   │   ├── cache.py
│   │   ├── caching.py
│   │   ├── cortex_helpers.py
│   │   ├── grafana_payment_dashboard.py
│   │   ├── load_testing.py
│   │   ├── ml_theory.py
│   │   ├── performance.py
│   │   ├── structured_logging.py
│   │   ├── supabase_client.py
│   │   ├── validation.py
│   │   └── __init__.py
│   │
│   ├── app/                         # Application Modules (Business Logic)
│   │
│   │   ├── farmgrow/                # 💬 RAG Chatbot System
│   │   │   ├── routes.py            # POST /farmgrow/query, POST /farmgrow/documents
│   │   │   ├── services/
│   │   │   │   ├── orchestrator.py          # RAG pipeline coordinator
│   │   │   │   ├── embeddings.py           # Text-to-vector (Sentence Transformers)
│   │   │   │   ├── embedding_store.py      # Local vector storage
│   │   │   │   ├── retrieval.py            # Hybrid (BM25 + vector) retrieval
│   │   │   │   ├── ranking.py              # Multi-signal document ranking
│   │   │   │   ├── llm.py                  # Ollama answer generation
│   │   │   │   ├── document_processor.py   # PDF/image processing
│   │   │   │   ├── ocr.py                  # OCR for scanned docs
│   │   │   │   ├── ingestion.py            # Doc ingestion pipeline
│   │   │   │   ├── conversations.py        # Chat history
│   │   │   │   └── __init__.py
│   │   │   ├── exceptions.py
│   │   │   ├── validation.py
│   │   │   ├── resilience.py        # Retry logic, circuit breaker
│   │   │   └── __init__.py
│   │   │
│   │   ├── farmscore/               # 💳 Credit Scoring System
│   │   │   ├── routes.py            # Credit scoring endpoints
│   │   │   ├── api/
│   │   │   │   └── routes/
│   │   │   │       └── credit_scoring.py
│   │   │   ├── application/
│   │   │   │   ├── services/
│   │   │   │   │   └── credit_scoring_service.py  # Orchestration
│   │   │   │   ├── repositories/
│   │   │   │   │   ├── farmer_repository.py
│   │   │   │   │   └── credit_score_repository.py
│   │   │   │   └── schemas/
│   │   │   ├── domain/
│   │   │   │   ├── entities/
│   │   │   │   │   ├── farmer.py
│   │   │   │   │   └── credit_score.py
│   │   │   │   └── services/
│   │   │   │       └── credit_calculation.py # Pure business logic
│   │   │   ├── ml/
│   │   │   │   ├── models/
│   │   │   │   │   └── ensemble.py          # 3-model ensemble
│   │   │   │   ├── predictors/
│   │   │   │   │   └── credit_model.py
│   │   │   │   └── training/
│   │   │   │       ├── credit_training_pipeline.py  # 7-stage training
│   │   │   │       └── training_utils.py
│   │   │   ├── synthetic/
│   │   │   │   └── farmer_credit_generator.py
│   │   │   ├── pipelines/
│   │   │   ├── models/
│   │   │   ├── exceptions.py
│   │   │   └── __init__.py
│   │   │
│   │   ├── farmsuite/               # 🌾 Farm Intelligence System
│   │   │   ├── routes.py
│   │   │   ├── api/ routes/
│   │   │   │   ├── farm_analysis.py
│   │   │   │   ├── predictions.py
│   │   │   │   ├── production.py
│   │   │   │   ├── risks.py
│   │   │   │   ├── markets.py
│   │   │   │   └── workers.py
│   │   │   ├── application/ (services, repositories)
│   │   │   ├── domain/ (entities, business logic)
│   │   │   ├── ml/ (models, training, predictors)
│   │   │   ├── pipelines/ (feature engineering)
│   │   │   ├── synthetic/ (test data generation)
│   │   │   └── __init__.py
│   │   │
│   │   ├── integrations/            # External Service Integration
│   │   │   ├── mpesa/               # M-Pesa Daraja API
│   │   │   │   ├── daraja_client.py
│   │   │   │   ├── mpesa_service.py
│   │   │   │   ├── routes.py
│   │   │   │   ├── schemas.py
│   │   │   │   └── __init__.py
│   │   │   └── ussd_sms/            # Africa's Talking
│   │   │       ├── africastalking_client.py
│   │   │       ├── sms_service.py
│   │   │       ├── ussd_service.py
│   │   │       ├── routes.py
│   │   │       ├── schemas.py
│   │   │       └── __init__.py
│   │   │
│   │   ├── payments/                # Payment Processing & Escrow
│   │   │   ├── routes.py
│   │   │   ├── services/
│   │   │   │   ├── mpesa_service.py
│   │   │   │   ├── ussd_service.py
│   │   │   │   ├── gateway.py
│   │   │   │   └── admin_service.py
│   │   │   ├── config.py
│   │   │   ├── validation.py
│   │   │   ├── exceptions.py
│   │   │   ├── caching.py
│   │   │   └── __init__.py
│   │   │
│   │   ├── ai_usage/                # AI Token Tracking & Quotas
│   │   │   ├── routes.py
│   │   │   └── services/
│   │   │       ├── usage_tracker.py
│   │   │       ├── quota_validator.py
│   │   │       └── __init__.py
│   │   │
│   │   ├── shared/                  # Reusable Code
│   │   │   ├── base/
│   │   │   │   ├── entity.py        # BaseEntity parent class
│   │   │   │   ├── repository.py     # CRUD repository pattern
│   │   │   │   ├── service.py        # Common service methods
│   │   │   │   └── __init__.py
│   │   │   ├── exceptions/
│   │   │   │   ├── domain_exceptions.py
│   │   │   │   ├── application_exceptions.py
│   │   │   │   └── __init__.py
│   │   │   ├── routes/
│   │   │   │   └── mpesa_routes.py
│   │   │   ├── services/
│   │   │   │   └── mpesa_service.py
│   │   │   └── __init__.py
│   │   │
│   │   └── __init__.py
│   │
│   ├── embeddings_cache/            # Pre-computed embeddings for RAG
│   │   ├── metadata.json            # Chunk metadata index
│   │   └── embeddings/              # *.npy vector files
│   │
│   ├── libraries/                   # Agricultural knowledge documents
│   │
│   ├── supabase/
│   │   └── migrations/
│   │       └── 20260321_farmiq_consolidated_complete.sql # Master schema
│   │
│   ├── .env                         # Environment variables (DO NOT COMMIT)
│   ├── .env.example                 # Template
│   ├── .env.development             # Dev defaults
│   ├── .env.production              # Prod defaults
│   ├── .gitignore
│   └── README.md                    # Backend documentation
│
├── supabase/                        # Database & Edge Functions
│   ├── functions/
│   │   ├── credit-score/            # FIQ calculation function
│   │   ├── ingest-documents/        # Document processing function
│   │   └── send-*-email/            # Email notification functions
│   │
│   └── migrations/
│       └── 20260321_farmiq_consolidated_complete.sql # Master schema (50+ tables)
│
├── README.md                        # Root documentation (you are here)
├── README_EXECUTIVE.md              # Executive overview
└── .gitignore

---

## 🚀 Quick Start

### Prerequisites

```bash
# Frontend requirements
Node.js 18+
npm or yarn

# Backend requirements
Python 3.10+
pip or conda

# Database
PostgreSQL 14+ (via Supabase)

# Optional but recommended
Ollama (local LLM serving) - for FarmGrow RAG
Docker & Docker Compose
```

### 1. Frontend Setup

```bash
cd farmiq
npm install
ng serve
# Navigate to http://localhost:4200
```

### 2. Backend Setup

```bash
cd farmiq-backend

# Create virtual environment
python -m venv .venv

# Activate
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Start backend
uvicorn main:app --reload --port 8000
# Backend runs at http://localhost:8000
```

### 3. Verify Setup

```bash
# Backend health check
curl http://localhost:8000/health | jq

# Expected output
{
  "status": "healthy",
  "components": {
    "ollama": "ready",
    "database": "ready",
    "embeddings": "ready"
  }
}
```

---

## 💬 FarmGrow - RAG Chatbot System

### Overview
Real-time agricultural Q&A using **Retrieval-Augmented Generation (RAG)** with local LLM inference. Provides answers based on document retrieval + semantic understanding.

### Technology Stack
- **Embeddings**: BAAI/bge-m3 (Sentence Transformers - 384-dim)
- **LLM**: Mistral 7B or Llama via Ollama
- **Retrieval**: Hybrid (BM25 keyword search + vector similarity)
- **Document Store**: Local embeddings cache (.npy) + PostgreSQL FTS
- **Answer Generation**: In-context learning with top-K documents

### RAG Pipeline Flow

```
User Query
   ↓
Generate Embedding (BAAI/bge-m3)
   ↓
Hybrid Retrieval:
  ├─ BM25 keyword search (Supabase Full-Text Search)
  └─ Vector similarity search (pgvector)
   ↓
Multi-Signal Ranking:
  ├─ Relevance score
  ├─ Document freshness
  └─ User context
   ↓
Top-K Documents Retrieved (default 5, max 10)
   ↓
Context Window Check (total tokens < limit)
   ↓
LLM Answer Generation (Ollama)
   ↓
Confidence Scoring & Citation
   ↓
Stream Response to User
```

### Key Endpoints

```bash
# Query the chatbot
POST /api/v1/farmgrow/query
{
  "query": "How do I treat maize blight?",
  "context": "optional farm context",
  "stream": false
}

# Upload agricultural documents
POST /api/v1/farmgrow/documents (multipart/form-data)
# Supports: PDF, images, text files
# Auto-chunks with overlap
# Generates embeddings

# Fetch conversation history
GET /api/v1/farmgrow/conversations/{user_id}
POST /api/v1/farmgrow/conversations
```

---

## 💳 FarmScore - Credit Scoring System

### Overview
AI-powered **credit scoring for farmer loan eligibility** using ensemble ML models with SHAP explainability. Provides transparent risk assessments.

### Credit Scoring Process

**7-Stage Pipeline**:
1. **Data Collection** - Farmer financial, operational, & behavioral data
2. **Feature Engineering** - 20+ engineered features (WOE binning, interactions)
3. **Model Training** - Ensemble of 3 ML models (see below)
4. **Probability Calibration** - Isotonic regression for reliable predictions
5. **Explainability** - SHAP values for feature contribution analysis
6. **Risk Assessment** - Risk level assignment (Low/Medium/High)
7. **Score Caching** - 90-day cache for performance optimization

### Ensemble Models

```
CreditScorer (Weighted Voting Ensemble):
├─ Gradient Boosting (40% weight)
│   ├─ XGBoost-based with early stopping
│   ├─ Handles non-linear relationships
│   ├─ Feature importance rankings
│   └─ Training accuracy: ~88%
├─ Random Forest (35% weight)
│   ├─ 500 trees, max_depth=15
│   ├─ Robust to outliers
│   ├─ Feature interaction detection
│   └─ Training accuracy: ~85%
└─ Logistic Regression (25% weight)
    ├─ Baseline interpretable model
    ├─ Business rule alignment
    └─ Training accuracy: ~82%

→ Final prediction: weighted average + calibration
→ Output: Score (0-100) + Risk Level + SHAP explanations
```

### Key Endpoints

```bash
# Calculate FarmScore for a farmer
POST /api/v1/farmscore/calculate
{
  "farmer_data": {...}
}
→ Returns: score, risk_level, shap_explanations

# Get score history
GET /api/v1/farmscore/history/{farmer_id}

# Get risk factors
GET /api/v1/farmscore/factors/{farmer_id}
```

---

## 🌾 FarmSuite - Farm Intelligence System

### Overview
**Comprehensive farm intelligence** providing predictive analytics, market insights, risk analysis, and worker optimization.

### Core Features

- **Yield Prediction**: Time-series forecasting (Prophet) for crop yields
- **Disease Risk**: Early warning system for crop diseases
- **Expense Prediction**: Optimal expenditure planning
- **Market Intelligence**: Real-time commodity price signals
- **Worker Optimization**: Attendance, payroll, task allocation
- **Geographic Analysis**: PostGIS-based location intelligence

### Key Endpoints

```bash
POST /api/v1/farmsuite/predict-yield
GET /api/v1/farmsuite/disease-risk/{crop}
GET /api/v1/farmsuite/market-prices/{commodity}
POST /api/v1/farmsuite/optimize-workers
GET /api/v1/farmsuite/farm-analysis/{farm_id}
```

---

## 📱 Frontend Features by Role

### 8 Role-Based Modules

| Role | Module | Key Features |
|------|--------|--------------|
| **Farmer** | `modules/farmer` | Dashboard, credit score, wallet, farm setup, chatbot |
| **Admin** | `modules/admin` | User management, payments, tokenomics, audits |
| **Worker** | `modules/worker` | Attendance, payroll, performance tracking |
| **Lender** | `modules/lender` | Loan portfolio, credit scores, disbursement |
| **Agent** | `modules/agent` | Field operations, data collection, mobile-first |
| **Vendor** | `modules/vendor` | Product listings, orders, analytics |
| **Cooperative** | `modules/cooperative` | Collective operations, aggregated analytics |
| **Auditor** | `modules/auditor` | Compliance, audit trails, blockchain verification |

### Frontend Services Architecture

```typescript
// Core Services (always available)
- Supabase (Auth + Real-time)
- FarmIQ ID (User identification)
- Error Handler
- Hedera (Blockchain)

// Feature Services
- FarmGrow Chatbot
- Farm Suite Analytics
- Payment Gateway
- Mapping & Geolocation
```

---

## ⚙️ Environment Configuration

### Backend Environment Variables

```bash
# Supabase (Database & Authentication)
SUPABASE_URL=https://your-instance.supabase.co
SUPABASE_KEY=eyJhbGc...
DATABASE_URL=postgresql://user:pass@db:5432/farmiq

# LLM & Embeddings
OLLAMA_HOST=http://localhost:11434
EMBEDDING_MODEL=BAAI/bge-m3
LLM_MODEL=mistral:latest

# M-Pesa Integration
MPESA_CONSUMER_KEY=your_key
MPESA_CONSUMER_SECRET=your_secret
MPESA_BUSINESS_SHORTCODE=174379
MPESA_ENVIRONMENT=sandbox

# Blockchain (Optional)
HEDERA_ACCOUNT_ID=0.0.xxxxx
HEDERA_PRIVATE_KEY=xxxxxx
HEDERA_NETWORK=testnet

# Server Configuration
ENVIRONMENT=development|staging|production
PORT=8000
LOG_LEVEL=INFO

# Monitoring
USE_GRAFANA=true
GRAFANA_URL=http://localhost:3000
```

### Frontend Environment Configuration

```typescript
// src/environments/environment.ts
export const environment = {
  production: false,
  supabase: {
    url: 'https://your-instance.supabase.co',
    key: 'eyJhbGc...'
  },
  api: {
    baseUrl: 'http://localhost:8000/api/v1'
  },
  hedera: {
    networkId: 'testnet',
    nodeAddress: '...'
  },
  tomtom: {
    apiKey: '...'
  },
  africastalking: {
    apiKey: '...'
  }
};
```

---

## 📦 API Endpoints Reference

### FarmGrow RAG Chatbot

```bash
POST /api/v1/farmgrow/query
GET /api/v1/farmgrow/conversations/{user_id}
POST /api/v1/farmgrow/documents
GET /api/v1/farmgrow/documents/{doc_id}
DELETE /api/v1/farmgrow/documents/{doc_id}
```

### FarmScore Credit Scoring

```bash
POST /api/v1/farmscore/calculate
GET /api/v1/farmscore/score/{farmer_id}
GET /api/v1/farmscore/history/{farmer_id}
GET /api/v1/farmscore/factors/{farmer_id}
```

### FarmSuite Intelligence

```bash
GET /api/v1/farmsuite/farm-analysis/{farm_id}
POST /api/v1/farmsuite/predict-yield
GET /api/v1/farmsuite/disease-risk/{crop}
GET /api/v1/farmsuite/market-prices/{commodity}
POST /api/v1/farmsuite/optimize-workers
```

### Payments & Tokens

```bash
POST /api/v1/payments/mpesa/initiate
POST /api/v1/payments/mpesa/callback
GET /api/v1/tokens/balance
POST /api/v1/tokens/purchase
GET /api/v1/tokens/usage
```

### Integrations

```bash
POST /api/v1/integrations/ussd/callback
POST /api/v1/integrations/sms/send
GET /api/v1/integrations/hedera/transactions
```

### Admin & Monitoring

```bash
GET /api/v1/admin/health
GET /api/v1/admin/dashboard
GET /api/v1/admin/transactions
GET /api/v1/admin/metrics/ai-usage
```

---

## 🔧 Development

## 🔧 Development

### Angular CLI Commands (Frontend)

```bash
# Generate Components
ng generate component components/component-name
ng g c components/my-component  # shorthand

# Generate Services
ng generate service services/service-name
ng g s services/my-service

# Generate Modules
ng generate module modules/module-name
ng g m modules/feature-module

# Generate Guards
ng generate guard guards/guard-name
ng g guard guards/auth.guard

# Generate Interceptors
ng generate interceptor interceptors/interceptor-name
ng g interceptor interceptors/api.interceptor

# Generate Pipes
ng generate pipe pipes/pipe-name
ng g p pipes/my.pipe

# Generate Interfaces
ng generate interface models/model-name
ng g i models/MyInterface

# Build for different environments
ng build --configuration development
ng build --configuration production
ng build --configuration production --service-worker  # PWA

# Development server with live reload
ng serve
ng serve --port 5000  # Custom port
ng serve --open  # Auto-open browser

# Run tests
ng test
ng test --code-coverage
ng test --watch=false

# Run e2e tests
ng e2e
```

### Backend Python Commands

```bash
# Format code (Black)
black .

# Lint code (Pylint/Flake8)
flake8 .
pylint app/

# Type checking (mypy)
mypy .

# Run tests
pytest
pytest --cov=app/  # With coverage
pytest -v  # Verbose

# Run database migrations
alembic upgrade head
alembic downgrade -1

# Start development server
python main.py

# Start with hot-reload
uvicorn main:app --reload

# Production server (Gunicorn)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker \
  --max-requests 1000 \
  --timeout 60 \
  main:app
```

---

## 🚀 Deployment

### Frontend Deployment

```bash
# Build optimized bundle
cd farmiq
npm install
ng build --configuration production

# With PWA support
ng build --configuration production --service-worker

# Output directory: dist/farmiq/
```

**Deployment Targets**:

**Azure Static Web Apps**:
```bash
az staticwebapp up --name farmiq --branch main
```

**Vercel**:
```bash
npm i -g vercel
vercel
```

**Firebase Hosting**:
```bash
npm i -g firebase-tools
firebase login
firebase deploy
```

**Traditional Hosting**:
```bash
# Copy dist/farmiq/ contents to web root
scp -r dist/farmiq/* user@server:/var/www/html/
```

### Backend Deployment

**Docker** (Recommended):
```bash
# Build image
docker build -f farmiq-backend/Dockerfile -t farmiq-backend:latest .

# Run container
docker run -p 8000:8000 \
  --env-file farmiq-backend/.env \
  farmiq-backend:latest
```

**Azure VM (Apache + Gunicorn)**:
```bash
# Install dependencies
sudo apt-get update
sudo apt-get install python3.10 python3-pip python3.10-venv

# Setup app
cd /opt/farmiq-backend
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure systemd service
sudo nano /etc/systemd/system/farmiq-backend.service
sudo systemctl daemon-reload
sudo systemctl start farmiq-backend
sudo systemctl enable farmiq-backend

# Configure Apache reverse proxy
sudo a2enmod proxy proxy_http
# Add to /etc/apache2/sites-available/farmiq.conf:
# ProxyPass /api/ http://localhost:8000/
# ProxyPassReverse /api/ http://localhost:8000/

sudo systemctl restart apache2
```

**Environment Variables (Production)**:
```bash
ENVIRONMENT=production
LOG_LEVEL=WARNING
DATABASE_URL=postgresql://prod_user:prod_pass@db.azure.com:5432/farmiq_prod
SUPABASE_URL=https://prod-instance.supabase.co
SUPABASE_KEY=prod_key_xxx
OLLAMA_HOST=http://ollama-service:11434
```

---

## 🔌 Integration Details

### Supabase (Database & Authentication)
- PostgreSQL database with pgvector for embeddings
- PostGIS for geographic queries
- Row-level security (RLS) for multi-tenant data isolation
- Real-time subscriptions via WebSocket
- File storage for farm images and documents
- **Setup**: `SUPABASE_URL`, `SUPABASE_KEY` in `.env`

### Ollama (Local AI Models)
- Privacy-first LLM on-premise execution
- Default models: Llama 2/3.2, Mistral, Neural Chat
- FastAPI integration for FarmGrow RAG
- Embedding models: BAAI/bge-m3 for semantic search
- **Setup**: `OLLAMA_HOST=http://localhost:11434`

### M-Pesa Daraja API (Mobile Money)
- STK Push for payment initiation
- C2B for receiving payments from farmers
- B2C for payouts (subsidies, bonuses)
- Tax remittance to KRA
- **Setup**: `MPESA_CONSUMER_KEY`, `MPESA_CONSUMER_SECRET`, `MPESA_SHORTCODE`

### Africa's Talking (USSD/SMS)
- USSD gateway for feature phone users
- SMS notifications and confirmations
- Two-way communication
- **Setup**: `AFRICASTALKING_API_KEY`, `AFRICASTALKING_USERNAME`

### Hedera Hashgraph (Blockchain)
- Hedera Consensus Service (HCS) for immutable audit logs
- Hedera Token Service (HTS) for FIQ token registry
- Smart contracts for loan agreements
- Decentralized credit scoring verification
- **Setup**: `HEDERA_ACCOUNT_ID`, `HEDERA_PRIVATE_KEY`

### Grafana (Monitoring & Dashboards)
- Real-time metrics visualization
- Payment dashboard for transactions
- AI usage analytics and quotas
- System health monitoring
- **Setup**: `GRAFANA_URL`, `GRAFANA_TOKEN`

---

## 🗄️ Database Schema

### Supabase Migrations

```bash
cd supabase
supabase login
supabase link --project-ref YOUR_PROJECT_ID
supabase db push  # Applies 20260321_farmiq_consolidated_complete.sql

# View migrations
supabase migration list
```

### Schema Overview (50+ Tables in 11 Sections)

1. **Reference Data**: Locations, measurement units, expense categories, status enums
2. **User Management**: Users, user profiles, roles, permissions
3. **Farm Management**: Farms, crops, land parcels, farm equipment
4. **Payment System**: M-Pesa transactions, callbacks, reversals, tax remittances
5. **Token System**: User token balances, usage logs, audit trails
6. **USSD/SMS**: Sessions, delivery tracking, opt-outs
7. **AI Tracking**: Usage logs for billing and analytics
8. **Credit Scoring**: FIQ scores, calibration data, calculation logs
9. **Worker Management**: Attendance, payroll, performance
10. **Market Data**: Commodity prices, market signals
11. **Blockchain**: Hedera transaction hashes, verification records

### Key Indexes
- **Primary queries**: Indexed on `user_id`, `status`, `created_at`, `phone_number`
- **Foreign keys**: All relationships have indexes for referential integrity
- **Composite indexes**: Multi-column indexes for common filter combinations
- **FTS indexes**: Full-text search indexes for document retrieval

---

## 🧪 Testing

### Frontend Testing

```bash
# Run unit tests
ng test

# With coverage report
ng test --code-coverage

# Watch mode (automatic re-run on changes)
ng test --watch

# Run specific test file
ng test --include='**/my.component.spec.ts'
```

### Backend Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app

# Verbose output
pytest -v

# Run specific test
pytest tests/test_farmgrow_rag.py::test_query

# With markers
pytest -m integration  # Integration tests only
pytest -m unit        # Unit tests only
```

---

## 🔐 Security

### Frontend Security
- **XSS Protection**: Angular sanitizes dynamic content
- **CSRF Protection**: CSRF tokens in sensitive endpoints
- **Auth Guards**: Protects routes from unauthorized access
- **FarmIQ ID Guard**: Validates user identity headers
- **Interceptors**: Add security headers, handle auth errors

### Backend Security
- **Input Validation**: Pydantic schemas validate all inputs
- **SQL Injection Protection**: Parameterized queries via SQLAlchemy
- **XSS Protection**: HTML escaping in security module
- **Rate Limiting**: Global middleware rate limiting
- **Auth Middleware**: Validates X-FarmIQ-ID header
- **HTTPS**: Enforce SSL/TLS in production
- **Secrets Management**: Use environment variables, never commit `.env`

---

## 🐛 Troubleshooting

### Frontend Issues

**"ng serve" fails**:
```bash
# Clear cache
rm -rf dist/
rm -rf node_modules/
npm install
ng serve
```

**PWA not working**:
```bash
# Rebuild with service worker
ng build --configuration production --service-worker
# Clear browser cache (DevTools → Storage → Clear all)
```

**CORS errors**:
- Check backend CORS configuration
- Verify API URL in `environment.ts`

### Backend Issues

**"Module not found" error**:
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Verify Python version
python --version  # Should be 3.10+
```

**Database connection fails**:
```bash
# Test connection
python -c "from core.database import get_db_client; print('OK')"

# Check DATABASE_URL format
echo $DATABASE_URL
```

**Ollama not running**:
```bash
# Start Ollama
ollama serve

# In separate terminal, pull model
ollama pull mistral
```

### Deployment Issues

**Port already in use**:
```bash
# Find process
lsof -i :8000

# Kill process
kill -9 PID
```

**Permission denied**:
```bash
chmod +x main.py
sudo chown -R app:app /opt/farmiq-backend
```

---

## 📚 Additional Resources

- **Backend README**: [farmiq-backend/README.md](farmiq-backend/README.md)
- **Frontend README**: [farmiq/README.md](farmiq/README.md)
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **SQL Schema**: [supabase/migrations/20260321_farmiq_consolidated_complete.sql](supabase/migrations/20260321_farmiq_consolidated_complete.sql)

---

## 📈 Next Steps & Roadmap

### Phase 2 (Current)
- ✅ Frontend 8-role module system
- ✅ Hedera blockchain integration
- ✅ Smart contracts for loan agreements
- ⏳ P2P lending through decentralized contracts
- ⏳ On-chain farmer reputation scores

### Phase 3 (Planned)
- Multilingual support (Swahili, Arabic, others)
- Cross-chain bridges (Ethereum, Polygon)
- Advanced farmer analytics dashboard
- Batch processing for farmer cooperatives
- IoT sensor integration (soil moisture, temperature)
- Satellite imagery for crop monitoring
- Mobile app (React Native/Flutter)

### Phase 4 (Vision)
- AI-powered crop recommendation engine
- Weather-based insurance products
- Supply chain traceability
- Carbon credit tracking
- Voice-based interfaces (ASR/TTS)

---

## 👥 Contributing

### Code Style

**Frontend (Angular/TypeScript)**:
```typescript
// Use Angular style guide
// https://angular.dev/style-guide

// Example: Component
@Component({
  selector: 'app-my-component',
  standalone: true,
  template: `<div>{{ data }}</div>`,
  styles: [`
    :host { display: block; }
  `]
})
export class MyComponent {
  data = signal('initial');
}
```

**Backend (FastAPI/Python)**:
```python
# Follow PEP 8 with Black formatter
# Use type hints throughout

from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/example")

class ExampleSchema(BaseModel):
    name: str
    value: int

@router.post("/")
async def create_example(schema: ExampleSchema) -> dict:
    """Create a new example."""
    return {"status": "created"}
```

### Pull Request Process

1. **Fork** the repository
2. **Create feature branch**: `git checkout -b feature/your-feature`
3. **Commit changes**: `git commit -m "feat: add your feature"`
4. **Push**: `git push origin feature/your-feature`
5. **Create Pull Request** with description
6. **Wait for review** and CI checks
7. **Merge** after approval

### Commit Message Convention

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Example:
```
feat(farmgrow): add streaming response support

Implements streaming RAG responses for real-time chatbot feedback.
Reduces time-to-first-token from 2s to 200ms.

Fixes #123
```

---

## 📄 License

This project is proprietary. All rights reserved.

---

## 📞 Support

### Getting Help

- **Documentation**: See README files in each directory
- **API Docs**: http://localhost:8000/docs (Swagger)
- **Issues**: Post in project management system
- **Slack**: #farmiq-dev channel

### Contact

- **Backend Team**: backend@farmiq.local
- **Frontend Team**: frontend@farmiq.local
- **DevOps**: devops@farmiq.local

---

## 🎯 Key Performance Indicators (KPIs)

### Backend Performance Targets
- RAG Query Response Time: < 2 seconds
- Credit Score Calculation: < 500ms
- API Availability: > 99.9%
- Database Query Performance: < 100ms (p95)

### Frontend Performance Targets
- Initial Load Time: < 3 seconds (4G)
- Core Web Vitals:
  - LCP (Largest Contentful Paint): < 2.5s
  - FID (First Input Delay): < 100ms
  - CLS (Cumulative Layout Shift): < 0.1

### ML Model Performance
- Credit Scoring Accuracy: > 85%
- Disease Detection Precision: > 90%
- Yield Prediction R²: > 0.75

---

## 🙏 Acknowledgments

- **Supabase**: Database and authentication infrastructure
- **Ollama**: Local AI model serving
- **Hedera**: Blockchain infrastructure
- **Angular Team**: Web framework
- **FastAPI Team**: Python web framework

---

**Last Updated**: April 2, 2026  
**Version**: 4.0 (Production Ready)
8. **Credit Scoring**: FIQ scores, calibration data, calculation logs
9. **Worker Management**: Attendance, payroll, performance
10. **Market Data**: Commodity prices, market signals
11. **Blockchain**: Hedera transaction hashes, verification records

### Key Indexes
- **Primary queries**: Indexed on `user_id`, `status`, `created_at`, `phone_number`
- **Foreign keys**: All relationships have indexes for referential integrity
- **Composite indexes**: Multi-column indexes for common filter combinations
- **FTS indexes**: Full-text search indexes for document retrieval

---

## 🧪 Testing

### Frontend Testing

```bash
# Run unit tests
ng test

# With coverage report
ng test --code-coverage

# Watch mode (automatic re-run on changes)
ng test --watch

# Run specific test file
ng test --include='**/my.component.spec.ts'
```

### Backend Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app

# Verbose output
pytest -v

# Run specific test
pytest tests/test_farmgrow_rag.py::test_query

# With markers
pytest -m integration  # Integration tests only
pytest -m unit        # Unit tests only
```

---

## 🔐 Security

### Frontend Security
- **XSS Protection**: Angular sanitizes dynamic content
- **CSRF Protection**: CSRF tokens in sensitive endpoints
- **Auth Guards**: Protects routes from unauthorized access
- **FarmIQ ID Guard**: Validates user identity headers
- **Interceptors**: Add security headers, handle auth errors

### Backend Security
- **Input Validation**: Pydantic schemas validate all inputs
- **SQL Injection Protection**: Parameterized queries via SQLAlchemy
- **XSS Protection**: HTML escaping in security module
- **Rate Limiting**: Global middleware rate limiting
- **Auth Middleware**: Validates X-FarmIQ-ID header
- **HTTPS**: Enforce SSL/TLS in production
- **Secrets Management**: Use environment variables, never commit `.env`

---

## 🐛 Troubleshooting

### Frontend Issues

**"ng serve" fails**:
```bash
# Clear cache
rm -rf dist/
rm -rf node_modules/
npm install
ng serve
```

**PWA not working**:
```bash
# Rebuild with service worker
ng build --configuration production --service-worker
# Clear browser cache (DevTools → Storage → Clear all)
```

**CORS errors**:
- Check backend CORS configuration
- Verify API URL in `environment.ts`

### Backend Issues

**"Module not found" error**:
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Verify Python version
python --version  # Should be 3.10+
```

**Database connection fails**:
```bash
# Test connection
python -c "from core.database import get_db_client; print('OK')"

# Check DATABASE_URL format
echo $DATABASE_URL
```

**Ollama not running**:
```bash
# Start Ollama
ollama serve

# In separate terminal, pull model
ollama pull mistral
```

### Deployment Issues

**Port already in use**:
```bash
# Find process
lsof -i :8000

# Kill process
kill -9 PID
```

**Permission denied**:
```bash
chmod +x main.py
sudo chown -R app:app /opt/farmiq-backend
```

---

## 📚 Additional Resources

- **Backend README**: [farmiq-backend/README.md](farmiq-backend/README.md)
- **Frontend README**: [farmiq/README.md](farmiq/README.md)
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **SQL Schema**: [supabase/migrations/20260321_farmiq_consolidated_complete.sql](supabase/migrations/20260321_farmiq_consolidated_complete.sql)
- Clear Angular cache: `ng cache clean`
- Delete node_modules: `rm -rf node_modules`
- Reinstall: `npm install`

**Database connection failed:**
- Check Supabase credentials in `.env`
- Verify internet connectivity to Supabase
- Check firewall rules on Azure VM

**Ollama not responding:**
- Ensure Ollama service is running: `ollama serve`
- Check port 11434 is accessible
- Pull model: `ollama pull llama2`

**M-Pesa callback not working:**
- Verify webhook URL is publicly accessible
- Check M-Pesa credentials in `.env`
- Review callback logs: `GET /api/v1/admin/callbacks`

## Support & Documentation

- **Executive Overview**: [README_EXECUTIVE.md](README_EXECUTIVE.md)
- **API Documentation**: http://localhost:8000/docs
- **Supabase Docs**: https://supabase.io/docs
- **Ollama Docs**: https://github.com/ollama/ollama
- **Hedera Docs**: https://docs.hedera.com/hedera

## Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit with clear messages: `git commit -m 'feat: add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Code Standards
- **Frontend**: Angular style guide, Strict TypeScript, unit tests
- **Backend**: PEP 8, Type hints, Docstrings for all functions
- **Database**: Migrations indexed, no breaking changes
- **Commits**: Conventional Commits (feat:, fix:, docs:, chore:)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🌾 Vision

> **Empowering African smallholder farmers with AI-driven intelligence, fair credit access, and market opportunity.**

By combining machine learning, blockchain, and mobile-first design, FarmIQ transforms how farmers access credit, understand markets, and adopt best practices—unlocking economic opportunity across the continent.

**Built with ❤️ for African Agriculture** 🌾🤖

---

**Frontend Tech**: Angular 21 | **Backend**: FastAPI | **AI**: Ollama + Cortex | **Blockchain**: Hedera | **Database**: Supabase | **Monitoring**: Grafana

*Last Updated: April 2, 2026*  
*FarmIQ Development Team*
