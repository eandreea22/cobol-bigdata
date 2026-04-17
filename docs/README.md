# Modernizing COBOL with Big Data Pipelines

**Master's Thesis Project — Hybrid COBOL + Python Banking System**  
**Status:** ✅ Complete | All 8 phases implemented | Streamlit UI live

---

## Overview

This project demonstrates how legacy COBOL banking systems can be extended with modern Python-based big data pipelines — without rewriting the existing business logic.

The core innovation is an **Inter-Process Communication (IPC) bridge** that lets COBOL programs delegate analytical operations to Python scripts. Python queries a modern data lake built on Apache Parquet and DuckDB, enabling real-time analytics that COBOL was never designed to handle.

Three banking workflows are simulated:
- **Customer 360°** — comprehensive customer profile from 10M+ transaction records
- **Loan Eligibility** — credit scoring and approval decision
- **Fraud Detection** — real-time risk assessment with batch analysis

---

## Quick Start

### Prerequisites

```bash
# Python dependencies
pip install streamlit duckdb pyarrow pandas numpy faker pytest

# COBOL compiler (Ubuntu/Debian)
sudo apt install gnucobol

# Windows: Use WSL2 with Ubuntu 22.04
```

### 1. Generate Data

```bash
python3 data/generate_synthetic.py
# Creates: customers.parquet (100K), loans.parquet (500K),
#          transactions/ (10M, 365 partitions), fraud_labels.parquet (50K)
```

### 2. Compile COBOL Programs

```bash
cd cobol && make all
```

### 3. Run the Analytics Dashboard

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
