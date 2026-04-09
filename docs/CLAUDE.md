# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

This is a master's thesis project demonstrating a hybrid COBOL + Python banking system. COBOL handles business logic and orchestration; Python handles analytics and scoring. Communication uses an IPC bridge with fixed-width records that map byte-for-byte to COBOL copybook layouts.

**Status:** ✅ All implementation phases complete (7 phases, ~2,500 lines of code).

## Technology Stack

- **COBOL compiler:** GnuCOBOL 3.2+ (`sudo apt install gnucobol` on Ubuntu)
- **Python:** 3.11+ (required for DuckDB compatibility)
- **Query engine:** DuckDB 1.1+ (`pip install duckdb`)
- **Data format:** Apache Parquet via pyarrow (`pip install pyarrow`)
- **Data generation:** Faker + NumPy
- **Testing:** pytest
- **OS:** Linux/Ubuntu required (GnuCOBOL + named pipes)

## Build & Run

```bash
# Compile all COBOL programs (requires cobol/Makefile)
make all

# Compile and run a single module
make run-customer-lookup CUSTOMER_ID=C-10042

# Run benchmarks
make benchmark

# Generate synthetic data (must be run first)
python3 data/generate_synthetic.py

# Run Python scripts directly
python3 python/customer_360.py <customer_id>
python3 python/loan_scoring.py <customer_id> <amount> <term> <purpose_code>
python3 python/fraud_detect.py <customer_id> <amount> <mcc> <location> <timestamp> <channel>

# Run tests
pytest python/
```

## Architecture

### Data Flow

Every operation follows: Trigger → COBOL validates input → COBOL invokes Python via `CALL "SYSTEM"` → Python queries Parquet via DuckDB → Python writes fixed-width record to stdout → COBOL reads response into WORKING-STORAGE.

### IPC Contract (CRITICAL)

Python output must be **byte-perfect** fixed-width records matching COBOL copybooks. The utility `python/utils/ipc_formatter.py` provides:
- `format_pic_x(value, length)` — left-justified, space-padded alphanumeric
- `format_pic_9(value, integer_digits, decimal_digits)` — right-justified, zero-padded numeric

**Customer 360 response record — 145 bytes total:**

| Field | Start | Len | Format |
|---|---|---|---|
| CUST-NAME | 1 | 50 | PIC X(50), left-justified |
| ACCT-BALANCE | 51 | 12 | PIC 9(10)V99, zero-padded |
| TXN-COUNT | 63 | 8 | PIC 9(8), zero-padded |
| AVG-MONTHLY | 71 | 10 | PIC 9(8)V99, zero-padded |
| RISK-SCORE | 81 | 3 | PIC 9(3), 000–999 |
| LAST-TXN-DATE | 84 | 10 | YYYY-MM-DD |
| RETURN-CODE | 94 | 2 | 00=success, 01=not found, 99=error |

### Modules

- **CUSTOMER-LOOKUP.cbl** + **customer_360.py** — 360° customer view; queries `customers.parquet` and `transactions/*.parquet`
- **LOAN-PROCESS.cbl** + **loan_scoring.py** — loan eligibility; queries `loans.parquet`; credit score formula: payment_history(35%) + credit_utilization(30%) + credit_length(15%) + new_credit(10%) + credit_mix(10%), normalized to 300–850; eligible if score ≥ 650 and DTI < 0.43 and no recent defaults
- **FRAUD-CHECK.cbl** + **fraud_detect.py** — real-time fraud scoring; checks amount anomaly (3σ), geo anomaly, velocity, category anomaly, time-of-day; returns LOW/MEDIUM/HIGH risk + APPROVE/REVIEW/DECLINE

### Data Layout

```
data/
  customers.parquet        # 100K records
  loans.parquet            # 500K records
  transactions/            # 10M+ records, partitioned by date
    date=YYYY-MM-DD/part-0000.parquet
```

Transactions are date-partitioned for DuckDB predicate pushdown. Python scripts use in-process DuckDB (no server needed) and must remain **stateless**.

### Error Handling

COBOL uses three-tier fallback: (1) non-zero Python exit code → RETURN-CODE=99, (2) 5-second timeout → safe defaults (`FLAG-RISK="UNKNOWN"`, `LOAN-ELIGIBLE="N"`), (3) Python validates field widths before output and pads/truncates to fit PIC clause.

### Benchmarks

- `bench_vsam_vs_parquet.py` — compares COBOL VSAM sequential scan vs. COBOL+Python+DuckDB/Parquet at scales 10K–10M records
- `bench_ipc_overhead.py` — measures round-trip latency (mean, P50, P95, P99) for three IPC options: subprocess stdout, flat file exchange, named pipes (FIFO)
