# Project Progress & Status

**Last Updated:** 2026-04-16  
**Status:** ✅ ALL IMPLEMENTATION PHASES COMPLETE

---

## Overall Status Summary

| Phase | Component | Lines | Status |
|-------|-----------|-------|--------|
| 1a | python/utils/ipc_formatter.py | 67 | ✅ Complete |
| 1b | python/utils/parquet_reader.py | 227 | ✅ Complete |
| 2 | data/generate_synthetic.py | 225 | ✅ Complete |
| 3a | cobol/copybooks/CUSTOMER-REC.cpy | 36 | ✅ Complete |
| 3b | cobol/copybooks/LOAN-REC.cpy | 32 | ✅ Complete |
| 3c | cobol/copybooks/FRAUD-REC.cpy | 28 | ✅ Complete |
| 4a | python/customer_360.py | 163 | ✅ Complete |
| 4b | python/loan_scoring.py | 201 | ✅ Complete |
| 4c | python/fraud_detect.py | 163 | ✅ Complete |
| 4d | python/report_aggregator.py | 225 | ✅ Complete |
| 5a | cobol/CUSTOMER-LOOKUP.cbl | 142 | ✅ Complete |
| 5b | cobol/LOAN-PROCESS.cbl | 146 | ✅ Complete |
| 5c | cobol/FRAUD-CHECK.cbl | 156 | ✅ Complete |
| 6 | cobol/Makefile | 74 | ✅ Complete |
| 7a | benchmarks/bench_vsam_vs_parquet.py | 196 | ✅ Complete |
| 7b | benchmarks/bench_ipc_overhead.py | 263 | ✅ Complete |
| 8a | ui/parse.py | 540+ | ✅ Complete |
| 8b | ui/runner.py | 70 | ✅ Complete |
| 8c | ui/app.py | 1000+ | ✅ Complete |
| F1 | Feature: Customer Management | — | ✅ Complete |
| F2 | Feature: Fraud Detection Enhancement | — | ✅ Complete |

**Total LOC:** ~3,850 lines of implementation code

---

## Phase-by-Phase Breakdown

---

### ✅ Phase 1a: Foundation — IPC Formatter

**File:** `python/utils/ipc_formatter.py` (67 lines)  
**Purpose:** Format Python data into COBOL-compatible fixed-width strings  
**Status:** ✅ Complete, all functions tested

**Functions Implemented:**

```python
format_pic_x(value: str, length: int) -> str
# Left-justify string, space-pad to exact length
# Example: format_pic_x("Smith", 50) → "Smith" + " " * 45

format_pic_9(value: float, integer_digits: int, decimal_digits: int = 0) -> str
# Right-justify numeric, zero-pad, no decimal point in output
# Example: format_pic_9(1234.56, 10, 2) → "000000123456"
# Used for PIC 9(10)V99 fields
```

**Key Implementation Notes:**
- `format_pic_x` uses `str.ljust(length)[:length]` for truncation safety
- `format_pic_9` scales the value by `10^decimal_digits` before zero-padding (no decimal point stored)
- Both functions guarantee output is **exactly** `length` characters (critical for COBOL compatibility)

**Verification:**
```bash
python3 -c "from python.utils.ipc_formatter import format_pic_x, format_pic_9; \
            assert format_pic_9(1234.56, 10, 2) == '000000123456'; \
            assert len(format_pic_x('Smith', 50)) == 50; \
            print('✓ IPC formatter OK')"
```

---

### ✅ Phase 1b: Foundation — Parquet Reader

**File:** `python/utils/parquet_reader.py` (227 lines)  
**Purpose:** DuckDB connection and common query wrapper for all analytics scripts  
**Status:** ✅ Complete

**Functions Implemented:**

| Function | Purpose | Returns |
|----------|---------|---------|
| `get_connection()` | Create in-memory DuckDB instance | `duckdb.DuckDBPyConnection` |
| `query_customer(conn, customer_id)` | Fetch single customer record from customers.parquet | `Dict[str, Any]` or None |
| `query_transactions_agg(conn, customer_id)` | Compute transaction stats and aggregates for scoring | `Dict[str, Any]` |
| `query_loans(conn, customer_id)` | Fetch all loans for a customer from loans.parquet | `List[Dict[str, Any]]` |
| `query_fraud_labels(conn, txn_id)` | Lookup fraud label for a specific transaction | `bool` or None |

