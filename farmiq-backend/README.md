# FarmIQ Backend - Production-Grade FastAPI Application

> **AI-Powered Agricultural Intelligence Platform** for Kenyan smallholder farmers  
> **Status**: Production-ready (v4.0) | **Last Updated**: 2026-04-02  
> **Framework**: FastAPI 0.109 | **Language**: Python 3.10+ | **Architecture**: Layered DDD

---

## 📋 Executive Summary

**FarmIQ Backend** is a sophisticated **FastAPI application** delivering three integrated AI systems for agricultural intelligence in Kenya:

| System | Purpose | Technology | Status |
|--------|---------|-----------|--------|
| **FarmGrow** | RAG-powered agricultural Q&A chatbot | Ollama + Embeddings + BM25 | ✅ Live |
| **FarmScore** | AI credit scoring for farmer loan eligibility | Ensemble ML + SHAP | ✅ Live |
| **FarmSuite** | Predictive farm intelligence & optimization | Time-series + Prophet | ✅ Live |

**Key Capabilities**:
- ✅ Real-time agricultural Q&A with document retrieval
- ✅ ML-based credit scoring (Gradient Boosting + Random Forest + Logistic Regression)
- ✅ Predictive analytics (yield, expenses, disease risk, market prices)
- ✅ M-Pesa payment integration (token purchases)
- ✅ USSD/SMS multi-channel support (Africa's Talking)
- ✅ Token quota management (FIQ utility tokens)
- ✅ Blockchain integration (Hedera for audit logging)

---

## 🚀 Quick Start

### Prerequisites

```bash
# Required versions
Python 3.10+
Node.js 18+ (for frontend integration)
PostgreSQL 14+ (via Supabase)
```

### 1. Clone & Setup Environment

```bash
# Clone repository
git clone https://github.com/your-org/farmiq.git
cd farmiq-backend

# Create Python virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy template
cp .env.example .env.development.local

# Edit with your credentials
nano .env.development.local
```

**Required Environment Variables**:
```bash
# Supabase (Database & Authentication)
SUPABASE_URL=https://your-instance.supabase.co
SUPABASE_KEY=eyJhbGc...
DATABASE_URL=postgresql://user:pass@localhost/farmiq

# LLM & Embeddings
OLLAMA_HOST=http://localhost:11434
EMBEDDING_MODEL=BAAI/bge-m3
LLM_MODEL=mistral:latest

# M-Pesa Integration
MPESA_CONSUMER_KEY=your_key
MPESA_BUSINESS_SHORTCODE=174379
MPESA_ENVIRONMENT=sandbox

# Blockchain (Optional)
HEDERA_ACCOUNT_ID=0.0.xxxxx
HEDERA_NETWORK=testnet

# Server Config
ENVIRONMENT=development
PORT=8000
LOG_LEVEL=INFO
```

### 3. Start Services (Terminal 1: Ollama)

```bash
# Start Ollama LLM server
ollama serve

# Ollama runs on http://localhost:11434
```

### 4. Start Backend (Terminal 2)

```bash
# Activate venv first
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Start FastAPI development server
python main.py

# Or with hot-reload (development)
uvicorn main:app --reload --port 8000

# Backend runs on http://localhost:8000
```

### 5. Verify Health

```bash
# In Terminal 3
curl http://localhost:8000/health | jq

# Expected output:
# {
#   "status": "healthy",
#   "components": {
#     "ollama": "ready",
#     "database": "ready",
#     "embeddings": "ready",
#     "llm": "ready"
#   }
# }
```

---

## 🏗️ Architecture Overview

### Layered Architecture (Domain-Driven Design)

---

## 📋 Executive Summary

### What is FarmIQ Backend?

FarmIQ Backend is a **production-grade FastAPI application** powering an agricultural intelligence platform for Kenyan smallholder farmers. It provides three interconnected AI systems built with **layered architecture**, **domain-driven design**, and **comprehensive ML/AI capabilities**.

### Core Systems

| System | Purpose | Tech Stack | Status |
|--------|---------|-----------|--------|
| **FarmGrow** | Agricultural knowledge RAG chatbot | Ollama + Embeddings | ✅ Complete |
| **FarmScore** | Farmer credit scoring & loan recommendations | Ensemble ML + SHAP | ✅ Complete |
| **FarmSuite** | Predictive farm intelligence & optimization | TimeSeries + Prophet | ✅ Complete |

### Key Features

- **Modular Architecture**: Clean separation (Domain → Application → API)
- **Scalable Design**: Reusable base classes, DRY principle, consistent patterns
- **ML-Ready**: Feature engineering, ensemble models, SHAP explainability
- **Production-Safe**: Comprehensive error handling, logging, validation
- **Testable Code**: Unit + integration tests with fixtures, 70%+ test coverage target
- **Cloud-Native**: FastAPI + Supabase + Ollama, containerization-ready

### Tech Stack Overview

```
Frontend:          Angular 21 PWA (farmiq/)
Backend:          FastAPI 0.104+ (Python 3.10+)
Database:         Supabase PostgreSQL (vector + postgis extensions)
ML/LLM:           Ollama (local), Sentence Transformers, scikit-learn, XGBoost
Inference:        SHAP for explainability
Infrastructure:   Azure VM, Docker, GitHub
```

---

## 🏗️ Architecture Overview

### Layered Architecture (v4.0 - NEW)

```
┌─────────────────────────────────────────┐
│  API Layer (Presentation)               │
│  ├─ Routes & HTTP Handlers             │
│  ├─ Request/Response Mapping           │
│  └─ Exception → HTTP Status Conversion │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ Application Layer (Orchestration)       │
│  ├─ Application Services               │
│  ├─ Repositories (Data Access)         │
│  ├─ DTOs / Schemas (Input/Output)      │
│  └─ Error Mapping                      │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ Domain Layer (Pure Business Logic)      │
│  ├─ Domain Entities                    │
│  ├─ Domain Services                    │
│  ├─ Value Objects                      │
│  └─ Business Rules (no dependencies)   │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ Infrastructure Layer (Technical Details)│
│  ├─ ML Models (ensemble, training)     │
│  ├─ External Services (Ollama, etc)    │
│  ├─ Database Clients                   │
│  └─ Feature Engineering                │
└─────────────────────────────────────────┘
```

**Benefits:**
- ✅ **Testability**: Domain logic has no dependencies (pure Python functions)
- ✅ **Maintainability**: Changes isolated to their layer
- ✅ **Scalability**: Easy to add new features or split services
- ✅ **Consistency**: Same pattern across farmscore & farmsuite

---

## 📁 New Project Structure (v4.0)

```
farmiq-backend/
├── app/
│   ├── shared/                          ⭐ Shared Commons (NEW)
│   │   ├── base/
│   │   │   ├── service.py               # BaseService (common methods)
│   │   │   ├── repository.py            # BaseRepository (CRUD patterns)
│   │   │   ├── entity.py                # BaseEntity (domain model)
│   │   │   └── __init__.py
│   │   ├── exceptions/
│   │   │   ├── domain_exceptions.py     # DomainException, ValidationError, etc
│   │   │   ├── application_exceptions.py # HTTPException mappings
│   │   │   └── __init__.py
│   │   └── utils/
│   │       ├── validation.py            # Common validators (non_empty, range, etc)
│   │       └── __init__.py
│   │
│   ├── farmscore/                       💳 Credit Scoring Module
│   │   ├── domain/                      # Pure business logic
│   │   │   ├── entities/
│   │   │   │   ├── farmer.py            # Farmer entity
│   │   │   │   ├── credit_score.py      # CreditScore entity
│   │   │   │   └── __init__.py
│   │   │   └── services/
│   │   │       ├── credit_calculation.py# Domain logic (no DB calls)
│   │   │       └── __init__.py
│   │   ├── application/                 # Orchestration layer
│   │   │   ├── repositories/            # Data access (implements BaseRepository)
│   │   │   │   ├── farmer_repository.py
│   │   │   │   ├── credit_score_repository.py
│   │   │   │   └── __init__.py
│   │   │   ├── services/                # App services (coordinates domain + repos)
│   │   │   │   ├── credit_scoring_service.py
│   │   │   │   └── __init__.py
│   │   │   ├── schemas/                 # DTOs (request/response)
│   │   │   │   └── __init__.py
│   │   │   └── __init__.py
│   │   ├── infrastructure/              # ML models & technical concerns
│   │   │   ├── models/                  # Existing ML code (ensemble.py, etc)
│   │   │   └── feature_engineering/     # Existing feature code
│   │   ├── api/                         # HTTP Layer
│   │   │   ├── routes/                  # FastAPI endpoints
│   │   │   ├── dependencies.py          # FastAPI dependency injection
│   │   │   ├── exceptions.py            # HTTP exception handlers
│   │   │   └── __init__.py
│   │   ├── tests/                       # Testing ⭐ NEW
│   │   │   ├── unit/                    # No I/O, pure logic testing
│   │   │   │   ├── domain/
│   │   │   │   ├── application/
│   │   │   │   └── infrastructure/
│   │   │   ├── integration/             # With DB/services
│   │   │   ├── conftest.py              # Pytest fixtures
│   │   │   └── __init__.py
│   │   ├── synthetic/                   # Synthetic data generation
│   │   ├── __init__.py
│   │   └── module_router.py             # Module-level router
│   │
│   ├── farmsuite/                       🌾 Intelligence Module (similar structure)
│   │   ├── domain/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   ├── api/
│   │   ├── tests/
│   │   └── [same pattern as farmscore]
│   │
│   ├── farmgrow/                        💬 RAG Chatbot (adjusted similarly)
│   │   └── [apply layered architecture]
│   │
│   └── __init__.py
│
├── core/                                Core Infrastructure
│   ├── database.py                      Supabase client & repository pattern
│   ├── ml_theory.py                     ML base classes
│   ├── ollama_service.py                Ollama integration
│   ├── schemas.py                       Shared data models
│   └── supabase_client.py               DB operations
│
├── auth/                                Authentication
├── config/                              Configuration
├── main.py                              FastAPI entry point
├── requirements.txt                     Dependencies
│
└── tests/                               Global tests
    ├── conft est.py                    Shared fixtures ⭐ NEW
    ├── fixtures/
    └── __init__.py
```

---

## 🚀 Quick Start (No Changes from v3.0)

### Start Everything
```bash
# Terminal 1: Ollama
ollama serve

# Terminal 2: Backend
cd farmiq-backend
python main.py

# Backend ready at: http://localhost:8000
```

### Health Check
```bash
curl http://localhost:8000/health | jq
```

---

## 🧪 Testing (NEW in v4.0)

### Run All Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests with coverage
pytest --cov=app --cov-report=html

# Run only unit tests (fast, no I/O)
pytest -m unit

# Run specific module tests
pytest app/farmscore/tests/unit/
```

### Test Fixtures (Reusable)
```python
# Import from conftest.py (global fixtures)
def test_credit_score(mock_db_repository, farmer_data, mock_credit_calculation_service):
    # Use fixtures for setup
    farmer = farmer_builder.with_experience(10).build()
    # Test logic here
```

---

## 🏛️ Key Improvements (v4.0)

| Aspect | Before | After | Benefit |
|--------|--------|-------|---------|
| **Code Reuse** | Duplicated util functions | Shared `base/` classes | 40% less code |
| **Error Handling** | Inconsistent HTTP mappings | Centralized exception mapping | Type-safe errors |
| **Testing** | Ad-hoc, no fixtures | Full pytest suite + fixtures | Easy test writing |
| **Scalability** | Mixed concerns | 3-layer separation | Better for growth  |
| **Consistency** | Different patterns/module | BaseService, BaseRepository | Uniform patterns |
| **Documentation** | Module docstrings | Layer-based organization | Self-documenting |

---

## 📚 Developer Workflows

### Adding a New Feature to FarmScore

```python
# 1. Define domain entity (app/farmscore/domain/entities/)
@dataclass
class MyEntity(BaseEntity):
    field: str
    
    def business_rule(self) -> bool:
        return len(self.field) > 0  # Pure logic

# 2. Define domain service (domain/services/)
class MyDomainService(BaseService):
    async def validate_input(self, data): ...
    def calculate_something(self): ...

# 3. Define repository (app/farmscore/application/repositories/)
class MyRepository(BaseRepository[MyEntity]):
    async def create(self, entity): ...

# 4. Define app service (application/services/)
class MyApplicationService(BaseService):
    def __init__(self, repo: MyRepository):
        self.repo = repo
    
    async def do_business_operation(self, request):
        # Orchestrate: domain logic + data access
        entity = await self.repo.get_by_id(...)
        result = entity.business_rule()
        return result

# 5. Define route (api/routes/)
@router.post("/my-endpoint")
async def my_endpoint(request: MyRequest, service: MyApplicationService = Depends(...)):
    try:
        result = await service.do_business_operation(request)
        return {"status": "success", "data": result}
    except DomainException as e:
        raise map_domain_exception_to_http(e)

# 6. Write tests (app/farmscore/tests/)
@pytest.mark.unit
async def test_my_domain_service(service):
    result = service.calculate_something()
    assert result > 0
```

### Adding a Shared Validator

```python
# In app/shared/utils/validation.py
def validate_my_field(value: str, field_name: str = "field") -> str:
    if not value:
        raise ValidationError(f"{field_name} cannot be empty")
    return value

# Use it everywhere
from app.shared import validate_my_field
validate_my_field(user_input, "username")
```

---

## � Migration Guide (v3.0 → v4.0)

### What Changed?

New layered architecture - **no breaking changes** to existing API endpoints.

### For Existing Code

**Old imports:**
```python
from farmiq_id_service import validate_farmiq_id  # ❌ old
from app.farmscore.services.feature_engineer import FeatureEngineer  # ❌ old
```

**New imports (recommended):**
```python
from auth.farmiq_id import validate_farmiq_id  # ✅ new
from app.farmscore.infrastructure.feature_engineering import FeatureEngineer  # ✅ new
```

**Existing code still works** - use at your own pace.

### For New Features

**Always follow the new architecture:**
```
Domain Entity → Domain Service → App Service + Repository → Route
```

---

## 💡 Common Patterns

###  Creating a Domain Entity
```python
from app.shared import BaseEntity, validate_positive

@dataclass
class Loan(BaseEntity):
    farmer_id: UUID
    amount_kes: float
    term_months: int
    
    def __post_init__(self):
        validate_positive(self.amount_kes, "loan amount")
        validate_positive(self.term_months, "term")
    
    def is_due_soon(self, days: int = 30) -> bool:
        """Domain logic - pure, testable"""
        due_date = self.created_at + timedelta(days=self.term_months * 30)
        return (due_date - datetime.utcnow()).days <= days
```

### Creating a Domain Service
```python
class LoanCalculationService(BaseService):
    async def validate_input(self, data):
        validate_not_empty(data.get('purpose'), 'purpose')
    
    def calculate_monthly_payment(self, amount: float, months: int, rate: float) -> float:
        """Pure business logic - no DB calls"""
        monthly_rate = rate / 100 / 12
        return amount * (monthly_rate * (1 + monthly_rate) ** months) / \
               ((1 + monthly_rate) ** months - 1)
```

### Creating an Application Service
```python
class LoanApplicationService(BaseService):
    def __init__(self, loan_repo: LoanRepository, calc_service: LoanCalculationService):
        super().__init__()
        self.loan_repo = loan_repo
        self.calc = calc_service
    
    async def apply_for_loan(self, request: LoanRequest) -> Loan:
        # Validate
        await self.validate_input(request.dict())
        
        # Calculate using domain service
        payment = self.calc.calculate_monthly_payment(
            request.amount_kes,
            request.term_months,
            request.interest_rate
        )
        
        # Create and persist
        loan = Loan(
            farmer_id=UUID(request.farmer_id),
            amount_kes=request.amount_kes,
            term_months=request.term_months
        )
        await self.loan_repo.create(loan)
        return loan
```

---

## �🚀 Quick Commands

### Start Everything
```bash
# Terminal 1: Ollama
ollama serve

# Terminal 2: Backend
cd farmiq-backend
python main.py

# Backend ready at: http://localhost:8000
```

### Health Check
```bash
curl http://localhost:8000/health | jq
```

### Phase 4: Generate Credit Scoring Models
```bash
# Terminal 3: Generate synthetic farmers + train models
cd farmiq-backend
python -c "
import asyncio
from app.farmscore.ml.training import run_credit_training_pipeline

result = asyncio.run(run_credit_training_pipeline(num_farmers=1000))
print(result.summary())
"

# Expected output: ROC-AUC > 0.85, models saved to ./models/credit_scoring/
```

---

## 🏗️ Modular Architecture Overview

```
FastAPI App (main.py)
    ├─ auth/              • FarmIQ ID validation
    │  ├─ farmiq_id.py    • ID format, storage, audit
    │  └─ dependencies.py • FastAPI dependency injection
    │
    ├─ config/            • Configuration management
    │  ├─ settings.py     • Environment settings
    │  └─ models.py       • Ollama model configs
    │
    ├─ core/              • Infrastructure
    │  ├─ database.py     • Supabase async repo
    │  ├─ ollama_service.py • Unified LLM interface
    │  ├─ schemas.py      • Pydantic validation
    │  └─ ml_theory.py    • ML base classes
    │
    ├─ app/farmgrow/      • RAG System (9 services)
    │  └─ services/
    │     ├─ orchestrator.py ← Main pipeline
    │     ├─ ingestion.py
    │     ├─ embeddings.py
    │     ├─ retrieval.py
    │     ├─ ranking.py
    │     ├─ llm.py
    │     ├─ ocr.py
    │     ├─ conversations.py
    │     └─ embedding_store.py
    │
    └─ app/farmscore/     • Credit Scoring + Phase 4 ML Pipeline ⭐
       ├─ synthetic/      ← NEW: Synthetic data generation (800+ lines)
       │  ├─ farmer_credit_generator.py
       │  └─ __init__.py
       ├─ ml/             ← NEW: ML training infrastructure
       │  ├─ training/
       │  │  ├─ credit_training_pipeline.py (900+ lines)
       │  │  └─ __init__.py
       │  ├─ models/
       │  │  └─ ensemble.py
       │  ├─ services/
       │  │  └─ feature_engineer.py
       │  └─ __init__.py
       ├─ services/
       │  └─ feature_engineer.py
       ├─ models/
       │  ├─ ensemble.py
       │  └─ loan.py
       └─ routes/
          └─ credit_scoring.py
```

---### Sample API Calls
```bash
# RAG Query
curl -X POST http://localhost:8000/api/v1/farmgrow/query \
  -H "Content-Type: application/json" \
  -H "X-FarmIQ-ID: FQK9M2XR" \
  -d '{"query": "How do I grow maize?", "user_id": "test"}'

# Credit Score
curl -X POST http://localhost:8000/api/v1/farmscore/score \
  -H "Content-Type: application/json" \
  -H "X-FarmIQ-ID: FQK9M2XR" \
  -d '{
    "annual_income": 250000,
    "land_size": 3.5,
    "years_farming": 8,
    "has_training": true
  }'
