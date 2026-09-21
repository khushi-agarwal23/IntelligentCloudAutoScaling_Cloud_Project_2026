# Amazon RDS Integration & Setup Guide

This guide provides an end-to-end walkthrough for deploying, securing, and integrating **Amazon Relational Database Service (Amazon RDS)** with the backend of the **Intelligent Cloud Auto-Scaling Framework for E-Commerce Festival Sales**.

---

## 1. Architectural Overview

During e-commerce festival flash sales, the database must handle sharp bursts of user logins, catalog queries, transactions, and high-frequency workload telemetry (from CloudWatch and ELB).

```
                                      AWS VPC (10.0.0.0/16)
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                        │
│   Public / App Subnet (us-east-1a)                Public / App Subnet (us-east-1b)                     │
│   ┌────────────────────────────────┐              ┌────────────────────────────────┐                   │
│   │ EC2 Backend Application Fleet  │              │ EC2 Backend Application Fleet  │                   │
│   │ Security Group: app-backend-sg │              │ Security Group: app-backend-sg │                   │
│   └───────────────┬────────────────┘              └───────────────┬────────────────┘                   │
│                   │                                               │                                    │
│                   │ Port 5432 (SSL)                               │ Port 5432 (SSL)                    │
│                   ▼                                               ▼                                    │
│   ┌────────────────────────────────────────────────────────────────────────────────┐                   │
│   │                        Amazon RDS PostgreSQL Multi-AZ Cluster                  │                   │
│   │                      Security Group: rds-autoscaling-sg (Port 5432)            │                   │
│   │                                                                                │                   │
│   │    Private Subnet 1 (us-east-1a)                  Private Subnet 2 (us-east-1b)│                   │
│   │    ┌───────────────────────────┐                  ┌───────────────────────────┐│                   │
│   │    │ Primary RDS Master DB     │ ═══════════════> │ Standby Replica (Multi-AZ)││                   │
│   │    │  - Connection Pool (20/30)│ Synchronous Rep  │  - Instant Failover       ││                   │
│   │    └───────────────────────────┘                  └───────────────────────────┘│                   │
│   └────────────────────────────────────────────────────────────────────────────────┘                   │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Step-by-Step Provisioning Guide

### Step 1: Create DB Subnet Group
Amazon RDS requires a DB subnet group containing subnets in at least two Availability Zones in your VPC.

1. Open the **AWS Management Console** and navigate to **RDS**.
2. In the left navigation pane, select **Subnet groups** > click **Create DB subnet group**.
3. Fill in the details:
   - **Name**: `scaling-rds-subnet-group`
   - **Description**: `Subnet group for festival auto-scaling backend`
   - **VPC**: Select your project VPC (e.g., `vpc-0123456789abcdef0`).
4. Under **Add subnets**:
   - Select your AWS region (e.g., `us-east-1`).
   - Select at least two Availability Zones (e.g., `us-east-1a`, `us-east-1b`).
   - Choose the private subnets associated with those AZs.
5. Click **Create**.

---

### Step 2: Configure VPC Security Groups
Security groups act as virtual firewalls to protect your database.

1. Navigate to **EC2** > **Security Groups** > click **Create security group**.
2. Create `rds-autoscaling-sg`:
   - **Security group name**: `rds-autoscaling-sg`
   - **Description**: `Inbound access for backend EC2 instances to Amazon RDS`
   - **VPC**: Select the same VPC as your RDS instance.
3. Configure **Inbound Rules**:
   - **Type**: `PostgreSQL` (Port `5432`) or `MySQL/Aurora` (Port `3306`).
   - **Source**:
     - *For Production inside VPC*: Select the Security Group ID of your backend EC2 instances (e.g., `sg-0abc1234backend`).
     - *For Direct Local Development Testing*: Select `My IP` (to allow your local development IP address only).
4. Click **Create security group**.

---

### Step 3: Launch the Amazon RDS Database Instance

1. Navigate to **RDS** > **Databases** > click **Create database**.
2. **Choose a database creation method**: Select `Standard create`.
3. **Engine options**:
   - Engine type: **PostgreSQL** (Recommended version: `16.2` or later) *or* **MySQL** (`8.0.x`).
4. **Templates**:
   - Choose **Free tier** for initial staging and development.
   - Choose **Production** with **Multi-AZ DB cluster** for final festival performance evaluation.
5. **Settings**:
   - **DB instance identifier**: `ecommerce-scaling-rds`
   - **Master username**: `db_user`
   - **Master password**: Enter a secure password (e.g., `FestivalScale2026!Secure`).
6. **Instance configuration**:
   - Free tier: `db.t4g.micro` or `db.t3.micro`
   - Production / Load Testing: `db.m6g.large` or `db.c6g.large`
7. **Storage**:
   - Storage type: `gp3` (General Purpose SSD)
   - Allocated storage: `20 GiB` (free tier) or `100 GiB` (production)
   - Enable storage autoscaling: **Yes** (Threshold: `500 GiB`)
8. **Connectivity**:
   - **Virtual Private Cloud (VPC)**: Select your project VPC.
   - **DB subnet group**: Choose `scaling-rds-subnet-group`.
   - **Public access**:
     - Choose **Yes** if connecting from local development without a VPN / bastion host.
     - Choose **No** if deployed strictly within private AWS subnets.
   - **VPC security group (firewall)**: Choose `rds-autoscaling-sg`.
9. **Additional configuration**:
   - **Initial database name**: `ecommerce_db`
   - **DB parameter group**: Default or custom with `max_connections >= 200`
   - **Enable automated backups**: Yes (Retention: 7 days)
   - **Encryption**: Enable encryption (AWS KMS key `aws/rds`)
10. Click **Create database**. Provisioning typically takes 5–10 minutes.

---

### Step 4: Configure Backend Environment (`.env`)

Once the RDS status becomes **Available**, copy the **Endpoint** from the RDS console.

In `src/backend/.env`, set the following environment variables:

```env
# Disable SQLite to enable Amazon RDS PostgreSQL
USE_SQLITE=false