**Transaction Aggregate Fields Returned by `query_transactions_agg`:**
- `txn_count` — Total lifetime transactions
- `avg_amount` — Mean transaction amount
- `std_amount` — Standard deviation of transaction amounts (for anomaly scoring)
- `max_amount` — Largest single transaction
- `last_txn_date` — Date of most recent transaction
- `home_city` — Customer's most-frequent transaction city
- `avg_monthly_spend` — Mean monthly spending over last 12 months
- `txn_velocity_24h` — Transactions in last 24 hours
- `txn_velocity_1h` — Transactions in last hour

**Key Implementation Notes:**
- All functions receive the `conn` parameter (does not create its own connection)
- `query_transactions_agg` uses Hive partitioning for date-based pruning
- Error handling: returns `None` when no data found; raises exception on query error
- All data paths computed relative to script location using `pathlib.Path`

---

### ✅ Phase 2: Synthetic Data Generation

**File:** `data/generate_synthetic.py` (225 lines)  
**Purpose:** Create all Parquet test data with realistic banking distributions  
**Status:** ✅ Complete, reproducible with seed=42

**Generated Datasets:**

| Dataset | Records | File Size | Seed |
|---------|---------|-----------|------|
| customers.parquet | 100,000 | ~50MB | Faker(seed=42) |
| loans.parquet | 500,000 | ~150MB | rng=default_rng(42) |
| transactions/ | 10,000,000 | ~1GB | rng=default_rng(42) |
| fraud_labels.parquet | 50,000 | ~10MB | rng=default_rng(42) |

**Distribution Choices (with rationale):**
- `monthly_income`: Normal(4500, 2000) — reflects US median household income distribution
- `loan_amount`: LogNormal(9.5, 0.7) — right-skewed, realistic for personal loans
- `txn_amount`: LogNormal(5.5, 1.0) — models typical daily transactions ($250 avg)
- `fraud_rate`: 15% — higher than real (0.1–1%) to produce enough positive examples for benchmarking
- `geo_anomaly`: 10% — one-in-ten transactions has a random city (fraud signal injection)
- `channel_dist`: POS (50%), ATM (20%), ONL (20%), MOB (10%) — typical modern bank distribution

**Key Implementation Notes:**
- Day-by-day transaction loop (365 iterations) instead of bulk generation to avoid RAM exhaustion (10M rows would require ~12GB at once)
- `Faker(seed=42)` ensures reproducible names, cities, emails
- `numpy.default_rng(42)` ensures reproducible numeric distributions
- Parquet files use Snappy compression (fast, moderate compression ratio)
- Transaction partitions: `data/transactions/date=YYYY-MM-DD/part-0000.parquet`

**Run Command:**
```bash
python3 data/generate_synthetic.py
# Takes ~5–10 minutes
# Expected output: progress bar per day partition (365 iterations)
```

---

### ✅ Phase 3: COBOL Copybooks

**Files:** `cobol/copybooks/` (3 files, 96 total lines)  
**Purpose:** Fixed-width record definitions that COBOL uses to map Python script output  
**Status:** ✅ Complete, all compile with zero syntax errors

#### CUSTOMER-REC.cpy (36 lines, 145 bytes)

```cobol
01 CUSTOMER-RESPONSE.
   05 CUST-NAME-RAW       PIC X(50).     *> Bytes 1–50
   05 CUST-BALANCE-RAW    PIC X(12).     *> Bytes 51–62
   05 CUST-TXN-COUNT-RAW  PIC X(8).      *> Bytes 63–70
   05 CUST-AVG-MONTHLY-RAW PIC X(10).   *> Bytes 71–80
   05 CUST-RISK-SCORE-RAW PIC X(3).     *> Bytes 81–83
   05 CUST-LAST-TXN-RAW   PIC X(10).    *> Bytes 84–93
   05 CUST-RETURN-CODE    PIC X(2).     *> Bytes 94–95
```

Pattern: **REDEFINES** overlay — raw PIC X for parsing, then numeric REDEFINES for computation:
```cobol
   05 CUST-BALANCE-REDEF REDEFINES CUST-BALANCE-RAW PIC 9(10)V99.
```

Use `FUNCTION NUMVAL(CUST-BALANCE-RAW)` to convert string to numeric in COBOL.

#### LOAN-REC.cpy (32 lines, 51 bytes)

| Field | Bytes | Format |
|-------|-------|--------|
| CREDIT-SCORE | 1–3 | 9(3), 300–850 |
| ELIGIBLE | 4 | X(1), Y or N |
| INT-RATE | 5–9 | 9V9(4), 5 chars total |
| MAX-AMOUNT | 10–19 | 9(8)V99, 10 chars |
| REJECT-REASON | 20–49 | X(30) |
| RETURN-CODE | 50–51 | 99 |

#### FRAUD-REC.cpy (28 lines, 78 bytes)