```

---

## 📁 File Structure Reference

```
farmiq-backend/
├── main.py                      # 🚀 Start here - app entry point
├── requirements.txt             # Python dependencies
│
├── auth/                        ⭐ NEW - Authentication Layer
│   ├── farmiq_id.py             # FarmIQ ID validation & storage
│   ├── dependencies.py          # FastAPI dependency injection
│   └── __init__.py              # Module exports
│
├── config/                      ⭐ NEW - Configuration Layer
│   ├── settings.py              # Environment settings (dev/staging/prod)
│   ├── models.py                # LLM model configurations (Ollama)
│   └── __init__.py              # Module exports
│
├── core/                        ✅ Infrastructure Layer
│   ├── database.py              # Supabase client & repository
│   ├── ollama_service.py        # Unified Ollama LLM interface
│   ├── schemas.py               # Pydantic models (type safety)
│   ├── ml_theory.py             # ML base classes & theory
│   ├── supabase_client.py       # Legacy Supabase wrapper
│   └── __init__.py              # Module exports
│
├── app/                         ✅ Application Logic
│   ├── __init__.py              # App module documentation
│   │
│   ├── farmgrow/                ← RAG System (9 modular services)
│   │   ├── routes.py            # API endpoints
│   │   ├── services/
│   │   │   ├── orchestrator.py  # Main RAG pipeline
│   │   │   ├── ingestion.py     # Document processing & PDF extraction
│   │   │   ├── embeddings.py    # Text embedding (BGE-M3)
│   │   │   ├── retrieval.py     # Hybrid retrieval (BM25 + vector)
│   │   │   ├── ranking.py       # Multi-signal ranking
│   │   │   ├── llm.py           # Answer generation (Ollama)
│   │   │   ├── ocr.py           # Image text extraction
│   │   │   ├── conversations.py # Chat history management
│   │   │   ├── embedding_store.py # Local embedding storage
│   │   │   └── __init__.py
│   │   └── __init__.py
│   │
│   └── farmscore/               ← Credit Scoring System ⭐ Phase 4
│       ├── routes.py            # Main router composition
│       │
│       ├── synthetic/           ⭐ PHASE 4: Synthetic Data Generation
│       │   ├─ farmer_credit_generator.py  # SyntheticFarmerCreditDataGenerator
│       │   │                              # - 47 Kenyan counties context
│       │   │                              # - 6 farm scenarios
│       │   │                              # - 20+ engineered credit features
│       │   │                              # - Realistic income/expense patterns
│       │   └─ __init__.py
│       │
│       ├── ml/                  ⭐ PHASE 4: ML Training Pipeline
│       │   ├─ training/
│       │   │  ├─ credit_training_pipeline.py  # FarmSCORETRAININGPipeline
│       │   │  │                                # - 7-stage async orchestration
│       │   │  │                                # - Data → Features → Train → Eval
│       │   │  │                                # - Save → Drift Detect
│       │   │  └─ __init__.py
│       │   │
│       │   ├─ models/
│       │   │  ├─ ensemble.py    # CreditScorer: GB + RF + LR voting
│       │   │  │                   # - Soft voting with isotonic calibration
│       │   │  │                   # - SHAP explainability
│       │   │  └─ __init__.py
│       │   │
│       │   ├─ services/
│       │   │  ├─ feature_engineer.py  # FeatureEngineer: 20+ features
│       │   │  │                        # - WOE binning (Weight of Evidence)
│       │   │  │                        # - Base + engineered features
│       │   │  └─ __init__.py
│       │   └─ __init__.py
│       │
│       ├── services/
│       │   ├─ feature_engineer.py  # WOE binning & feature engineering
│       │   └─ __init__.py
│       ├── models/
│       │   ├─ ensemble.py      # Voting ensemble (GB + RF + LR)
│       │   ├─ loan.py          # Loan recommendations (rates, limits, scenarios)
│       │   └─ __init__.py
│       ├── routes/
│       │   ├─ credit_scoring.py    # API endpoints: /score, /loan/apply, /loan/simulate
│       │   └─ __init__.py
│       └─ __init__.py
│
├── utils/                       ✅ Utility Functions
│   ├── metrics.py               # Performance metrics & monitoring
│   ├── validation.py            # Input validation
│   └── __pycache__/
│
├── scripts/                     ✅ Utility Scripts
│   └── train_ensemble_model.py  # ML model training
│
├── embeddings_cache/            # Local embedding storage
│   ├── metadata.json            # Chunk metadata
│   └── embeddings/              # NumPy embedding files (*.npy)
│
├── libraries/                   # Agricultural knowledge documents
│
├── documentation/
│   ├── PHASE4_QUICK_REFERENCE.md      # ⭐ Phase 4 quick-start guide
│   ├── PHASE4_IMPLEMENTATION.md       # ⭐ Phase 4 comprehensive docs
│   ├── PHASE4_PLAN.md                 # ⭐ Phase 4 strategic roadmap
│   ├── ARCHITECTURE.md                # System design & components
│   ├── MODULARIZATION_GUIDE.md        # Module organization & imports
│   ├── TESTING_GUIDE.md               # Test scenarios & procedures
│   ├── IMPLEMENTATION_SUMMARY.md      # Implementation details
│   └── README.md                      # This file
│
├── .env                         # Environment configuration (⚠️ Keep secret)
├── .env.development.local       # Local development overrides
│
└── supabase/
    └── migrations/
        └── 20260215000000_consolidated_farmiq_schema.sql  # Database schema
