# BankCore Analytics: Modernizing COBOL with Big Data Pipelines

## Project Overview

**BankCore Analytics** is a hybrid enterprise system that modernizes legacy COBOL banking applications by connecting them to a contemporary big data analytics platform. The system architecture spans **five technology layers** — legacy COBOL programs, a Python analytics engine, an in-process DuckDB data layer, and dual UI frontends (Streamlit and React) — demonstrating how traditional mainframe business logic can evolve without replacement.

The system analyzes **100,000 customer records**, processes **10,000,000 transactions**, and performs real-time **customer profiling, loan eligibility assessment, and fraud risk detection** using algorithmic scoring across multiple factors (risk profile, credit history, transaction anomalies).

## Research Context

This project is a master's thesis demonstrating:

1. **Legacy system modernization without code replacement** — COBOL business logic remains authoritative while analytics scale to petabyte-range data
2. **Fixed-width IPC bridge design** — Secure, stateless, language-agnostic communication between COBOL and Python
3. **In-process analytics architecture** — DuckDB eliminates database server complexity, enabling Parquet-scale performance on laptop hardware
4. **Dual UI paradigm** — Streamlit for rapid analytics iteration, React for production user interfaces

---

## System Architecture (5 Layers)

```
┌─────────────────────────────────────────────────────────────────┐
│                     5. User Interface Layer                      │
│         Streamlit (analytics) + React (production)              │
├─────────────────────────────────────────────────────────────────┤
│                     4. Application Layer                         │
│         Python analytics scripts + FastAPI REST API            │
├─────────────────────────────────────────────────────────────────┤
│                  3. IPC Bridge Layer (Protocol)                 │
│    Fixed-width records (145/78/51 bytes), subprocess I/O      │
├─────────────────────────────────────────────────────────────────┤
│                   2. Data Access Layer                          │
│      DuckDB (in-process) + Parquet (10M transactions)          │
├─────────────────────────────────────────────────────────────────┤
│                  1. Business Logic Layer                        │
│         GnuCOBOL programs (CUSTOMER-LOOKUP, FRAUD-CHECK, etc.)  │
└─────────────────────────────────────────────────────────────────┘
```

### Layer 1: COBOL Business Logic
- **4 programs** (CUSTOMER-LOOKUP, LOAN-PROCESS, FRAUD-CHECK, CUSTOMER-UPDATE) implementing core banking rules
- **3 copybooks** defining IPC contracts in strict byte layouts
- Runs via `cobol/` directory, compiled with GnuCOBOL 3.2+

### Layer 2: Data Access
- **DuckDB** (in-process, no server) reading Parquet files from disk
- **4 datasets**: customers (100K), loans (500K), transactions (10M Hive-partitioned), fraud_labels (50K)
- Stateless per-query model — each Python script creates and destroys its own connection

### Layer 3: IPC Bridge
- **Fixed-width record exchange** (145/78/51 bytes) via copybook overlays
- **Three transport mechanisms**:
  - COBOL calls Python via `CALL "SYSTEM"` + temp file redirect (CUSTOMER-LOOKUP, LOAN-PROCESS, FRAUD-CHECK)
  - Python calls COBOL via subprocess + file argument (CUSTOMER-UPDATE)
  - Python calls Python via subprocess + pipe (UI layer + reporting)
- Numeric encoding: PIC 9 formatted without decimal point; parse divides by 10^decimal_places

### Layer 4: Analytics & API
- **9 Python analytics scripts** implementing proprietary scoring algorithms (risk, credit, fraud)
- **FastAPI REST API** (wrappers.py) providing simplified, direct-DuckDB implementations
- **Key architectural note**: The FastAPI wrappers do NOT call the Python scripts — they re-implement the analytics directly with DuckDB for web service performance

### Layer 5: User Interface
- **Streamlit UI** (`ui/app.py`) — 1,300-line analytical dashboard with full algorithm access
- **React+TypeScript UI** (`frontend/`) — Production-grade interface with 4 pages, SearchWidget customer selection, pre-selected customer navigation pattern

---

## Quick Start

### 1. Install Dependencies
```bash
cd cobol-bigdata

# Backend dependencies
cd backend && pip install -r requirements.txt && cd ..

# Frontend dependencies
cd frontend && npm install && cd ..
```

