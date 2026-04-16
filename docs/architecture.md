# System Architecture

**Version:** 2.0  
**Consolidated from:** project-data.md, data-architecture.md, architecture.mermaid, README-IMPLEMENTATION.md

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Architecture Overview](#system-architecture-overview)
3. [Module Specifications](#module-specifications)
4. [IPC Bridge Design](#ipc-bridge-design)
5. [Data Layer Design](#data-layer-design)
6. [Technology Stack](#technology-stack)

---

## Executive Summary

This is a hybrid COBOL + Python banking system demonstrating how legacy COBOL systems can be extended with modern big data capabilities through an Inter-Process Communication (IPC) bridge.

**Core Innovation:** COBOL programs delegate data-intensive operations to Python scripts that query a modern analytical data layer (Apache Parquet + DuckDB). This allows COBOL to handle transaction processing while Python provides large-scale analytics, ML-based scoring, and real-time anomaly detection.

**The Thesis Problem:** COBOL (deployed in 95% of ATM and 80% of in-person banking transactions) was architected for sequential file processing on megabyte-scale data. Modern banking demands real-time analytics over petabyte-scale datasets—operations COBOL was never designed for.

**The Solution:** Keep COBOL for business logic, extend it with Python pipelines for analytics. The IPC bridge is the architectural keystone that makes this hybrid approach practical.

---

## System Architecture Overview

### Five-Layer Architecture

| Layer | Technology | Responsibility |
|-------|-----------|---|
| **1. Entry Points** | Terminal / ATM / Batch | User-facing interfaces triggering banking operations |
| **2. Core Banking** | GnuCOBOL programs | Business logic, validation, workflow orchestration |
| **3. IPC Bridge** | Subprocess / pipes / files | Communication between COBOL and Python |
| **4. Data Pipeline** | Python 3.11+ scripts | Big data queries, analytics, ML scoring |
| **5. Data Lake** | Parquet + DuckDB | Columnar storage and analytical query engine |

### Architecture Diagram

```
    ┌─────────────────────────────────────┐
    │  Layer 1: COBOL Programs            │
    │  ├─ CUSTOMER-LOOKUP.cbl             │
    │  ├─ LOAN-PROCESS.cbl                │
    │  └─ FRAUD-CHECK.cbl                 │
    └───────────────┬─────────────────────┘
                    │ CALL SYSTEM
                    │ (fixed-width records)
    ┌───────────────▼─────────────────────┐
    │  Layer 2: IPC Bridge                │
    │  ├─ Input: customer_id, params      │
    │  ├─ Output: 145B/51B/78B records    │
    │  └─ Timeout: 5 seconds              │
    └───────────────┬─────────────────────┘
                    │
    ┌───────────────▼─────────────────────┐
    │  Layer 3: Python Analytics Scripts  │
    │  ├─ customer_360.py                 │
    │  ├─ loan_scoring.py                 │
    │  ├─ fraud_detect.py                 │
    │  └─ report_aggregator.py            │
    └───────────────┬─────────────────────┘
                    │ SQL queries
    ┌───────────────▼─────────────────────┐
    │  Layer 4: Query Engine              │
    │  ├─ DuckDB (in-process)             │
    │  ├─ Hive partitioning               │
    │  └─ Row group pruning               │
    └───────────────┬─────────────────────┘
                    │
    ┌───────────────▼─────────────────────┐
    │  Layer 5: Data Lake                 │
    │  ├─ customers.parquet (100K rows)   │
    │  ├─ loans.parquet (500K rows)       │
    │  ├─ transactions/ (10M rows)        │
    │  │  └─ date=YYYY-MM-DD/ partitions  │
    │  └─ fraud_labels.parquet (50K)      │
    └─────────────────────────────────────┘
```

### Data Flow Pattern

Every interaction follows the same fundamental pattern:

1. A trigger event occurs (teller input, ATM request, or batch job)
2. The appropriate COBOL program receives the request and validates input
3. COBOL packages parameters into a fixed-width record
4. COBOL invokes the IPC bridge (CALL "SYSTEM" with Python script name)
5. The Python script queries Parquet files through DuckDB
6. Python formats the result as a fixed-width record matching the COBOL copybook layout
7. The result is returned through the IPC bridge (stdout pipe)
8. COBOL reads the response and continues its business logic

### Design Principles

- **Separation of Concerns:** COBOL owns business logic; Python owns analytics
- **COBOL-Native Interfaces:** Fixed-width records map directly to COBOL copybooks
- **Stateless Python Scripts:** Each invocation is independent (no shared state)
- **Fail-Safe Defaults:** If Python fails, COBOL falls back to safe defaults

---

## Module Specifications

### Module 1: Customer 360° Lookup

**Business Scenario:** A bank teller queries a comprehensive 360-degree view of a customer including account balance, transaction history, and risk score.

**COBOL Program:** `cobol/CUSTOMER-LOOKUP.cbl`  
**Python Script:** `python/customer_360.py`

**Input Parameters:**
- `WS-CUSTOMER-ID` (PIC X(10)) — Customer identifier (e.g., C-00001)

**Output Record (145 bytes total):**

| Field | Start | Len | Type | Format |
|-------|-------|-----|------|--------|
| CUST-NAME | 1 | 50 | X | Left-justified, space-padded |
| ACCT-BALANCE | 51 | 12 | 9(10)V99 | Right-justified, zero-padded |
| TXN-COUNT | 63 | 8 | 9(8) | Right-justified, zero-padded |
| AVG-MONTHLY | 71 | 10 | 9(8)V99 | Right-justified, zero-padded |
| RISK-SCORE | 81 | 3 | 9(3) | 000–999 |
| LAST-TXN-DATE | 84 | 10 | X | YYYY-MM-DD format |
| RETURN-CODE | 94 | 2 | X | 00=success, 01=not found, 99=error |

**Key Operations:**
1. Query `customers.parquet` for demographic data and balance
2. Query `transactions/*.parquet` with aggregation: COUNT(*), AVG(amount), MAX(txn_date)
3. Compute risk score based on transaction frequency, average amount, and recency
4. Format all fields as fixed-width strings matching PIC clauses
5. Write single-line record to stdout

---

### Module 2: Loan Eligibility Assessment

**Business Scenario:** A customer applies for a personal loan. The system determines eligibility based on historical financial behavior from the data lake.

**COBOL Program:** `cobol/LOAN-PROCESS.cbl`  
**Python Script:** `python/loan_scoring.py`

**Input Parameters:**
- `WS-CUSTOMER-ID` (PIC X(10))
- `WS-LOAN-AMOUNT` (PIC 9(8)V99)
- `WS-LOAN-TERM` (PIC 9(3)) — months
- `WS-PURPOSE-CODE` (PIC X(4)) — HOME, AUTO, PERS, EDUC

**Output Record (51 bytes total):**

| Field | Start | Len | Type | Format |
|-------|-------|-----|------|--------|
| CREDIT-SCORE | 1 | 3 | 9(3) | 300–850 |
| ELIGIBLE | 4 | 1 | X | Y = approved, N = rejected |
| INT-RATE | 5 | 5 | 9V9(4) | Interest rate (e.g., 5.25%) |
| MAX-AMOUNT | 10 | 10 | 9(8)V99 | Maximum approvable amount |
| REJECT-REASON | 20 | 30 | X | Reason if rejected |
| RETURN-CODE | 50 | 2 | X | 00=success, 99=error |

**Eligibility Criteria:**
- Credit score ≥ 650
- Debt-to-income ratio < 0.43
- No recent defaults

**Credit Score Formula (300–850 scale):**
- Payment history: 35%
- Credit utilization: 30%
- Credit length: 15%
- New credit: 10%
- Credit mix: 10%

---

### Module 3: Real-Time Fraud Detection

**Business Scenario:** During transaction processing, every transaction is screened for fraud against the customer's historical patterns.

**COBOL Program:** `cobol/FRAUD-CHECK.cbl`  
**Python Script:** `python/fraud_detect.py`

**Input Parameters:**
- `WS-CUSTOMER-ID` (PIC X(10))
- `WS-TXN-AMOUNT` (PIC 9(8)V99)
- `WS-MERCHANT-CAT` (PIC X(4)) — MCC code
- `WS-TXN-LOCATION` (PIC X(20))
- `WS-TXN-TIMESTAMP` (PIC X(19)) — ISO 8601
- `WS-TXN-CHANNEL` (PIC X(3)) — POS, ATM, ONL, MOB

**Output Record (78 bytes total):**

| Field | Start | Len | Type | Format |
|-------|-------|-----|------|--------|
| FRAUD-RISK | 1 | 6 | X | LOW, MEDIUM, or HIGH |
| FRAUD-SCORE | 7 | 3 | 9(3) | 0–100 |
| FRAUD-FLAGS | 10 | 60 | X | Comma-separated risk indicators |
| RECOMMEND | 70 | 7 | X | APPROVE, REVIEW, or DECLINE |
| RETURN-CODE | 77 | 2 | X | 00=success, 99=error |

**Fraud Detection Checks:**
- **Amount Anomaly:** Compares against customer's mean ± 3 standard deviations
- **Geographic Anomaly:** Flags sudden location changes (e.g., Bucharest to Lagos within hours)
- **Velocity Check:** Counts transactions within last hour and 24 hours
- **Category Anomaly:** Identifies first-time merchant categories
- **Time-of-Day Analysis:** Flags transactions outside customer's normal active hours

---

## IPC Bridge Design

### Communication Mechanisms

The project implements three IPC approaches:

#### Option A: Subprocess with stdout Pipe (Implemented)

**How It Works:**
```
COBOL writes command line to file or passes as argument:
  python3 customer_360.py C-10042
Python writes fixed-width record to stdout (145 bytes)
COBOL reads from pipe and parses the record
```

**Advantages:**
- Minimal complexity
- No persistent processes
- Easy to debug
- Cross-platform compatible

**Disadvantages:**
- Process creation overhead on every call
- Not suitable for high-frequency invocations

#### Option B: Flat File Exchange

**How It Works:**
- COBOL writes request record to a request file
- Python script reads request, processes, writes response to response file
- COBOL reads response file

**Advantages:**
- Mirrors traditional COBOL I/O patterns
- Easy audit trail (files can be archived)
- Batch processing support

**Disadvantages:**
- Disk I/O overhead
- File locking complexity in concurrent scenarios

#### Option C: Named Pipes (FIFO)

**How It Works:**
- Python runs as a persistent daemon listening on UNIX named pipe
- COBOL writes request records to FIFO
- Python responds on a second FIFO

**Advantages:**
- No process creation overhead
- Persistent Python process can maintain DuckDB connections and caches
- Lowest latency

**Disadvantages:**
- Requires process management (systemd/supervisor)
- More complex error handling

### IPC Data Format Contract

All three options use the same data format: **fixed-width records defined by COBOL copybooks**.

The `python/utils/ipc_formatter.py` utility provides formatting functions:

```python
def format_pic_x(value: str, length: int) -> str:
    """Left-justify and pad with spaces."""
    return value.ljust(length)[:length]

def format_pic_9(value: float, integer_digits: int, 
                  decimal_digits: int = 0) -> str:
    """Right-justify, zero-pad numeric value."""
    scaled = int(value * (10 ** decimal_digits))
    total = integer_digits + decimal_digits
    return str(abs(scaled)).zfill(total)[:total]
```

### Error Handling Strategy

Three-tier fallback approach:

1. **Tier 1 — Python Script Failure:**  
   If Python exits with non-zero code or produces malformed output, COBOL detects via RETURN-CODE=99 and falls back to safe default response.

2. **Tier 2 — Timeout:**  
   If response is not available within 5 seconds, COBOL proceeds with default ("UNKNOWN" risk, "N" eligibility).

3. **Tier 3 — Data Integrity:**  
   Python validates all output fields against expected PIC clause lengths. Fields are padded/truncated to fit if necessary.

---

## Data Layer Design

### Why Parquet + DuckDB?

| Criterion | Choice | Reason |
|-----------|--------|--------|
| **Storage Format** | Apache Parquet | Columnar, compressed, SQL-compatible |
| **Query Engine** | DuckDB | In-memory SQL, no server setup required |
| **Server** | None (serverless) | Stateless analytics, perfect for thesis |
| **Dependencies** | Minimal | Works on Windows, macOS, Linux |
| **Data Volume** | 10M+ records | Parquet handles scale; DuckDB loads in-memory |

### Advantages

✅ No server to deploy or manage  
✅ Fast columnar queries optimized for analytics  
✅ Snappy compression built-in  
✅ Native Hive partitioning (date-based pruning)  
✅ SQL standard syntax  
✅ Cross-platform (Windows, Linux, macOS)

### Data Generation Flow

#### Step 1: Generate Customers (100K records)

**Output:** `data/customers.parquet`

| Field | Type | Distribution |
|-------|------|---|
| customer_id | String | C-00001 to C-100000 |
| name | String | Faker-generated US names |
| dob | Date | Ages 18–80 |
| city | String | US cities |
| account_open_date | Date | 1–15 years ago |
| credit_tier | String | EXCELLENT, GOOD, FAIR, POOR |
| email | String | Faker-generated emails |
| monthly_income | Float | Normal(4500, 2000) |

#### Step 2: Generate Loans (500K records)

**Output:** `data/loans.parquet`

**Key Relationship:** loans.customer_id → customers.customer_id (foreign key)

| Field | Type | Distribution |
|-------|------|---|
| loan_id | String | L-000001 to L-500000 |
| customer_id | String | References customers table |
| amount | Float | LogNormal(9.5, 0.7) ≈ $10K–$30K |
| term | Integer | 12, 24, 36, 48, 60, 84, 120 months |
| rate | Float | 3.5%–24.0% |
| status | String | ACTIVE, PAID, DEFAULT, DELINQUENT |
| purpose | String | HOME, AUTO, PERS, EDUC |
| on_time_payments | Integer | 0 to term |
| days_past_due | Integer | 0 or 1–365 days |

#### Step 3: Generate Transactions (10M records, 365 daily partitions)

**Output:** `data/transactions/date=YYYY-MM-DD/*.parquet` (27K rows per day)

**Key Relationship:** transactions.customer_id → customers.customer_id (foreign key)

**Hive Partitioning Strategy:**
```
data/transactions/
  date=2025-01-01/part-0000.parquet  (27K rows)
  date=2025-01-02/part-0000.parquet  (27K rows)
  ...
  date=2025-12-31/part-0000.parquet  (27K rows)
```

DuckDB uses **Hive partitioning** to automatically prune directories:
```sql
SELECT * FROM read_parquet('transactions/date=*/part-*.parquet', 
                           hive_partitioning=true)
WHERE customer_id = 'C-00001' AND date >= '2025-06-01'
-- DuckDB only reads: date=2025-06-01/ through date=2025-12-31/
```

| Field | Type | Distribution |
|-------|------|---|
| txn_id | String | T-00000001 to T-10000000 |
| customer_id | String | References customers table |
| amount | Float | LogNormal(5.5, 1.0) ≈ $250 typical |
| merchant | String | 1000 unique merchants |
| mcc | String | 4-digit merchant category code |
| city | String | 90% customer's home, 10% random |
| timestamp | ISO8601 | Date + time (hours ≈ Normal(14, 4)) |
| channel | String | POS (50%), ATM (20%), ONL (20%), MOB (10%) |
| date | Date | YYYY-MM-DD partition key |

#### Step 4: Generate Fraud Labels (50K records)

**Output:** `data/fraud_labels.parquet`

| Field | Type | Notes |
|-------|------|-------|
| txn_id | String | T-00000001 to T-10000000 |
| is_fraud | Boolean | True (15%), False (85%) |
| fraud_type | String | CARD_NOT_PRESENT, ACCOUNT_TAKEOVER, IDENTITY_THEFT, NONE |
| detection_method | String | How fraud was identified |

### DuckDB as the Query Engine

**Key Characteristics:**
- **Zero Infrastructure:** Embedded database (no server to install/maintain)
- **Columnar Execution:** Vectorized engine reads only needed columns
- **Parquet Native:** Reads natively with predicate pushdown and statistics-based pruning
- **SQL Interface:** Standard SQL makes code readable and maintainable

**In Python Scripts:**
```python
import duckdb

conn = duckdb.connect(':memory:')
result = conn.execute("""
    SELECT customer_id, COUNT(*) as txn_count, AVG(amount) as avg_amount
    FROM read_parquet('data/transactions/date=*/part-*.parquet', 
                      hive_partitioning=true)
    WHERE customer_id = 'C-00001'
    GROUP BY customer_id
""").fetchall()
```

---

## Technology Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **COBOL Compiler** | GnuCOBOL | 3.2+ | Compile COBOL programs |
| **Python Runtime** | Python | 3.11+ | Execute analytics scripts |
| **Query Engine** | DuckDB | 1.1+ | Analytical SQL on Parquet |
| **Data Format** | Apache Parquet | Via pyarrow | Columnar storage |
| **Data Generation** | Faker + NumPy | Latest | Synthetic data generation |
| **Testing** | pytest | Latest | Python unit tests |
| **Benchmarking** | time + matplotlib | Standard | Wall-clock measurement + charts |
| **OS** | Ubuntu 22.04+ | Latest | GnuCOBOL + named pipes support |
| **Version Control** | Git | Latest | Repository management |

### Installation Requirements

```bash
# Python dependencies
pip install duckdb pyarrow pandas numpy faker pytest

# COBOL compiler (Ubuntu/Debian)
sudo apt install gnucobol

# On Windows: Use WSL2 with Ubuntu 22.04
```

---

## Project Structure

```
cobol-bigdata/
├── CLAUDE.md                      ← Claude Code guidance
├── docs/
│   ├── architecture.md            ← This file
│   ├── implementation.md           ← Phase implementations
│   ├── progress.md                ← Status tracking
│   ├── ui.md                      ← UI documentation
│   ├── fixes.md                   ← Bug fixes
│   └── thesis.md                  ← Thesis outline & roadmap
├── cobol/
│   ├── CUSTOMER-LOOKUP.cbl
│   ├── LOAN-PROCESS.cbl
│   ├── FRAUD-CHECK.cbl
│   ├── Makefile
│   └── copybooks/
│       ├── CUSTOMER-REC.cpy       (145 bytes)
│       ├── LOAN-REC.cpy           (51 bytes)
│       └── FRAUD-REC.cpy          (78 bytes)
├── python/
│   ├── customer_360.py
│   ├── loan_scoring.py
│   ├── fraud_detect.py
│   ├── report_aggregator.py
│   ├── customer_search.py
│   ├── customer_list.py
│   ├── customer_update.py
│   ├── customer_transactions.py
│   ├── fraud_batch_analysis.py
│   └── utils/
│       ├── ipc_formatter.py
│       └── parquet_reader.py
├── data/
│   ├── generate_synthetic.py
│   ├── customers.parquet
│   ├── loans.parquet
│   ├── transactions/              (365 date partitions)
│   └── fraud_labels.parquet
├── benchmarks/
│   ├── bench_vsam_vs_parquet.py
│   └── bench_ipc_overhead.py
└── ui/
    ├── app.py
    ├── parse.py
    ├── runner.py
    └── __pycache__/
```

---

## Build & Verification

### Generate Data (First-Time Setup)

```bash
python3 data/generate_synthetic.py
# Creates: customers.parquet, loans.parquet, transactions/*, fraud_labels.parquet
```

### Compile COBOL Programs

```bash
cd cobol
make all

# Or compile individually
gnucobol -x CUSTOMER-LOOKUP.cbl -o customer-lookup
gnucobol -x LOAN-PROCESS.cbl -o loan-process
gnucobol -x FRAUD-CHECK.cbl -o fraud-check
```

### Test Python Analytics Scripts Directly

```bash
python3 python/customer_360.py C-00001
python3 python/loan_scoring.py C-00001 10000.00 36 PERS
python3 python/fraud_detect.py C-00001 500.00 5411 Bucharest 2025-01-15T14:30:00 POS
```

### Run Tests

```bash
pytest python/
```

---

## References

- **CLAUDE.md** — Claude Code session guidance
- **implementation.md** — Phase-by-phase implementation guides
- **progress.md** — Project status and checklists
- **thesis.md** — Thesis outline, benchmarking methodology, submission roadmap