```

---

## 🔑 Key Concepts

### **FarmIQ ID**
- Format: `FQ` + 4 alphanumeric chars (e.g., `FQK9M2XR`)
- Unique identifier for each user
- Passed in `X-FarmIQ-ID` header
- Never changes after creation

### **RAG Pipeline**
```
User Question
    ↓
Embedding Generation
    ↓
Hybrid Retrieval (BM25 + Vector)
    ↓
Document Ranking
    ↓
LLM Answer Generation
    ↓
Conversation Storage
    ↓
Response to User
```

### **Service Architecture**
```
main.py (ServiceInitializer)
    ├→ Creates and caches all services
    ├→ Dependencies access via get_*_service()
    └→ Available in routes via FastAPI Depends()
```

---

## 📊 Database

### **Connection**
```python
from app.core.supabase_client import supabase_client

# Query
response = supabase_client.table("user_profiles").select("*").eq("farmiq_id", "FQK9M2XR").execute()
user = response.data[0] if response.data else None
```

### **Key Tables**
| Table | Purpose | Key Field |
|-------|---------|-----------|
| `user_profiles` | Core users | `farmiq_id`, `id` |
| `farmer_profiles` | Farmer info | `user_id`, `farmiq_id` |
| `conversations` | Chat sessions | `user_id`, `session_id` |
| `messages` | Chat messages | `conversation_id` |
| `documents` | Knowledge docs | `file_name`, `processing_status` |
| `embeddings` | Vector storage | `chunk_id`, `embedding` |

### **Active User Index**
```sql
-- For finding only active (non-deleted) users
idx_farmiq_id_active WHERE is_deleted = false
```

---

## 🔧 Phase 4: Credit Scoring Quick Start

### **Synthetic Data Generation**
```python
from app.farmscore.synthetic import SyntheticFarmerCreditDataGenerator, FarmScenario

