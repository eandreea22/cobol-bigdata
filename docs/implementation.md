# Implementation Guide: Phases & Features

**Consolidated from:** PHASE4.md, PHASE5.md, PHASE7.md, FEATURE-*.md files

---

## Table of Contents

1. [Phase 4: Python Analytics Scripts](#phase-4-python-analytics-scripts)
2. [Phase 5: COBOL Programs](#phase-5-cobol-programs)
3. [Phase 7: Benchmarks](#phase-7-benchmarks)
4. [Feature: Customer Management](#feature-customer-management)
5. [Feature: Fraud Detection Enhancement](#feature-fraud-detection-enhancement)

---

## Phase 4: Python Analytics Scripts

### Overview

Phase 4 implements four Python analytics scripts that query the Parquet data lake and return fixed-width results to COBOL.

### Script 1: customer_360.py

**Purpose:** Return comprehensive 360° customer view  
**Invocation:** `python3 customer_360.py <customer_id>`  
**Output:** 145-byte fixed-width record to stdout

**Key Operations:**
1. Query `customers.parquet` for demographic data and balance
2. Query `transactions/*.parquet` with aggregations: COUNT(*), AVG(amount), MAX(date)
3. Compute risk score based on: transaction frequency, average amount, recency
4. Return all fields as fixed-width record

**Return Codes:**
- `00` = Success
- `01` = Customer not found
- `99` = Error (system failure, invalid input)

**Example Invocation:**
```bash
python3 python/customer_360.py C-00001
# Output: 145-byte record with name, balance, txn_count, avg_monthly, risk_score, last_txn_date, return_code
```

### Script 2: loan_scoring.py

**Purpose:** Determine loan eligibility and compute credit score  
**Invocation:** `python3 loan_scoring.py <customer_id> <amount> <term_months> <purpose_code>`  
**Output:** 51-byte fixed-width record to stdout

**Input Parameters:**
- `customer_id` — Customer identifier
- `amount` — Requested loan amount (numeric)
- `term_months` — Loan term in months (e.g., 36)
- `purpose_code` — HOME, AUTO, PERS, EDUC

**Key Operations:**
1. **Payment History Analysis:** Query loans.parquet for historical loan records; compute on-time payment ratio, avg days-past-due, default count
2. **Income Stability:** Analyze salary deposits from transactions; compute income consistency coefficient
3. **Debt-to-Income Calculation:** Sum active loan obligations; compare vs. estimated monthly income
4. **Credit Score Computation:**
   - Payment history: 35%
   - Credit utilization: 30%
   - Credit length: 15%
   - New credit: 10%
   - Credit mix: 10%
   - Normalized to 300–850 scale
5. **Eligibility Decision:** Approve if score ≥ 650 AND DTI < 0.43 AND no recent defaults
6. **Interest Rate Computation:** base_rate + risk_premium based on score tier

**Return Codes:**
- `00` = Success
- `99` = Error

**Example Invocation:**
```bash
python3 python/loan_scoring.py C-00001 15000.00 36 PERS
# Output: 51-byte record with credit_score, eligible (Y/N), int_rate, max_amount, reject_reason, return_code
```

### Script 3: fraud_detect.py

**Purpose:** Assess transaction fraud risk in real-time  
**Invocation:** `python3 fraud_detect.py <customer_id> <amount> <mcc> <location> <timestamp> <channel>`  
**Output:** 78-byte fixed-width record to stdout

**Input Parameters:**
- `customer_id` — Customer identifier
- `amount` — Transaction amount (numeric)
- `mcc` — Merchant category code (4 digits)
- `location` — City/country of transaction
- `timestamp` — ISO 8601 timestamp
- `channel` — POS, ATM, ONL, or MOB

**Key Checks:**
1. **Amount Anomaly:** Flag if amount > (mean + 3σ) of customer's historical transactions
2. **Geographic Anomaly:** Flag rapid location changes (e.g., Bucharest to Lagos within hours)
3. **Velocity Check:** Flag if transaction count in last hour or 24 hours exceeds threshold
4. **Category Anomaly:** Flag transactions in merchant categories customer has never used
5. **Time-of-Day Analysis:** Minor flag for transactions outside customer's normal active hours

**Risk Scoring:**
- Aggregates flags to produce fraud score (0–100)
- Maps to risk level: LOW (0–40), MEDIUM (41–75), HIGH (76–100)
- Produces recommendation: APPROVE, REVIEW, or DECLINE

**Return Codes:**
- `00` = Success
- `99` = Error

**Example Invocation:**
```bash
python3 python/fraud_detect.py C-00001 500.00 5411 Bucharest 2025-01-15T14:30:00 POS
# Output: 78-byte record with fraud_risk, fraud_score, fraud_flags, recommendation, return_code
```

### Script 4: report_aggregator.py

**Purpose:** Aggregate multiple analytics results into a unified report  
**Invocation:** `python3 report_aggregator.py <customer_id>`  
**Output:** Multi-line report to stdout

**Operations:**
- Calls customer_360.py, loan_scoring.py, fraud_detect.py
- Aggregates results into a comprehensive customer profile
- Formats output as human-readable report or machine-parseable structure

---

## Phase 5: COBOL Programs

### Overview

Phase 5 implements three COBOL programs that orchestrate business logic and call Python analytics scripts.

### Program 1: CUSTOMER-LOOKUP.cbl

**Purpose:** Retrieve comprehensive customer 360° information  
**Compilation:** `gnucobol -x CUSTOMER-LOOKUP.cbl -o customer-lookup`  
**Invocation:** `./customer-lookup`

**Input:** Prompts user for customer ID  
**Output:** Formatted display of customer information  
**Calls:** `python3 python/customer_360.py`

**COBOL Copybook:** `cobol/copybooks/CUSTOMER-REC.cpy` (145 bytes)

**IPC Flow:**
1. Accept customer_id from user input
2. Call SYSTEM to execute Python script: `python3 python/customer_360.py <customer_id>`
3. Read response record (145 bytes) from stdout/file
4. Parse with `parse_customer_360()` function
5. Validate RETURN-CODE (00=success, 01=not found, 99=error)
6. Display results or error message

### Program 2: LOAN-PROCESS.cbl

**Purpose:** Process loan application and determine eligibility  
**Compilation:** `gnucobol -x LOAN-PROCESS.cbl -o loan-process`  
**Invocation:** `./loan-process`

**Input:** Prompts user for customer_id, loan_amount, term_months, purpose_code  
**Output:** Loan eligibility decision with credit score and interest rate  
**Calls:** `python3 python/loan_scoring.py`

**COBOL Copybook:** `cobol/copybooks/LOAN-REC.cpy` (51 bytes)

**IPC Flow:**
1. Accept loan application parameters
2. Validate input (amount > 0, term valid, purpose_code recognized)
3. Call SYSTEM with Python script and parameters
4. Read response record (51 bytes)
5. Parse with `parse_loan_scoring()` function
6. Display decision: approved with credit score/rate or rejected with reason

### Program 3: FRAUD-CHECK.cbl

**Purpose:** Screen transaction for fraud risk  
**Compilation:** `gnucobol -x FRAUD-CHECK.cbl -o fraud-check`  
**Invocation:** `./fraud-check`

**Input:** Prompts user for transaction details (customer_id, amount, mcc, location, timestamp, channel)  
**Output:** Fraud risk assessment and recommendation  
**Calls:** `python3 python/fraud_detect.py`

**COBOL Copybook:** `cobol/copybooks/FRAUD-REC.cpy` (78 bytes)

**IPC Flow:**
1. Accept transaction details
2. Validate input parameters
3. Call SYSTEM with Python script and parameters
4. Read response record (78 bytes)
5. Parse with `parse_fraud_detect()` function
6. Display risk assessment: LOW/MEDIUM/HIGH with flags and recommendation

### IPC Error Handling Pattern

All three programs implement three-tier error handling:

**Tier 1: Script Execution Error**
```cobol
CALL "SYSTEM" USING "python3 python/customer_360.py C-00001"
IF RETURN-CODE NOT = 0
    DISPLAY "Python script failed"
    SET FLAG-ERROR TO TRUE
END-IF
```

**Tier 2: Response Parsing Error**
```cobol
IF CUST-RETURN-CODE = "99"
    DISPLAY "Script error: " CUST-ERROR-MSG
    SET FLAG-ERROR TO TRUE
END-IF
```

**Tier 3: Timeout**
```cobol
ACCEPT RESPONSE-REC 
    USING TIMEOUT 5 SECONDS
IF TIMEOUT-OCCURRED
    SET FLAG-ERROR TO TRUE
    MOVE "UNKNOWN" TO FLAG-RISK
END-IF
```

---

## Phase 7: Benchmarks

### Overview

Phase 7 implements two benchmarks comparing the hybrid COBOL-Python approach against traditional COBOL-only processing.

### Benchmark 1: VSAM vs. Parquet Query Performance

**File:** `benchmarks/bench_vsam_vs_parquet.py`

**Hypothesis:** For datasets exceeding 1 million records, the COBOL + Python + DuckDB/Parquet hybrid outperforms COBOL-only VSAM sequential scanning for analytical queries.

**Methodology:**
1. Generate datasets at varying scales: 10K, 100K, 1M, 5M, 10M records
2. Implement same customer lookup query in both approaches:
   - (A) COBOL reading VSAM-equivalent indexed file
   - (B) COBOL calling Python + DuckDB on Parquet
3. Measure wall-clock time for 100 random customer lookups at each scale
4. Record the crossover point where hybrid becomes faster
5. Plot results as line chart (x = dataset size, y = average query time)

**Expected Outcome:**
- Pure VSAM: O(log n) lookup via index, but full record reads
- Parquet + DuckDB: O(log n) partition pruning + columnar scan, faster for large datasets
- Crossover point typically around 1M records

### Benchmark 2: IPC Overhead Analysis

**File:** `benchmarks/bench_ipc_overhead.py`

**Hypothesis:** The IPC bridge introduces measurable but acceptable latency overhead that varies by communication mechanism.

**Methodology:**
1. Execute 1,000 identical requests through each IPC option:
   - Option A: Subprocess stdout pipe
   - Option B: Flat file exchange
   - Option C: Named pipes (FIFO)
2. Measure round-trip times (COBOL invocation to response received)
3. Record distribution: mean, P50, P95, P99 latencies

**Expected Outcome:**
- **Subprocess:** Mean ~50–100ms, high variance, process creation overhead visible
- **Flat File:** Mean ~30–50ms, moderate variance, disk I/O effects
- **Named Pipes:** Mean ~10–20ms, low variance, persistent connection benefits

**Use Case:**
- Fraud detection (real-time): Named pipes (P99 < 50ms target)
- Customer lookup (interactive): Subprocess (acceptable if < 500ms)
- Batch reporting: Flat file (throughput over latency)

---

## Feature: Customer Management

**Status:** ✅ Complete

**Purpose:** Enable tellers to search for and manage customers (create, update, view) without direct database access.

### Architecture Overview

```
User Interface (Streamlit)
    ├─ Search Widget: Find customers by last name
    ├─ Customer List Page: Paginated results with detail view
    ├─ Customer Update Form: Modify customer data
    │
    └─ Backend Python Scripts
        ├─ customer_search.py (frontend: search by name)
        ├─ customer_list.py (backend: fetch paginated list)
        ├─ customer_update.py (backend: validate + update)
        │
        └─ Python Parser Functions (ui/parse.py)
            ├─ parse_customer_search() — parse pipe-delimited results
            ├─ parse_customer_list() — parse paginated list
            └─ parse_customer_update() — parse update response
```

### Phase 1: Backend Scripts

#### Script: customer_search.py
- **Purpose:** Search customers by last name (prefix match)
- **Input:** Last name prefix (e.g., "Smith")
- **Output:** Pipe-delimited results: `count\ncustomer_id|name|city|email\n...`
- **Query:** `SELECT * FROM customers.parquet WHERE name LIKE 'Smith%'`
- **Returns:** Up to 100 matches

#### Script: customer_list.py
- **Purpose:** Fetch paginated list of customers (with filtering/sorting)
- **Input:** limit (10), offset (0), sort_field (name)
- **Output:** Pipe-delimited: `total_count\ncustomer_id|name|email|city|street|balance|monthly_income\n...`
- **Query:** `SELECT * FROM customers.parquet ORDER BY <sort> LIMIT <limit> OFFSET <offset>`
- **Returns:** Page of results with total count for pagination

#### Script: customer_update.py
- **Purpose:** Validate and update customer record
- **Input:** customer_id, field_name, new_value
- **Output:** Pipe-delimited: `return_code|message`
- **Validation Rules:**
  - customer_id must exist
  - field_name must be updateable (name, email, city, street)
  - value must match field type (string max length, etc.)
- **Returns:** 00=success, 01=validation error, 99=system error

### Phase 2: COBOL Validation Program

**File:** `cobol/CUSTOMER-UPDATE.cbl`

**Purpose:** Server-side validation of customer updates (207-byte input record)

**Input Record (207 bytes):**
| Field | Start | Len | Type |
|-------|-------|-----|------|
| CUST-ID | 1 | 10 | X |
| FIELD-NAME | 11 | 20 | X |
| NEW-VALUE | 31 | 177 | X |

**Output Record (52 bytes):**
| Field | Start | Len | Type |
|-------|-------|-----|------|
| RETURN-CODE | 1 | 2 | X |
| ERROR-MSG | 3 | 50 | X |

**Validation Logic:**
1. Check customer_id exists in customers.parquet
2. Validate field_name is updateable (CUST-NAME, CUST-EMAIL, CUST-CITY, CUST-STREET)
3. Validate NEW-VALUE format (length, data type)
4. Return 00 if valid, 01 if validation fails, 99 if error

### Phase 3: Parse Functions (ui/parse.py)

```python
def parse_customer_search(raw: str) -> List[Dict[str, str]]:
    """Parse: count line + pipe-delimited rows (customer_id|name|city|email)"""
    
def parse_customer_list(raw: str) -> Tuple[List[Dict[str, Any]], int]:
    """Parse: total line + pipe-delimited rows (7 fields) + return total"""
    
def parse_customer_update(raw: str) -> Dict[str, Any]:
    """Parse: return_code|message format"""
```

### Phase 4: UI Components (ui/app.py)

#### Component 1: search_widget()
- **Purpose:** Persistent search box for finding customers by last name
- **UI:** Text input + search button (→)
- **Behavior:** On search, queries customer_search.py and displays results
- **State:** Stores selected customer in session state

#### Component 2: page_customer_list()
- **Purpose:** Paginated view of all customers with search/filter
- **UI:** Dataframe with columns: ID, Name, Email, City, Street, Balance, Monthly Income
- **Features:** Pagination controls, sort by column, click for details
- **Calls:** customer_list.py

#### Component 3: Customer Update Form
- **Purpose:** Edit customer details (name, email, city, street)
- **UI:** Form fields + submit button
- **Calls:** customer_update.py
- **Validation:** Checks return_code from COBOL program

### Phase 5: Integration Testing

**Test Cases:** 33 tests across 6 categories
- **Backend Scripts:** Script invocation, output format validation, error handling
- **Parser Functions:** Format parsing, edge cases, error detection
- **UI Components:** Search functionality, pagination, form submission
- **IPC Contract:** Byte-level format compliance
- **Error Handling:** Invalid input, missing customer, system errors
- **E2E Workflow:** Search → Select → View → Edit → Update

---

## Feature: Fraud Detection Enhancement

**Status:** ✅ Complete

**Purpose:** Enable batch fraud analysis on ALL customer transactions, with searchable/filterable transaction view.

### Design Philosophy

**Original Approach (Replaced):**
- Manually enter transaction details (amount, MCC, location, etc.)
- Analyze one transaction at a time
- Requires user memory of transaction information

**New Approach (Current):**
- Auto-load ALL transactions for selected customer
- Searchable/filterable transaction list (merchant, city, channel, amount range)
- Single "Analyse All Transactions" button for batch fraud scoring
- Results show summary cards (Total, High Risk, Medium Risk, Low Risk)
- Full transaction table with fraud scores and risk levels
- Flagged transactions section highlighting HIGH-risk items

### Key Changes

#### Backend: customer_transactions.py
- **Purpose:** Fetch ALL transactions for a customer
- **Previous:** Limited to N rows per page (pagination)
- **Current:** Fetches ALL transactions in one pass
- **Output:** 8-field format: `txn_id|date|time|amount|merchant|mcc|city|channel`
- **Fields Added:** merchant name + time extracted from timestamp

#### UI: Transaction View
- **Previous:** Paginated 10-row clickable list → select 1 transaction → auto-fill form
- **Current:** Full dataframe with client-side filtering
  - Search box: Filter by merchant or city (case-insensitive)
  - Channel multiselect: Filter by POS, ATM, ONL, MOB
  - Min/Max amount: Range filter
  - Real-time filtering with pandas DataFrame

#### Analysis Method
- **Previous:** Per-transaction analysis (`fraud_detect.py`)
- **Current:** Batch analysis (`fraud_batch_analysis.py`)
  - Scores ALL transactions in single pass
  - Returns summary: Total, High count, Medium count, Low count
  - Returns per-transaction: txn_id, date, amount, mcc, city, channel, score, risk, recommendation, is_fraud

### Implementation Details

#### Script: fraud_batch_analysis.py
- **Purpose:** Score ALL transactions for a customer
- **Input:** customer_id
- **Output:** Summary line + transaction lines
- **Summary Format:** `total|high_count|medium_count|low_count`
- **Per-Transaction Format:** `txn_id|date|amount|mcc|city|channel|score|risk|recommendation|is_fraud`
- **Risk Levels:** LOW (0–40), MEDIUM (41–75), HIGH (76–100)
- **Recommendations:** APPROVE, REVIEW, DECLINE

#### UI: Filter Implementation
```python
# Parse transaction list
df = pd.DataFrame(txns)

# Apply filters
if search_text:
    mask = (
        df['merchant'].str.contains(search_text, case=False, na=False) |
        df['city'].str.contains(search_text, case=False, na=False)
    )
    df = df[mask]

if channel_filter:
    df = df[df['channel'].isin(channel_filter)]

if min_amount > 0:
    df = df[df['amount'] >= min_amount]

if max_amount > 0:
    df = df[df['amount'] <= max_amount]

# Display
st.dataframe(df, use_container_width=True, height=400)
```

#### UI: Results Display
- **Summary Cards:** Total transactions, High risk count, Medium risk count, Low risk count
- **Risk Distribution:** Pie chart showing % HIGH, MEDIUM, LOW
- **Full Results Table:** All transactions with computed fraud scores
  - Columns: ID, Date, Time, Amount, Merchant, MCC, City, Channel, Fraud Score, Risk Level, Recommendation
  - Color-coding: Green (LOW), Yellow (MEDIUM), Red (HIGH)
- **Flagged Transactions Section:** Only HIGH-risk transactions listed
  - Detailed view with all fields + fraud flags

### Parser Function: parse_fraud_batch_analysis()

```python
def parse_fraud_batch_analysis(raw: str) -> Dict[str, Any]:
    """
    Parse batch fraud analysis output (pipe-delimited).
    
    Format:
        total|high_count|medium_count|low_count
        txn_id|date|amount|mcc|city|channel|score|risk|recommendation|is_fraud
        ...
    
    Returns:
        {
            'summary': {total, high_count, medium_count, low_count},
            'transactions': [list of dicts with all transaction fields]
        }
    """
```

### Session State Management

```python
# New session variables for batch analysis
'fraud_all_transactions'       # List of all txns for current customer (cached)
'fraud_txns_loaded_cid'        # Customer ID of cached list (for cache invalidation)

# Removed session variables (pagination is gone)
# - 'fraud_txn_page'
# - 'fraud_selected_txn_idx'
# - 'fraud_selected_transaction'
```

### User Guide

**Workflow:**
1. Navigate to "Fraud Detection" page
2. Search for customer by last name → Select from results
3. All transactions auto-load below
4. Use filters to explore:
   - Search merchant name or city
   - Select specific channels (ATM, Online, etc.)
   - Filter by amount range
5. Click "Analyse All Transactions" button
6. View batch results: summary cards, risk distribution, full table, flagged transactions

### Performance Metrics

| Metric | Target | Actual |
|--------|--------|--------|
| Load all transactions | <500ms | ~100–200ms |
| Apply filters | Real-time | <50ms |
| Run batch analysis | <2s | ~1–1.5s |
| Display results | Real-time | ~200ms |

---

## Quick Reference: All IPC Contracts

### Customer 360 Response (145 bytes)
| Field | Bytes | Type |
|-------|-------|------|
| Name | 50 | X(50) |
| Balance | 12 | 9(10)V99 |
| Txn Count | 8 | 9(8) |
| Avg Monthly | 10 | 9(8)V99 |
| Risk Score | 3 | 9(3) |
| Last Txn Date | 10 | X(10) |
| Return Code | 2 | X(2) |

### Loan Scoring Response (51 bytes)
| Field | Bytes | Type |
|-------|-------|------|
| Credit Score | 3 | 9(3) |
| Eligible | 1 | X(1) |
| Interest Rate | 5 | 9V9(4) |
| Max Amount | 10 | 9(8)V99 |
| Reject Reason | 30 | X(30) |
| Return Code | 2 | X(2) |

### Fraud Detection Response (78 bytes)
| Field | Bytes | Type |
|-------|-------|------|
| Risk | 6 | X(6) |
| Score | 3 | 9(3) |
| Flags | 60 | X(60) |
| Recommendation | 7 | X(7) |
| Return Code | 2 | X(2) |

---

## References

- **CLAUDE.md** — Claude Code session guidance
- **architecture.md** — System architecture & data layer
- **progress.md** — Implementation status checklists
- **thesis.md** — Thesis outline & benchmarking roadmap