### 2. Generate Synthetic Data (optional, included)
```bash
cd data && python generate_synthetic.py && cd ..
```

### 3. Run Backend (FastAPI, port 8000)
```bash
cd backend && python main.py
```

### 4. Run Frontend (React, port 3000)
```bash
cd frontend && npm run dev
```

Open `http://localhost:3000` in your browser. System is ready for analytics.

```bash
streamlit run ui/app.py
# Opens in browser at http://localhost:8501
```

### 4. Run Python Scripts Directly

```bash
python3 python/customer_360.py C-00001
python3 python/loan_scoring.py C-00001 15000.00 36 PERS
python3 python/fraud_detect.py C-00001 500.00 5411 Bucharest 2025-01-15T14:30:00 POS
```

### 5. Run Benchmarks

```bash
python3 benchmarks/bench_vsam_vs_parquet.py   # VSAM vs Parquet query performance
python3 benchmarks/bench_ipc_overhead.py      # IPC mechanism latency comparison
```

---

## System Architecture

```
User / Teller / ATM
        │
        ▼
┌────────────────────┐
│  COBOL Programs    │  Business logic, validation, workflow
│  CUSTOMER-LOOKUP   │  orchestration
│  LOAN-PROCESS      │
│  FRAUD-CHECK       │
└────────┬───────────┘
         │  CALL "SYSTEM" (IPC bridge, fixed-width records)
         ▼
┌────────────────────┐
│  Python Scripts    │  Analytics, scoring, ML-style algorithms
│  customer_360.py   │
│  loan_scoring.py   │
│  fraud_detect.py   │
└────────┬───────────┘
         │  SQL queries
         ▼
┌────────────────────┐
│  DuckDB (in-proc.) │  In-memory analytical SQL engine
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│  Apache Parquet    │  Columnar data lake (100K–10M records)
│  (date-partitioned)│
└────────────────────┘
```

All three IPC mechanisms are implemented and benchmarked:
- **Subprocess + stdout pipe** — simplest, used in production
- **Flat file exchange** — COBOL-native I/O pattern
- **Named pipes (FIFO)** — lowest latency, Linux-only

---

## Project Structure

```
cobol-bigdata/
├── cobol/
│   ├── CUSTOMER-LOOKUP.cbl       Business logic: customer 360 query
│   ├── LOAN-PROCESS.cbl          Business logic: loan eligibility
│   ├── FRAUD-CHECK.cbl           Business logic: fraud assessment
│   ├── Makefile                  Compilation & run targets
│   └── copybooks/
│       ├── CUSTOMER-REC.cpy      145-byte IPC record
│       ├── LOAN-REC.cpy          51-byte IPC record
│       └── FRAUD-REC.cpy         78-byte IPC record
├── python/
│   ├── customer_360.py           Analytics: customer profile
│   ├── loan_scoring.py           Analytics: credit scoring
│   ├── fraud_detect.py           Analytics: fraud risk scoring
│   ├── report_aggregator.py      Batch: multi-customer reports
│   ├── customer_search.py        UI: search by last name
│   ├── customer_list.py          UI: paginated customer list
│   ├── customer_update.py        UI: update customer record
│   ├── customer_transactions.py  UI: fetch all transactions
│   ├── fraud_batch_analysis.py   UI: batch fraud scoring
│   └── utils/
│       ├── ipc_formatter.py      format_pic_x, format_pic_9
│       └── parquet_reader.py     DuckDB query wrappers
├── data/
│   ├── generate_synthetic.py     Generates all Parquet test data
│   ├── customers.parquet         100K customer records
│   ├── loans.parquet             500K loan records
│   ├── transactions/             10M transactions, date-partitioned
│   └── fraud_labels.parquet      50K ground-truth fraud labels
├── benchmarks/
│   ├── bench_vsam_vs_parquet.py  Performance comparison (10K–10M records)
│   └── bench_ipc_overhead.py     IPC latency (subprocess/file/pipe)
├── ui/
│   ├── app.py                    Streamlit analytics dashboard
│   ├── parse.py                  Output parsing utilities (8 parsers)
│   └── runner.py                 Subprocess execution wrapper
└── docs/
    ├── INDEX.md                  Documentation index (start here)
    ├── architecture.md           System design & IPC contracts
    ├── data.md                   Data layer & Parquet schemas
    ├── implementation.md         Phase & feature implementation guides
    ├── progress.md               Project status & verification steps
    ├── ui.md                     UI design, user guide, developer guide
    ├── fixes.md                  Bug fixes & iterative improvements
    └── thesis.md                 Thesis outline & writing roadmap
```