# Create generator with Kenya context
gen = SyntheticFarmerCreditDataGenerator(seed=42)

# Generate 1000 farmers with realistic data
df = gen.generate_training_dataset(
    count=1000,
    default_rate=0.05  # 5% default rate
)

print(f"Generated {len(df)} farmers")
print(f"Features: {list(df.columns)}")  # 30+ columns
print(f"Counties: {df['county'].nunique()} Kenyan counties")
```

### **Training Pipeline**
```python
import asyncio
from app.farmscore.ml.training import run_credit_training_pipeline, CreditTrainingConfig

# Configure 7-stage training
config = CreditTrainingConfig(
    num_farmers=1000,
    default_rate=0.05,
    data_source="SYNTHETIC",
    train_ratio=0.70,
    val_ratio=0.15,
    test_ratio=0.15
)

# Run full pipeline (Data → Features → Train → Eval → Save → Drift Detect)
result = asyncio.run(run_credit_training_pipeline(num_farmers=1000, config=config))

# Examine results
print(result.summary())
print(f"ROC-AUC: {result.metrics.roc_auc:.3f}")  # Target > 0.85
print(f"Accuracy: {result.metrics.accuracy:.3f}")  # Target > 0.95
print(f"Models saved to: {result.model_path}")
```

### **Credit Scoring**
```python
from app.farmscore.models import CreditScorer