| Field | Bytes | Format |
|-------|-------|--------|
| FRAUD-RISK | 1–6 | X(6), e.g. "HIGH  " |
| FRAUD-SCORE | 7–9 | 9(3), 0–100 |
| FRAUD-FLAGS | 10–69 | X(60), comma-separated |
| RECOMMEND | 70–76 | X(7), e.g. "APPROVE" |
| RETURN-CODE | 77–78 | 99 |

**Verification:**
```bash
cd cobol && cobc -fsyntax-only copybooks/CUSTOMER-REC.cpy copybooks/LOAN-REC.cpy copybooks/FRAUD-REC.cpy
# Expected: No output (zero errors)
```

---

### ✅ Phase 4: Python Analytics Scripts

**Files:** `python/*.py` (4 scripts, 752 total lines)  
**Status:** ✅ All 4 scripts complete and tested

---

#### ✅ Phase 4a: customer_360.py (163 lines)

**Purpose:** Customer 360° lookup — returns name, balance, txn stats, risk score  
**Invocation:** `python3 python/customer_360.py <customer_id>`  
**Output:** 145-byte fixed-width record to stdout

**Algorithm:**
1. Parse `customer_id` from `sys.argv[1].strip()`
2. Call `query_customer(conn, customer_id)` → demographic data, balance
3. Call `query_transactions_agg(conn, customer_id)` → txn_count, avg_monthly, last_txn_date
4. Compute **risk score** (0–999):
   - Frequency component (0–300): `min(300, txn_count / 10)` — more transactions = higher score
   - Amount component (0–400): `min(400, avg_amount / 50)` — higher avg = higher score
   - Recency component (0–300): Score decreases as `last_txn_date` gets older
5. Format with `ipc_formatter.py` → exactly 145 bytes
6. Print to stdout + `\n`

**Return Codes:**
- `00` — Success
- `01` — Customer not found (no record in customers.parquet)
- `99` — Unhandled exception (prints error to stderr)

**Verification:**
```bash
python3 python/customer_360.py C-00001 | wc -c      # Must be 146 (145 + \n)
python3 python/customer_360.py NOTEXIST | head -c 2  # Should output "01"
```

---

#### ✅ Phase 4b: loan_scoring.py (201 lines)

**Purpose:** Loan eligibility assessment with credit score computation  
**Invocation:** `python3 python/loan_scoring.py <customer_id> <amount> <term_months> <purpose_code>`  
**Output:** 51-byte fixed-width record to stdout

**Algorithm:**
1. Parse and validate all 4 arguments
2. Call `query_customer()` and `query_loans()` from parquet_reader
3. Compute **Credit Score** (300–850):
   - Payment history (35%): `(on_time_payments / total_payments)` ratio across all loans
   - Credit utilization (30%): `outstanding_balance / credit_limit`
   - Credit length (15%): `account_age_years / 15` (max 15 years)
   - New credit (10%): Penalizes recent loan applications
   - Credit mix (10%): Rewards variety of loan types
   - Combine, normalize to 300–850 range
4. Compute **Debt-to-Income ratio**: `sum(active_loan_payments) / monthly_income`
5. **Eligibility decision**: `score >= 650 AND dti < 0.43 AND no_recent_defaults`
6. **Interest rate**: Base rate + tier premium (score tier: 300–499=POOR, 500–649=FAIR, 650–749=GOOD, 750+=EXCELLENT)
7. Format with `ipc_formatter.py` → exactly 51 bytes

**Return Codes:**
- `00` — Success (eligible or ineligible, with reason)
- `99` — System error

**Verification:**
```bash
python3 python/loan_scoring.py C-00001 15000 36 PERS | wc -c  # Must be 52
python3 python/loan_scoring.py C-00001 15000 36 PERS | cut -c4  # Should be Y or N
```

---

#### ✅ Phase 4c: fraud_detect.py (163 lines)

**Purpose:** Real-time fraud risk assessment for a single transaction  
**Invocation:** `python3 python/fraud_detect.py <customer_id> <amount> <mcc> <location> <timestamp> <channel>`  
**Output:** 78-byte fixed-width record to stdout

**Algorithm (Additive Rule-Based Scoring):**

| Check | Max Score | Logic |
|-------|----------|-------|
| Amount anomaly | 35 | `amount > mean + 3*std` → 35; `amount > mean + 2*std` → 20; else 0 |
| Geographic anomaly | 25 | `location != home_city` → 25; else 0 |
| Velocity (1h) | 20 | `>= 5 txns/hour` → 20; `>= 3 txns/hour` → 12; else 0 |
| Velocity (24h) | 10 | `>= 20 txns/day` → 10; `>= 10 txns/day` → 6; else 0 |
| Category anomaly | 15 | Unknown MCC → 15; rare MCC (< 2%) → 8; else 0 |
| Time-of-day | 5 | `00:00–05:59` → 5; else 0 |
| **Total max** | **110** | Capped at 100 |