# Full SQLAlchemy 2.0 Connection URL
DATABASE_URL=postgresql+psycopg2://db_user:FestivalScale2026!Secure@ecommerce-scaling-rds.c3xxxx.us-east-1.rds.amazonaws.com:5432/ecommerce_db

# RDS Connection Parameters
DB_HOST=ecommerce-scaling-rds.c3xxxx.us-east-1.rds.amazonaws.com
DB_PORT=5432
DB_NAME=ecommerce_db
DB_USER=db_user
DB_PASSWORD=FestivalScale2026!Secure
DB_SSL_MODE=require

# High-Concurrency Connection Pooling (Tuned for Festival Flash Sales)
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_PRE_PING=true
DB_POOL_RECYCLE=1800
DB_POOL_TIMEOUT=30
```

*(If using **Amazon RDS MySQL**, set `DATABASE_URL=mysql+pymysql://db_user:password@endpoint:3306/ecommerce_db`)*.

---

### Step 5: Initialize Tables & Seed Synthetic Festival Data

Run the database initializer script to automatically create all tables in Amazon RDS:

```bash
# Verify connection and create tables in RDS
python3 src/backend/scripts/init_db.py

# Seed festival users, flash sale orders, metrics, and scaling logs
python3 src/backend/scripts/seed_data.py
```

---

### Step 6: Verify Database Connectivity in FastAPI

Start the backend and test the database health check endpoint:

```bash
# Start backend
python3 -m uvicorn app.main:app --app-dir src/backend --port 8000

# Test database health
curl http://127.0.0.1:8000/api/v1/health/db
```

Expected JSON Response:
```json
{
  "status": "connected",
  "database_dialect": "postgresql",
  "connection_pool": {
    "size": 20,
    "checked_in": 1,
    "checked_out": 0,
    "overflow": 0
  }
}
```

---

## 3. High-Concurrency Connection Pooling & Festival Optimization

During festival sales, thousands of shoppers simultaneously check out products. If each incoming web worker opened an unpooled connection to Amazon RDS, the database would rapidly encounter connection exhaustion (`FATAL: remaining connection slots are reserved`).

Our backend implements high-performance connection pooling via SQLAlchemy 2.0:
- **`DB_POOL_SIZE=20`**: Maintains a steady pool of 20 pre-warmed connections.
- **`DB_MAX_OVERFLOW=30`**: Dynamically creates up to 30 additional temporary connections during traffic spikes (total 50 concurrent DB connections per backend worker).
- **`DB_POOL_PRE_PING=true`**: Emits a lightweight `SELECT 1` ping before borrowing a connection from the pool. If Amazon RDS terminated an idle connection due to network timeout, SQLAlchemy transparently recycles it without failing customer requests.
- **`DB_POOL_RECYCLE=1800`**: Periodically closes connections older than 30 minutes to prevent memory leaks and stale socket state.

---

## 4. Troubleshooting Common Amazon RDS Issues

### Issue 1: Connection Timeout (`could not connect to server: Connection timed out`)
- **Cause**: Security group inbound rules are blocking the client IP address, or RDS is not in a public subnet with an Internet Gateway.
- **Fix**:
  1. Check RDS Security Group `rds-autoscaling-sg`.
  2. Verify that your current public IP is listed in the inbound rule for port `5432` / `3306`.
  3. Ensure **Publicly Accessible** is set to **Yes** if connecting from outside the VPC.

### Issue 2: SSL Connection Failure (`FATAL: no pg_hba.conf entry for host ... SSL off`)
- **Cause**: Amazon RDS enforces SSL/TLS encryption for database connections.
- **Fix**:
  - In `src/backend/.env`, verify `DB_SSL_MODE=require`.
  - The backend engine automatically appends `sslmode=require` to PostgreSQL and `ssl_mode=REQUIRED` to MySQL connections.

### Issue 3: Table Creation Permission Denied
- **Cause**: The master user or role lacks `CREATE TABLE` permissions on the database.
- **Fix**:
  - Connect with master credentials (`db_user`) and run:
    ```sql
    GRANT ALL PRIVILEGES ON DATABASE ecommerce_db TO db_user;
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO db_user;
    ```

---

## 5. Security Checklist
- [x] Master database credentials stored strictly in `.env` (never committed to Git).
- [x] SSL encryption (`DB_SSL_MODE=require`) enforced for all in-transit traffic.
- [x] Multi-AZ deployment enabled for production high availability and automatic failover.
- [x] Inbound security group rules restricted strictly to backend EC2 instances.