# Load trained ensemble
scorer = CreditScorer(ensemble=True)

# Engineer features
farmer_features = {
    'annual_income': 250000,
    'annual_expense': 100000,
    'farm_size_acres': 3.5,
    'years_farming': 8,
    'household_size': 5,
    'education_level': 2,
    'existing_debt': 50000,
    'crop_count': 3,
    'livestock_count': 2
}

# Get score
result = scorer.score(farmer_features)
print(f"Score: {result['score']} | Risk: {result['risk_level']}")
print(f"Default Prob: {result['default_probability']:.3f}")
```

### **Loan Recommendation**
```python
from app.farmscore.models import CreditRecommendationEngine

engine = CreditRecommendationEngine()

# Get loan recommendation with interest rate
recommendation = engine.recommend_loan(
    credit_score=82,
    default_probability=0.12,
    farm_size_acres=3.5,
    annual_income=250000
)

print(f"Approval: {recommendation['approval_likelihood']:.0%}")
print(f"Credit Limit: {recommendation['recommended_credit_limit']:,.0f} KES")
print(f"Interest Rate: {recommendation['recommended_interest_rate']:.1f}%")
print(f"Scenarios: {len(recommendation['loan_scenarios'])} available")
```

---

## 🔧 Module Imports (Updated)

### **Phase 4: FarmScore Credit Scoring Imports**
```python
# Synthetic Data Generation
from app.farmscore.synthetic import (
    SyntheticFarmerCreditDataGenerator,
    FarmScenario,
    EducationLevel
)