---

## IPC Contract (Critical)

Python output must be **byte-perfect** fixed-width records matching COBOL copybooks.

| Module | Output Size | Fields |
|--------|------------|--------|
| customer_360.py | **145 bytes** | name(50) + balance(12) + txn_count(8) + avg_monthly(10) + risk_score(3) + last_txn_date(10) + return_code(2) |
| loan_scoring.py | **51 bytes** | credit_score(3) + eligible(1) + int_rate(5) + max_amount(10) + reject_reason(30) + return_code(2) |
| fraud_detect.py | **78 bytes** | fraud_risk(6) + fraud_score(3) + flags(60) + recommendation(7) + return_code(2) |

Return codes: `00` = success, `01` = not found, `99` = error

Formatting utilities in `python/utils/ipc_formatter.py`:
- `format_pic_x(value, length)` — left-justified, space-padded alphanumeric
- `format_pic_9(value, int_digits, dec_digits)` — right-justified, zero-padded numeric

---

## Analytics Dashboard

The Streamlit app (`ui/app.py`) provides four pages:

| Page | Capability |
|------|-----------|
| **Customer 360** | Balance, risk score, transaction history for any customer |
| **Loan Assessment** | Credit score (300–850), eligibility, interest rate |
| **Fraud Detection** | Searchable transaction list, batch fraud scoring, risk report |
| **Customer Management** | Search, view, and update customer records |

---

## Data Layer

| Dataset | Records | Size | Notes |
|---------|---------|------|-------|
| customers.parquet | 100,000 | ~50MB | Demographics, credit tier, income |
| loans.parquet | 500,000 | ~150MB | 5 loans per customer on avg |
| transactions/ | 10,000,000 | ~1GB | 365 daily partitions, date-prunable |
| fraud_labels.parquet | 50,000 | ~10MB | Ground-truth labels (15% fraud rate) |

Transactions are Hive-partitioned by date (`date=YYYY-MM-DD/`), enabling DuckDB to automatically skip irrelevant partitions on date-range queries.

---

## Research Questions

This project provides empirical answers to three thesis research questions:

1. **Can COBOL be extended with Python analytics via IPC without modifying business logic?**
   Yes — demonstrated by the complete working implementation.

2. **At what data volume does hybrid COBOL-Python-Parquet outperform COBOL-only VSAM?**
   Empirical crossover measured at approximately 1 million records (see `bench_vsam_vs_parquet.py`).

3. **What are the latency trade-offs between IPC mechanisms?**
   Named pipes (~12ms) < Flat file (~30ms) < Subprocess (~50ms) for P50 latency (see `bench_ipc_overhead.py`).

---

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| COBOL compiler | GnuCOBOL | 3.2+ |
| Python runtime | Python | 3.11+ |
| Query engine | DuckDB | 1.1+ |
| Data format | Apache Parquet (pyarrow) | Latest |
| Data generation | Faker + NumPy | Latest |
| UI framework | Streamlit | Latest |
| Testing | pytest | Latest |

---

## Documentation

All documentation is in `docs/`. Start with [`INDEX.md`](INDEX.md) for navigation.

| File | Contents |
|------|----------|
| [`INDEX.md`](INDEX.md) | Master navigation index |
| [`architecture.md`](architecture.md) | System design, modules, IPC bridge |
| [`data.md`](data.md) | Data layer, Parquet schemas, DuckDB queries |
| [`implementation.md`](implementation.md) | Phase-by-phase implementation guides |
| [`progress.md`](progress.md) | Project status, verification commands |
| [`ui.md`](ui.md) | UI design, user guide, developer guide |
| [`fixes.md`](fixes.md) | Bug fixes and iterative improvements |
| [`thesis.md`](thesis.md) | Thesis outline, benchmarks, writing roadmap |
