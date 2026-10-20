# Intelligent Cloud Auto-Scaling — Backend

FastAPI and SQLAlchemy backend for the **Intelligent Cloud Auto-Scaling Framework for E-Commerce Festival Sales Using Reinforcement Learning**. Local development uses SQLite; cloud database and AWS credentials are deployment concerns.

---

## 1. System Architecture & Work Distribution

```
                                    ┌──────────────────────────────────────┐
                                    │    Frontend (Khushi Agarwal)         │
                                    │  - Festival Flash Sale UI            │
                                    │  - Customer Cart & Checkout          │
                                    └──────────────────┬───────────────────┘
                                                       │  REST API / JWT
                                                       ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 Backend Subsystem (Ivy Gupta)                                            │
│  FastAPI + SQLAlchemy 2.0 Async Engine + Connection Pooling (20/30) + Structured Logging                │
│                                                                                                          │
│  ┌─────────────────────────┐  ┌──────────────────────────────┐  ┌─────────────────────────────────────┐  │
│  │   Auth & Transactions   │  │   CloudWatch & ELB Telemetry │  │     RL Scaling Orchestrator         │  │
│  │  - User Auth (JWT/Bcrypt│  │  - CPU / Memory ingestion    │  │  - POST /scaling/decision           │  │
│  │  - Flash Sale Checkout  │  │  - Request rate & latency    │  │  - POST /scaling/evaluate-and-act   │  │
│  │  - Sales Statistics     │  │  - Smoothed RL state vector  │  │  - RL feedback reward logging       │  │
│  └────────────┬────────────┘  └──────────────┬───────────────┘  └──────────────────┬──────────────────┘  │
└───────────────┼──────────────────────────────┼─────────────────────────────────────┼─────────────────────┘
                │                              │                                     │
                ▼                              ▼                                     ▼
   ┌─────────────────────────┐   ┌───────────────────────────┐         ┌───────────────────────────┐
   │ Amazon RDS (PostgreSQL/ │   │ CloudWatch / ELB Metrics  │         │ AI / RL Scaling Module    │
   │ MySQL with SSL & Pool)  │   │  (Simulated / Live Feed)  │         │     (Arpita Sinha)        │
   │  - Users & Transactions │   └───────────────────────────┘         │  - SAC / PPO Policy Agent │
   │  - Telemetry Metrics    │                                         └─────────────┬─────────────┘
   │  - Scaling Audit Trail  │                                                       │ Target Desired
   └─────────────────────────┘                                                       ▼ Capacity
                                                                       ┌───────────────────────────┐
                                                                       │ AWS Auto Scaling Group    │
                                                                       │  - EC2 Instance Fleets    │
                                                                       │  - Boto3 / Mock Mode      │
                                                                       └───────────────────────────┘
```

---

## 2. Directory Structure

```
src/backend/
├── app/
│   ├── main.py                  # FastAPI app with CORS and lifespan table initialization
│   ├── config.py                # Environment configuration (Pydantic BaseSettings)
│   ├── database.py              # SQLAlchemy engine with connection pooling & RDS SSL
│   ├── models/                  # User, Transaction, WorkloadMetric, ScalingDecision
│   ├── schemas/                 # Pydantic schemas (User, Order, Telemetry, Scaling)
│   ├── routers/                 # health, auth, transactions, workload, scaling
│   ├── services/                # ai_client, aws_asg_client, workload_service
│   └── utils/                   # Direct bcrypt hashing, JWT tokens, structured logging
├── scripts/
│   ├── init_db.py               # Table creation script (PostgreSQL, MySQL, SQLite)
│   ├── seed_data.py             # Synthetic festival users, orders, & metrics seeder
│   └── simulate_traffic.py      # Real-time festival traffic spike simulator
├── tests/                       # Automated unit and integration tests
├── .env.example                 # Config template for Amazon RDS & AWS
├── pytest.ini                   # Pytest configuration
├── requirements.txt             # Backend dependencies
├── run.py                       # Uvicorn entrypoint runner
└── README.md                    # Complete backend reference documentation
```

---

## 3. Quickstart & Local Setup

### Step 1: Install Dependencies
```bash
Set-Location src\backend
py -3.12 -m pip install -r requirements.txt
```