# Training Pipeline (7-stage)
from app.farmscore.ml.training import (
    run_credit_training_pipeline,
    CreditTrainingConfig,
    CreditTrainingResult,
    FarmSCORETRAININGPipeline
)

# Models & Scoring
from app.farmscore.models import (
    CreditScorer,          # 3-model ensemble
    CreditRecommendationEngine  # Loan recommendations
)

# Features
from app.farmscore.services import FeatureEngineer  # 20+ features
```

### **Auth Module**
```python
from auth.farmiq_id import FarmiqIdValidator, FarmiqIdStorage, FarmiqIdAudit
from auth.dependencies import (
    get_farmiq_id_from_header,
    get_user_by_farmiq_id,
    get_user_context,
    get_embedding_service,
    get_llm_service,
    get_conversation_service,
    get_retrieval_service,
    get_ingestion_service
)
```

### **Config Module**
```python
from config.settings import Settings, settings
from config.models import (
    ModelConfig,
    ModelSelector,
    TEXT_MODELS,
    EMBEDDING_MODEL,
    OCR_MODEL,
    DEFAULT_TEXT_MODEL,
    EMBEDDING_MODEL_NAME,
    OCR_MODEL_NAME,
)
```

### **Core Module**
```python
from core.database import SupabaseClientFactory, DatabaseRepository, get_supabase_client
from core.ollama_service import OllamaService, get_ollama_service
from core.schemas import CreditRiskLevel, DocumentCategory
from core.ml_theory import MLModel, ClassificationModel, RegressionModel
```

### **App Modules**
```python
# FarmGrow RAG
from app.farmgrow.services import RAGOrchestrator, EmbeddingService, OllamaLLMService
from app.farmgrow.routes import router as farmgrow_router

# FarmScore Credit
from app.farmscore.models import CreditScorer, CreditRecommendationEngine
from app.farmscore.services import FeatureEngineer
from app.farmscore.routes import router as farmscore_router
```

---

### **Service List**
| Service | Purpose | Key Method |
|---------|---------|-----------|
| `OllamaService` | LLM inference | `generate(prompt)` |
| `EmbeddingService` | Text embeddings | `generate_embedding(text)` |
| `RAGRetriever` | Document search | `retrieve(query, top_k)` |
| `OllamaLLMService` | Answer generation | `generate_answer(query, context)` |
| `ConversationService` | Chat history | `add_message(conversation_id, role, content)` |
| `DocumentIngestionService` | PDF processing | `ingest_all_documents()` |

### **Using in Routes**
```python
from fastapi import Depends
from auth.dependencies import get_llm_service, get_embedding_service

@app.post("/query")
async def my_endpoint(
    query: str,
    llm = Depends(get_llm_service),
    embeddings = Depends(get_embedding_service)
):
    # Services are ready to use
    result = await embeddings.generate_embedding(query)
    answer = await llm.generate_answer(query, context=[])
    return {"answer": answer}
```

---

## 🛠️ Common Tasks

### **Add a New RAG Query Handler**
```python
# Location: app/farmgrow/routes.py
from fastapi import APIRouter, Depends
from auth.dependencies import get_rag_orchestrator

router = APIRouter(prefix="/api/v1/farmgrow")

@router.post("/custom-query")
async def custom_query(
    query: str,
    orchestrator = Depends(get_rag_orchestrator)
):
    response = await orchestrator.process_query(query)
    return {
        "answer": response.answer,
        "confidence": response.confidence,
        "sources": response.sources
    }
```

### **Add a New Credit Scoring Feature**
```python
# Location: app/farmscore/services/feature_engineer.py
# Extend FeatureEngineer class

def calculate_new_feature(self, farmer_data):
    """Calculate a new agricultural feature"""
    
    # Feature logic here
    feature_value = farmer_data['some_field'] * multiplier
    
    return feature_value

# Then in ensemble.py, add to feature vector
```

### **Update Database Schema**
```bash
# Create new migration file:
supabase/migrations/YYYYMMDDHHMMSS_description.sql

# In Supabase SQL editor:
# 1. Paste migration content
# 2. Execute
# 3. Test queries
```

---

## 🧪 Testing

### **Unit Test Template**
```python
import pytest
from app.farmgrow.services.llm import OllamaLLMService

@pytest.pytest.mark.asyncio
async def test_llm_generation():
    llm = OllamaLLMService()
    result = await llm.generate_answer("test query", [])
    assert result is not None
    assert len(result) > 0