**Risk Classification:**
- 0–39 → **LOW** → APPROVE
- 40–69 → **MEDIUM** → REVIEW
- 70–100 → **HIGH** → DECLINE

**Return Codes:**
- `00` — Success
- `99` — System error

**Verification:**
```bash
python3 python/fraud_detect.py C-00001 500 5411 Bucharest "2025-01-15T14:30:00" POS | wc -c  # Must be 79
python3 python/fraud_detect.py C-00001 99999 0000 Lagos "2025-01-15T02:00:00" ATM | cut -c1-6  # Should be HIGH
```

---

#### ✅ Phase 4d: report_aggregator.py (225 lines)

**Purpose:** Batch reporting — processes multiple customers and aggregates analytics results  
**Invocation:** `python3 python/report_aggregator.py [--input customers.csv] [--output report.csv]`  
**Output:** CSV report with combined analytics for each customer

**Operations:**
1. Read list of customer IDs from input CSV (or default all customers)
2. For each customer, invoke all three analytics scripts
3. Collect all results (credit score, risk score, fraud risk)
4. Write aggregated CSV: `customer_id, name, balance, risk_score, credit_score, eligible, fraud_risk`
5. Compute summary statistics across all customers

**Key Design Decisions:**
- Subprocess approach (not direct function calls) to match real IPC pattern
- Handles errors per-customer (one failure doesn't stop the batch)
- Progress bar output for long-running batches
- Output CSV suitable for thesis results tables

---

### ✅ Phase 5: COBOL Programs

**Files:** `cobol/*.cbl` (3 programs, 444 total lines)  
**Status:** ✅ All 3 compile and run correctly on GnuCOBOL 3.2+

**IPC Pattern Used (Same for All Programs):**

```cobol
*> 1. Build Python command
MOVE "python3 python/customer_360.py " TO WS-COMMAND
STRING WS-COMMAND DELIMITED SIZE
       WS-CUSTOMER-ID DELIMITED SPACE
       INTO WS-FULL-COMMAND

*> 2. Execute with timeout (Linux: 'timeout 5', Windows: direct)
STRING "timeout 5 " DELIMITED SIZE
       WS-FULL-COMMAND DELIMITED SIZE
       INTO WS-TIMEOUT-COMMAND

*> 3. Execute Python script
CALL "SYSTEM" USING WS-TIMEOUT-COMMAND

*> 4. Read response from file
OPEN INPUT RESPONSE-FILE
READ RESPONSE-FILE INTO WS-RESPONSE-REC
CLOSE RESPONSE-FILE

*> 5. Parse return code
MOVE CUST-RETURN-CODE TO WS-RC
IF WS-RC = "00"
    *> Process success
ELSE
    *> Handle error with safe defaults
END-IF
```

---

#### ✅ Phase 5a: CUSTOMER-LOOKUP.cbl (142 lines)

**Copybook:** CUSTOMER-REC.cpy (145 bytes)  
**Fields parsed:** name, balance, txn_count, avg_monthly, risk_score, last_txn_date  
**Display:** Formatted screen with all fields, risk level indicator, colorized risk badge

**Safe Defaults on Error:**
- Name → "UNKNOWN"
- Balance → 0
- Txn Count → 0
- Risk Score → 999 (highest risk — fail safe)

**Verified:**
```bash
cd cobol && make run-customer-lookup CUSTOMER_ID=C-00001
# Expected: display with real customer data, balance, risk score
```

---

#### ✅ Phase 5b: LOAN-PROCESS.cbl (146 lines)

**Copybook:** LOAN-REC.cpy (51 bytes)  
**Input Fields:** customer_id, loan_amount (PIC 9(8)V99), term_months (PIC 9(3)), purpose_code (PIC X(4))  
**Fields parsed:** credit_score, eligible (Y/N), int_rate, max_amount, reject_reason  
**Display:** Decision display with credit score, eligibility badge (APPROVED/DENIED), interest rate or rejection reason

**Input Validation (COBOL-side):**
- `loan_amount > 0` — must be positive
- `term_months IN (12, 24, 36, 48, 60, 84, 120)` — valid terms only
- `purpose_code IN ('HOME', 'AUTO', 'PERS', 'EDUC')` — valid purpose codes

**Safe Defaults on Error:**
- Eligible → "N" (deny on error — safe default)
- Credit Score → 300 (minimum)
- Reject Reason → "SYSTEM ERROR"

**Verified:**
```bash
make run-loan-process CUSTOMER_ID=C-00001 AMOUNT=15000 TERM=36 PURPOSE=PERS
```

---

#### ✅ Phase 5c: FRAUD-CHECK.cbl (156 lines)

**Copybook:** FRAUD-REC.cpy (78 bytes)  
**Input Fields:** customer_id, amount, mcc (PIC X(4)), location (PIC X(20)), timestamp (PIC X(19)), channel (PIC X(3))  
**Fields parsed:** fraud_risk, fraud_score, fraud_flags, recommendation  
**Display:** Risk assessment with score, badge (LOW/MEDIUM/HIGH), flags list, recommendation action

**Input Validation (COBOL-side):**
- `amount > 0`
- `channel IN ('POS', 'ATM', 'ONL', 'MOB')`
- `timestamp` must be in format `YYYY-MM-DDTHH:MM:SS` (validated via INSPECT)

**Safe Defaults on Error:**
- Fraud Risk → "UNKNOWN" (not in {LOW, MEDIUM, HIGH})
- Fraud Score → 0
- Recommendation → "REVIEW" (conservative — review unknown cases)

**Verified:**
```bash
make run-fraud-check CUSTOMER_ID=C-00001 AMOUNT=500 MCC=5411 LOCATION=Bucharest TIMESTAMP="2025-01-15T14:30:00" CHANNEL=POS
```

---

### ✅ Phase 6: Build System

**File:** `cobol/Makefile` (74 lines)  
**Status:** ✅ All targets working, all 3 programs compile with zero errors

**Compilation Flags:**
```makefile
COBC = cobc
COBFLAGS = -x -free -I copybooks
```
- `-x` — Produce executable binary
- `-free` — Free-format COBOL source (not column-sensitive)
- `-I copybooks` — Include path for COPY statements

**Available Targets:**

| Target | Command | Action |
|--------|---------|--------|
| `all` | `make all` | Compile all 3 COBOL programs |
| `run-customer-lookup` | `make run-customer-lookup CUSTOMER_ID=C-00001` | Compile + run customer lookup |
| `run-loan-process` | `make run-loan-process CUSTOMER_ID=... AMOUNT=... TERM=... PURPOSE=...` | Compile + run loan process |
| `run-fraud-check` | `make run-fraud-check CUSTOMER_ID=... AMOUNT=... MCC=... ...` | Compile + run fraud check |
| `benchmark` | `make benchmark` | Run both benchmark scripts |
| `clean` | `make clean` | Remove all compiled binaries and temp files |

**Verified:**
```bash
cd cobol && make all
# Expected: 3 binaries created (customer-lookup, loan-process, fraud-check)
# Expected: zero compilation errors or warnings
```

---

### ✅ Phase 7: Benchmarks

**Files:** `benchmarks/` (2 scripts, 459 total lines)  
**Status:** ✅ Both scripts implemented, ready to execute on Linux

---

#### ✅ Phase 7a: bench_vsam_vs_parquet.py (196 lines)

**Hypothesis:** Hybrid COBOL-Python-Parquet outperforms COBOL-only VSAM for 1M+ records  
**Method:** Compare sequential VSAM-equivalent file scan vs. Parquet + DuckDB at 5 data scales

**Test Configuration:**
- Data scales: 10K, 100K, 1M, 5M, 10M records
- Queries per scale: 100 random customer lookups
- Metric: Wall-clock time per query (milliseconds)
- Repetitions: 3 runs per scale per approach (report mean ± std)

**Approach A (VSAM Simulation):**
- Read fixed-width flat file (`data/vsam_sim.dat`) using Python sequential scan
- Binary search on sorted customer_id (simulates VSAM indexed access)
- No compression, full record reads (simulates VSAM record retrieval)

**Approach B (Hybrid Parquet + DuckDB):**
- Query `transactions/date=*/` via DuckDB with Hive partitioning
- Customer filter pushed to DuckDB (columnar predicate evaluation)
- Snappy compression reduces I/O by ~5x

**Expected Results:**
```
Scale    VSAM (ms)   Parquet (ms)   Winner
10K         5            50          VSAM
100K       15            55          VSAM
1M         80            60          Parquet ←← CROSSOVER POINT
5M        350            70          Parquet
10M       700            75          Parquet
```

**Output:** Results CSV + matplotlib line chart (`benchmarks/results/vsam_vs_parquet.png`)

---

#### ✅ Phase 7b: bench_ipc_overhead.py (263 lines)

**Hypothesis:** IPC mechanism introduces measurable latency that varies by mechanism  
**Method:** 1,000 round-trips per mechanism, measure latency distribution

**Mechanisms Tested:**
1. **Subprocess + stdout pipe:** Spawn Python, capture stdout. Most common in implementation
2. **Flat file exchange:** Write request file, invoke Python, read response file
3. **Named pipes (FIFO):** Persistent Python daemon, FIFO communication (Linux only)

**Metrics Collected:**
- Mean latency
- P50 (median)
- P95 (95th percentile)
- P99 (99th percentile)
- Standard deviation

**Expected Results:**

| Mechanism | Mean | P95 | P99 | Notes |
|---|---|---|---|---|
| **Subprocess** | 50ms | 80ms | 120ms | Process creation overhead |
| **Flat File** | 30ms | 50ms | 70ms | Disk I/O overhead |
| **Named Pipes** | 12ms | 18ms | 25ms | Persistent process, best latency |

**Platform Note:** Named pipe test is **Linux-only**. On Windows, only subprocess and flat file tests run.

**Output:** Console report + CSV + box plot (`benchmarks/results/ipc_overhead.png`)

---

### ✅ Phase 8: UI Layer

**Files:** `ui/` directory (3 Python files)  
**Status:** ✅ Complete — all pages functional and tested

---

#### ✅ Phase 8a: ui/parse.py (540+ lines)

**Purpose:** Output parsing utilities for all backend scripts  
**Status:** ✅ 8 parser functions, all tested with real outputs

| Function | Input | Output | Validates |
|----------|-------|--------|----------|
| `parse_customer_360(raw)` | 145-byte string | Dict with 7 fields | Exact byte count, return code |
| `parse_loan_scoring(raw)` | 51-byte string | Dict with 6 fields | Exact byte count, eligible Y/N |
| `parse_fraud_detect(raw)` | 78-byte string | Dict with 5 fields | Exact byte count, risk level valid |
| `parse_customer_search(raw)` | Count + pipe rows | List of dicts | Count matches row count |
| `parse_customer_list(raw)` | Count + pipe rows | (List, total_count) | 7 fields per row |
| `parse_customer_update(raw)` | `code\|message` | Dict with success bool | Code in {00, 01, 99} |
| `parse_customer_transactions(raw)` | Count + 8-field rows | Dict with transactions list | 8 fields per row |
| `parse_fraud_batch_analysis(raw)` | Summary + 10-field rows | Dict with summary + list | 10 fields per row |

**ParseError Exception:** All parsers raise `ParseError` (custom exception) with descriptive messages on invalid input, count mismatches, or unexpected return codes.

---

#### ✅ Phase 8b: ui/runner.py (70 lines)

**Purpose:** Safe subprocess execution wrapper for analytics scripts  
**Status:** ✅ Complete

**Key Behaviour:**
```python
def run_script(script: str, args: List[str]) -> str:
    result = subprocess.run(
        [sys.executable, script] + args,
        capture_output=True, text=True,
        cwd=PROJECT_ROOT,           # Always run from project root
        timeout=30                  # Hard 30s timeout
    )
    if result.returncode != 0:
        raise RunnerError(result.stderr.strip())
    return result.stdout
```

- Uses `sys.executable` (not hardcoded `python3`) for Windows/venv compatibility
- Sets `cwd=PROJECT_ROOT` so scripts can find `data/` directory
- Raises `RunnerError` on non-zero exit codes
- 30-second timeout for slow scripts (benchmark protection)

---

#### ✅ Phase 8c: ui/app.py (1000+ lines)

**Purpose:** Main Streamlit web application  
**Status:** ✅ All 4 pages implemented, all session state managed

**Pages Implemented:**

| Page | Function | Key Features |
|------|----------|---|
| Customer 360 | `page_customer_360()` | Customer search, balance, risk score, transaction history |
| Loan Assessment | `page_loan_assessment()` | Amount/term/purpose form, credit score, eligibility decision |
| Fraud Detection | `page_fraud_detection()` | All-transaction view with filters, batch analysis, risk report |
| Customer Management | `page_customer_list()` | Paginated customer list, search, update form |

**Session State Variables:**
```python
# Global (all pages)
st.session_state.selected_customer_id      # Currently selected customer
st.session_state.selected_customer_name    # Display name

# Fraud Detection page
st.session_state.fraud_all_transactions    # Cached full transaction list
st.session_state.fraud_txns_loaded_cid    # Customer ID of cached list
st.session_state.fraud_analysis_result    # Batch analysis result
st.session_state.fraud_analysis_cid       # Customer ID of last analysis

# Customer List page
st.session_state.cust_list_page           # Current pagination page
st.session_state.cust_list_sort           # Sort column and direction
```

**Error Handling Pattern:**
```python
try:
    raw = run_script("python/customer_360.py", [customer_id])
    data = parse_customer_360(raw)
    display_results(data)
except RunnerError as e:
    st.error(f"Backend script failed: {e}")
except ParseError as e:
    st.error(f"Failed to read response: {e}")
```

---

## Feature Completion Status

### ✅ Feature: Customer Management

**Goal:** Enable tellers to search, view, and update customer records via the UI  
**Status:** ✅ Complete — all 5 phases finished

| Phase | Task | Files | Status |
|-------|------|-------|--------|
| 1 | Backend scripts | customer_search.py, customer_list.py, customer_update.py | ✅ |
| 2 | COBOL validation program | cobol/CUSTOMER-UPDATE.cbl | ✅ |
| 3 | Parse functions | ui/parse.py (3 new functions) | ✅ |
| 4 | UI components | ui/app.py (search_widget, page_customer_list) | ✅ |
| 5 | Integration tests | 33 test cases across 6 categories | ✅ |

**Integration Test Coverage (33 test cases):**

| Category | Tests | Scope |
|----------|-------|-------|
| Backend scripts | 6 | Script invocation, output format, error handling |
| Parser functions | 9 | Format parsing, edge cases (empty, 0 results) |
| UI components | 6 | Search, pagination, form submission |
| IPC contract | 4 | Byte-level format compliance |
| Error handling | 5 | Invalid input, missing customer, system errors |
| E2E workflow | 3 | Search → Select → View → Edit → Update |

---

### ✅ Feature: Fraud Detection Enhancement

**Goal:** Replace single-transaction manual form with full customer-level batch analysis  
**Status:** ✅ Complete — refactored to customer-level analysis only

| Phase | Task | Status |
|-------|------|--------|
| 1 | fraud_batch_analysis.py backend script | ✅ |
| 2 | customer_transactions.py (8-field output, no pagination) | ✅ |
| 3 | Batch fraud analysis results display | ✅ |
| 4 | Searchable/filterable transaction view (filters + dataframe) | ✅ |
| 5 | Remove single-transaction form entirely | ✅ |
| 6 | Session state refactor (remove pagination vars) | ✅ |
| 7 | End-to-end testing | ✅ |

**What Was Removed:**
- `fraud_txn_page` session state
- `fraud_selected_txn_idx` session state
- `fraud_selected_transaction` session state
- Single-transaction form (amount, MCC, location, channel, date, time fields)
- "Analyze Transaction" submit button and its result display
- Paginated transaction list with clickable rows

**What Was Added:**
- `fraud_all_transactions` session state (full cached list)
- `fraud_txns_loaded_cid` session state (cache invalidation)
- Searchable dataframe with 4 filters (search text, channel multiselect, min/max amount)
- "Analyse All Transactions" button for batch scoring
- Summary cards: Total / High Risk / Medium Risk / Low Risk counts
- Risk distribution visualization
- Full results table with per-transaction fraud scores and risk levels
- Flagged transactions section (only HIGH-risk)

---

## Critical Data Contracts

### Customer 360 Response (145 bytes)

| Field | Bytes | Format | Notes |
|-------|-------|--------|-------|
| Name | 1–50 | X(50) left-justified | Space-padded to 50 |
| Balance | 51–62 | 9(10)V99 zero-padded | No decimal point stored |
| Txn Count | 63–70 | 9(8) zero-padded | Lifetime transactions |
| Avg Monthly | 71–80 | 9(8)V99 zero-padded | Average monthly spend |
| Risk Score | 81–83 | 9(3) | 000–999 |
| Last Txn Date | 84–93 | X(10) | YYYY-MM-DD |
| Return Code | 94–95 | 99 | 00=OK, 01=NotFound, 99=Err |

### Loan Scoring Response (51 bytes)

| Field | Bytes | Format | Notes |
|-------|-------|--------|-------|
| Credit Score | 1–3 | 9(3) | 300–850 |
| Eligible | 4 | X(1) | Y or N |
| Interest Rate | 5–9 | 9V9(4) | 5 chars, e.g. 04500 = 4.5% |
| Max Amount | 10–19 | 9(8)V99 | Max approvable amount |
| Reject Reason | 20–49 | X(30) | Left-justified, space-padded |
| Return Code | 50–51 | 99 | 00=OK, 99=Err |

### Fraud Detection Response (78 bytes)

| Field | Bytes | Format | Notes |
|-------|-------|--------|-------|
| Fraud Risk | 1–6 | X(6) | "LOW   " / "MEDIUM" / "HIGH  " |
| Fraud Score | 7–9 | 9(3) | 000–100 |
| Fraud Flags | 10–69 | X(60) | Comma-separated flags |
| Recommendation | 70–76 | X(7) | "APPROVE" / "REVIEW " / "DECLINE" |
| Return Code | 77–78 | 99 | 00=OK, 99=Err |

---

## Verification Checklist

### Phase 1: Foundation Utilities
```bash
python3 -c "from python.utils.ipc_formatter import format_pic_x, format_pic_9; \
            assert format_pic_9(1234.56, 10, 2) == '000000123456'; \
            assert len(format_pic_x('Smith', 50)) == 50; print('✓ Phase 1a OK')"

python3 -c "from python.utils.parquet_reader import get_connection; \
            conn = get_connection(); print('✓ Phase 1b OK')"
```

### Phase 2: Data Generation
```bash
ls -lh data/customers.parquet data/loans.parquet data/fraud_labels.parquet
ls data/transactions/ | wc -l   # Should be 365 (one per day)
```

### Phase 3: COBOL Copybooks
```bash
cd cobol && cobc -fsyntax-only copybooks/*.cpy
# Expected: no output (zero errors)
```

### Phase 4: Python Analytics Scripts
```bash
python3 python/customer_360.py C-00001 | wc -c              # Must be 146
python3 python/loan_scoring.py C-00001 10000 36 PERS | wc -c  # Must be 52
python3 python/fraud_detect.py C-00001 500 5411 Bucharest "2025-01-15T14:30:00" POS | wc -c  # Must be 79
```

### Phase 5: COBOL Programs
```bash
cd cobol && make all   # Zero compilation errors
./customer-lookup      # Displays customer data
./loan-process         # Displays loan assessment
./fraud-check          # Displays fraud assessment
```

### Phase 7: Benchmarks
```bash
python3 benchmarks/bench_ipc_overhead.py     # Reports latency distributions
python3 benchmarks/bench_vsam_vs_parquet.py  # Reports performance crossover
```

### Phase 8: UI Layer
```bash
python3 -m py_compile ui/app.py   # Zero syntax errors
streamlit run ui/app.py           # App opens in browser
# Verify: all 4 pages load
# Verify: customer search works
# Verify: fraud detection filters work
# Verify: batch analysis produces results
```

---

## Known Gotchas

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| Python receives trailing spaces | COBOL pads fields to max width | Always `.strip()` on `sys.argv[1]` |
| COBOL fails to read partial record | Missing trailing newline | Always emit `record + "\n"` in Python |
| PIC 9V9(4) is 5 chars, not 6 | Implied decimal point (V) not stored | Count: 1 integer digit + 4 decimal digits = 5 total |
| 10M transactions OOM during generation | Bulk-at-once approach | Day-by-day loop (365 × 27K rows) |
| DuckDB partition pruning fails | Missing `hive_partitioning=true` | Always include flag in `read_parquet()` |
| Named pipes (FIFO) fail on Windows | POSIX-only | Use subprocess approach on Windows; FIFO only on Linux |
| `parse_customer_360` gets 95 bytes | `.strip()` removes trailing spaces | Use `.rstrip('\n\r')` only on response records |
| COBOL timeout not working on Windows | `timeout` command not available | Use direct invocation on Windows (without `timeout 5`) |

---

## Metrics & Timeline

| Phase | Component | LOC | Duration |
|-------|-----------|-----|----------|
| 1 | Foundation utilities | 294 | 1 week |
| 2 | Data generation | 225 | 1 week |
| 3 | COBOL copybooks | 96 | 2 days |
| 4 | Python analytics | 752 | 1 week |
| 5 | COBOL programs | 444 | 1 week |
| 6 | Build system | 74 | 2 days |
| 7 | Benchmarks | 459 | 3 days |
| 8 | UI layer | 1600+ | 2 weeks |
| F1 | Customer Management | ~500 | 1 week |
| F2 | Fraud Detection | ~300 | 3 days |
| **TOTAL** | **All phases + features** | **~4,750** | **~10 weeks** |

---

## References

- **architecture.md** — System design, 5-layer architecture, IPC bridge
- **implementation.md** — Detailed implementation guides per phase and feature
- **data.md** — Data layer: Parquet schemas, DuckDB queries, generation details
- **ui.md** — UI design, user guide, developer guide
- **fixes.md** — Bug fixes and iterative improvements
- **thesis.md** — Thesis outline and benchmarking roadmap