### Step 2: Configure Environment
```bash
if (-not (Test-Path .env)) { Copy-Item .env.example .env } else { Write-Host 'Preserving existing .env' }
```
*(`.env.example` uses SQLite, `AWS_MOCK_MODE=true`, and disabled live-scaling gates. Local development and automated tests stay in mock mode. The AWS integration guide documents an owner-controlled read-only preflight and live-test procedure.)*

### Step 3: Initialize Database & Seed Synthetic Festival Data
```bash
# Create schema tables
py -3.12 scripts/init_db.py

# Seed festival users, flash sale orders, metrics, and scaling decisions
py -3.12 scripts/seed_data.py
```

### Step 4: Launch Backend Server
```bash
py -3.12 run.py
# or directly via uvicorn:
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Interactive Swagger API documentation is available at: **http://127.0.0.1:8000/docs**

---

## 4. REST API Reference

### Health & Monitoring
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Service liveness & version check |
| `GET` | `/api/v1/health/db` | Database connectivity & pool statistics check |

### Authentication & User Management (Khushi's Frontend)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Register new festival shopper (`email`, `password`, `full_name`) |
| `POST` | `/api/v1/auth/login` | Authenticate shopper and return JWT token |
| `GET` | `/api/v1/auth/me` | Fetch authenticated user profile (requires `Bearer` token) |

### Transactions & Flash Sale Checkout (Khushi's Frontend)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/transactions/checkout` | High-speed checkout during flash sales |
| `GET` | `/api/v1/transactions` | Query orders with optional `user_id` filter |
| `GET` | `/api/v1/transactions/{id}` | Fetch individual transaction details |
| `GET` | `/api/v1/transactions/stats` | Festival sales metrics (total revenue, order count, AOV) |

### Workload Telemetry (CloudWatch / ELB Metrics)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/workload/metrics` | Ingest caller-provided values, labeled `manual_simulated` |
| `POST` | `/api/v1/workload/batch` | Bulk ingest historical / stream metrics |
| `GET` | `/api/v1/workload/latest` | Retrieve latest system telemetry |
| `GET` | `/api/v1/workload/history` | Historical metrics time-series |
| `GET` | `/api/v1/workload/state` | Smoothed rolling state vector for the RL agent |
| `GET` | `/api/v1/workload/aws/current` | Fetch current read-only CloudWatch telemetry when configured |

### AI / RL Auto-Scaling Orchestrator (Arpita's RL Module)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/scaling/decision` | Evaluate RL policy decision without modifying ASG |
| `POST` | `/api/v1/scaling/evaluate-and-act` | Complete loop: pull state, query RL, scale ASG, log in RDS |
| `POST` | `/api/v1/scaling/evaluate-cloudwatch` | Evaluate fresh CloudWatch telemetry; writes require explicit gates and request opt-in |
| `POST` | `/api/v1/scaling/feedback` | Ingest post-scaling latency and record RL experience reward |
| `GET` | `/api/v1/scaling/history` | Query audit trail of past scaling actions and rewards |
| `GET` | `/api/v1/scaling/aws/preflight` | Read-only AWS identity, target, capacity, health and activity checks |

---

## 5. Simulating Traffic Spikes (AWS mutations disabled)

To test the backend under festival flash-sale traffic surges:
```bash
python3 scripts/simulate_traffic.py --rounds 15 --delay 0.3
```
This script creates a multi-phase synthetic surge and records policy decisions. It sends `apply_to_aws=false`; it does not change mock or real AWS capacity. For real AWS configuration, IAM requirements, read-only preflight and explicitly approved live-test steps, see [AWS_INTEGRATION_GUIDE.md](AWS_INTEGRATION_GUIDE.md).

---

## 6. Running Automated Tests

Run the complete test suite with pytest (from `src/backend`, Windows PowerShell):
```bash
py -3.12 -m pytest -p no:cacheprovider tests/ -q
```
Tests use isolated in-memory SQLite fixtures and force `AWS_MOCK_MODE=true`. Results verify local policy/API behavior only; they do not establish AWS access or live Auto Scaling behavior. See [project readiness](../../docs/project-readiness.md) for the latest command and result.