```

### **Integration Test Template**
```python
@pytest.mark.asyncio
async def test_full_rag_pipeline():
    # Test the complete flow
    query = "How do I grow maize?"
    
    response = client.post(
        "/api/v1/farmgrow/query",
        json={"query": query, "user_id": "test"},
        headers={"X-FarmIQ-ID": "FQK9M2XR"}
    )
    
    assert response.status_code == 200
    assert "answer" in response.json()
```

---

## 🐛 Debugging

### **Enable Debug Logging**
```python
# In main.py
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Or in .env
LOG_LEVEL=DEBUG
```

### **Check Service Status**
```bash
curl http://localhost:8000/status | jq

# Output should show all services: RAG, Credit, Ollama, Database OK
```

---

## 🚢 Deployment

### **Environment Variables**
```bash
# .env (create from .env.example)
SUPABASE_URL=https://abc.supabase.co
SUPABASE_KEY=secret-key
OLLAMA_HOST=http://localhost:11434
LOG_LEVEL=INFO
ENVIRONMENT=production
```

### **Docker Build** (Future)
```bash
docker build -t farmiq-backend:latest .
docker run -p 8000:8000 --env-file .env farmiq-backend:latest
```

### **Deploy to Azure**
```bash
# Using Azure CLI
az container create \
  --resource-group farmiq \
  --name farmiq-backend \
  --image farmiq-backend:latest \
  --ports 80 \
  --environment-variables SUPABASE_URL=... SUPABASE_KEY=...
```

---

## 📈 Performance Optimization

### **Caching**
```python
# Cache credit scores for 90 days
@cached(ttl=7776000)  # 90 days
def get_cached_credit_score(user_id: str):
    return calculate_credit_score(user_id)
```

### **Batch Processing**
```python
# Process multiple farmers at once
from app.farmscore.services import FeatureEngineer

engineer = FeatureEngineer()
batch_features = engineer.engineer_features(df_farmers)  # Vectorized
```

### **Query Optimization**
```python
# Add indexes to Supabase tables
CREATE INDEX idx_farmiq_id_active ON user_profiles(farmiq_id) WHERE is_active = true;
CREATE INDEX idx_user_conversations ON conversations(user_id, created_at DESC);
```

---

## 🤝 Contributing

### **Coding Standards**
- ✅ Follow PEP 8 (use `black` for formatting)
- ✅ Type hints on all functions
- ✅ Docstrings: module, class, public method
- ✅ Tests: 70%+ coverage target
- ✅ Async/await for I/O operations

### **Branch Strategy**
```bash
git branch -b feature/add-my-feature    # Feature branch
git commit -m "feat: add new feature"   # Conventional commits
git push origin feature/add-my-feature
# Open PR for review
```

---

## 📞 Support & Issues

### **Common Issues**

| Issue | Solution |
|-------|----------|
| Ollama not running | `ollama serve` in separate terminal |
| Supabase connection timeout | Check internet connection & API key |
| Import errors | Ensure `PYTHONPATH` includes project root |
| Port 8000 already in use | `lsof -i :8000` and kill the process |
| CORS errors | Check `ALLOWED_ORIGINS` in config |

### **Debug Endpoints**
```bash
# Health check
GET /health

# System status
GET /status

# Service info
GET /info
```

---

## 📚 Additional Resources

- [Angular Frontend Docs](../farmiq/README.md)
- [Supabase Schema](../supabase/migrations/)
- [API Documentation](http://localhost:8000/docs) (SwaggerUI)
- [Phase 4 Details](documentation/PHASE4_IMPLEMENTATION.md)

---

## 📄 License

FarmIQ - Agricultural Intelligence Platform for Smallholder Farmers
(c) 2024-2026 | All Rights Reserved

---

**Last Update:** March 15, 2026
**Version:** 4.0 (Layered Architecture with DDD)
**Maintainer:** FarmIQ Development Team
```python
from main import ServiceInitializer

status = ServiceInitializer.get_health_status()
print(f"Initialized: {status['initialized']}")
print(f"Services: {status['services']}")
print(f"Errors: {status['errors']}")
```

### **Verify Modular Imports**
```python
# Test import paths
from auth import FarmiqIdValidator, get_user_context
from config import settings, ModelSelector
from core import OllamaService, SupabaseClientFactory
from app.farmgrow.services import RAGOrchestrator
from app.farmscore.models import CreditScorer

print("✅ All modular imports successful!")
```

### **Common Errors**
```
❌ "ModuleNotFoundError: No module named 'auth'"
   → Check: auth/ folder exists with __init__.py
   → Fix: Ensure working directory is farmiq-backend

❌ "from config_models import" (old import)
   → Check: Use new modular import path
   → Fix: Change to "from config.models import"

❌ "from dependencies import" (old import)
   → Check: Use new auth module
   → Fix: Change to "from auth.dependencies import"

❌ "Ollama not responding"
   → Check: ollama serve is running
   → Fix: ollama serve in terminal

❌ "Module not found: app.farmgrow"
   → Check: Working directory is farmiq-backend
   → Fix: cd farmiq-backend

❌ "Supabase client not initialized"
   → Check: SUPABASE_URL in .env
   → Fix: Verify credentials in Supabase dashboard

❌ "Models not found"
   → Check: ollama pull mistral:7b-instruct
   → Fix: Pull each model manually
```

---

## 📊 Configuration

### **.env Template**
```bash
# Environment
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Server
HOST=0.0.0.0
PORT=8000

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_TEXT_MODEL=mistral:7b-instruct

# CORS
CORS_ORIGINS=http://localhost:4200,http://localhost:3000
```

### **Model Selection**
```python
# In config/models.py
DEFAULT_TEXT_MODEL = 'mistral:7b-instruct'  # ← Change here (⚡ 5-6x faster)
DEFAULT_EMBEDDING_MODEL = 'bge-m3:latest'  # Multilingual embeddings
DEFAULT_OCR_MODEL = 'deepseek-ocr:latest'  # Image text extraction
```

---

## 📈 Performance Tuning

### **Embedding Performance**
```python
# Batch multiple texts instead of single
# Before (slow):
embeddings = [generate_embedding(text) for text in texts]

# After (fast):
embeddings = generate_embeddings(texts)  # Vectorized
```

### **Query Performance**
```python
# Specify top_k to limit results
response = await retriever.retrieve(
    query=query,
    top_k=5,  # ← Limit to needed results
    similarity_threshold=0.3  # ← Filter low-quality results
)
```

### **Database Optimization**
```sql
-- Use indexes for common queries
EXPLAIN ANALYZE
SELECT * FROM messages 
WHERE conversation_id = 'xxx' 
ORDER BY created_at DESC;
-- Should use idx_messages_conversation_id index
```

---

## 🚀 Deployment

### **Development**
```bash
python main.py
```

### **Production**
```bash
# With gunicorn
gunicorn main:app --workers 4 --bind 0.0.0.0:8000

# Or with uvicorn
uvicorn main:app --workers 4 --host 0.0.0.0 --port 8000
```

### **Docker**
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

---

## 📚 Documentation Map

| Document | Purpose | Read When |
|----------|---------|-----------|
| **PHASE4_QUICK_REFERENCE.md** | 🆕 Phase 4 fast-track guide, API examples, Kenya context | Getting started with credit scoring |
| **PHASE4_IMPLEMENTATION.md** | 🆕 Phase 4 architecture, features, pipeline stages | Deep dive into credit scoring system |
| **PHASE4_PLAN.md** | 🆕 Phase 4 strategic roadmap, validation metrics | Understanding Phase 4 objectives |
| **MODULARIZATION_GUIDE.md** | Module organization & imports | Understanding modular structure |
| **ARCHITECTURE.md** | System design & components | Onboarding, design decisions |
| **TESTING_GUIDE.md** | Testing scenarios | QA, validation, load testing |
| **IMPLEMENTATION_SUMMARY.md** | Implementation details | Understanding changes |
| **This file** | Quick reference | Daily development |

---

## � Learn More

**Phase 4 Documentation** (Recommended starting points):
- **PHASE4_QUICK_REFERENCE.md** - Fast-track guide with examples & Kenya context ⭐ START HERE
- **PHASE4_IMPLEMENTATION.md** - Comprehensive architecture & feature engineering
- **PHASE4_PLAN.md** - Strategic roadmap & validation metrics

**Architecture & Design:**
- **Modularization Guide:** [MODULARIZATION_GUIDE.md](MODULARIZATION_GUIDE.md) - Module organization & import patterns
- **Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md) - System design & component details

**Interactive Docs:**
- **API Docs:** http://localhost:8000/docs (automatic Swagger)
- **ReDoc:** http://localhost:8000/redoc (alternative API docs)

---

## 🔗 Important Links

- **Supabase Dashboard:** https://app.supabase.com
- **Ollama:** http://localhost:11434
- **API Health Check:** http://localhost:8000/health

---

## 💡 Tips & Tricks

### **Auto-reload during development**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### **Access API docs**
```
http://localhost:8000/docs       # Swagger UI
http://localhost:8000/redoc      # ReDoc
```

### **Check model versions**
```bash
ollama list
# mistral:7b-instruct    <model>  11b    2024-02-14
# bge-m3:latest          <model>  4.3gb  2024-01-15
```

### **Monitor logs in real-time**
```bash
tail -f farmiq-backend.log | grep ERROR
```

---

## ⚡ Quick Decisions

| Scenario | Action | Location |
|----------|--------|----------|
| Generate synthetic farmers | Use SyntheticFarmerCreditDataGenerator | `app/farmscore/synthetic/farmer_credit_generator.py` |
| Train credit scoring models | Run 7-stage pipeline | `app/farmscore/ml/training/credit_training_pipeline.py` |
| Score a farmer | Use CreditScorer ensemble | `app/farmscore/models/ensemble.py` |
| Get loan recommendation | Use CreditRecommendationEngine | `app/farmscore/models/loan.py` |
| New RAG feature | Add to `orchestrator.py` | `app/farmgrow/services/orchestrator.py` |
| New credit feature | Add to `feature_engineer.py` | `app/farmscore/services/feature_engineer.py` |
| New API endpoint | Add to routes | `app/farmgrow/routes.py` or `app/farmscore/routes/` |
| New authentication logic | Add to dependencies | `auth/dependencies.py` |
| New configuration setting | Add to settings | `config/settings.py` |
| New LLM model config | Update models.py | `config/models.py` |
| New DB table | Add migration | `supabase/migrations/` |
| New validation rule | Add to validation | `utils/validation.py` |
| New metric | Add tracking | `utils/metrics.py` |

---

**Happy coding! 🌾**

**For detailed information, start with:**
- 🆕 **[PHASE4_QUICK_REFERENCE.md](PHASE4_QUICK_REFERENCE.md)** - Phase 4 credit scoring quick-start
- 🆕 **[PHASE4_IMPLEMENTATION.md](PHASE4_IMPLEMENTATION.md)** - Phase 4 comprehensive guide
- 🆕 **[PHASE4_PLAN.md](PHASE4_PLAN.md)** - Phase 4 strategic roadmap
- [ARCHITECTURE.md](ARCHITECTURE.md) - Full system architecture
- [TESTING_GUIDE.md](TESTING_GUIDE.md) - Testing scenarios & procedures
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - What was done
