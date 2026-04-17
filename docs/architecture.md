# System Architecture: Complete Technical Reference

## Executive Summary

BankCore Analytics implements a **5-layer hybrid architecture** connecting legacy COBOL mainframe logic to modern Python analytics via a fixed-width **IPC bridge**. This document describes every layer, all 12 IPC contracts, and the complete data flow for three core analytics modules.

---

## Layer 1: COBOL Business Logic

### Programs

| Program | Input | Output | IPC Record | Calls |
|---------|-------|--------|-----------|-------|
| `CUSTOMER-LOOKUP.cbl` | customer_id (CLI) | Comprehensive profile | CUSTOMER-REC (145 bytes) | `python/customer_360.py` |
| `LOAN-PROCESS.cbl` | customer_id, amount, term, purpose (CLI) | Credit score + eligibility | LOAN-REC (51 bytes) | `python/loan_scoring.py` |
| `FRAUD-CHECK.cbl` | customer_id, amount, mcc, location, timestamp, channel (CLI) | Fraud risk assessment | FRAUD-REC (78 bytes) | `python/fraud_detect.py` |
| `CUSTOMER-UPDATE.cbl` | Input file path (CLI arg) | Validation response | stdout (52 bytes) | None (validation engine) |

### Copybooks (IPC Contracts)

**CUSTOMER-REC.cpy (145 bytes)**
```
Offset  Length  Field                   COBOL Type  Example
─────────────────────────────────────────────────────────
0       50      CR-CUST-NAME            PIC X(50)   "John Smith                                            "
50      12      CR-ACCT-BALANCE-STR     PIC X(12)   "000123456789"  (dollars, no decimal point)
62      8       CR-TXN-COUNT-STR        PIC X(8)    "00000125"      (8 digits)
70      10      CR-AVG-MONTHLY-STR      PIC X(10)   "00002349"      (dollars, no decimal point, right-padded)
80      3       CR-RISK-SCORE-STR       PIC X(3)    "456"           (0-999)
83      10      CR-LAST-TXN-DATE        PIC X(10)   "2026-04-15"    (YYYY-MM-DD)
93      2       CR-RETURN-CODE-STR      PIC X(2)    "00"            (00=success, 01=not found, 99=error)
95      50      CR-RESERVED             PIC X(50)   spaces
```

**FRAUD-REC.cpy (78 bytes)**
```
Offset  Length  Field                   COBOL Type  Content
─────────────────────────────────────────────────────────
0       6       FR-FRAUD-RISK           PIC X(6)    "LOW   " / "MEDIUM" / "HIGH  "
6       3       FR-FRAUD-SCORE-STR      PIC X(3)    "085"           (0-100)
9       60      FR-FRAUD-FLAGS          PIC X(60)   "AMOUNT_ANOMALY,GEO_ANOMALY,..."
69      7       FR-RECOMMEND            PIC X(7)    "APPROVE" / "REVIEW " / "DECLINE"
76      2       FR-RETURN-CODE-STR      PIC X(2)    "00" / "99"
```

**LOAN-REC.cpy (51 bytes)**
```
Offset  Length  Field                   COBOL Type  Content
─────────────────────────────────────────────────────────
0       3       LR-CREDIT-SCORE-STR     PIC X(3)    "750"           (300-850)
3       1       LR-ELIGIBLE             PIC X(1)    "Y" / "N"
4       5       LR-INT-RATE-STR         PIC X(5)    "03500"         (3.5% as 3500 = 3.5 * 1000)
9       10      LR-MAX-AMOUNT-STR       PIC X(10)   "0000250000"    (dollars, no decimal)
19      30      LR-REJECT-REASON        PIC X(30)   "Credit score too low              "
49      2       LR-RETURN-CODE-STR      PIC X(2)    "00" / "01" / "99"
```

### IPC Mechanism: COBOL → Python

1. COBOL builds shell command string via `STRING ... DELIMITED BY SIZE`
2. Executes `CALL "SYSTEM" USING WS-CMD` (e.g., `python python/customer_360.py C-00001 > cust-response.dat`)
3. Reads response file with `ORGANIZATION IS LINE SEQUENTIAL`, moves to REDEFINES overlay
4. Parses numeric strings via `FUNCTION NUMVAL()`
5. Deletes temp file, returns to caller

Example (CUSTOMER-LOOKUP.cbl):
```cobol
MOVE "python python/customer_360.py C-00001 > cust-response.dat" TO WS-CMD
CALL "SYSTEM" USING WS-CMD
OPEN INPUT CUST-RESPONSE-FILE
READ CUST-RESPONSE-FILE INTO WS-RAW-CUST-RESPONSE
```

### Design Notes

- **No persistent IPC state:** Each invocation creates fresh Python process
- **Timeout protection:** Not implemented in COBOL (would require extension)
- **Error handling:** Three-tier (exit code, return_code, value validation)
- **Path handling:** Hard-coded relative paths (Python scripts in ../python/)

---

## Layer 2: Data Access (DuckDB + Parquet)

### Architecture
- **DuckDB**: In-process SQL engine (no server), created fresh per query
- **Parquet files**: Columnar format, Snappy-compressed, read-only from Python/DuckDB
- **Hive partitioning**: transactions/ split by date for partition pruning

### Datasets

| Dataset | Records | Format | Partitioning | Key Fields |
|---------|---------|--------|---|---|
| customers.parquet | 100,000 | Snappy Parquet | None | customer_id (PK: C-00001..C-100000), name, dob, city, account_open_date, credit_tier, email, monthly_income |
| loans.parquet | 500,000 | Snappy Parquet | None | loan_id, customer_id (FK), amount, term, rate, status, purpose, origination_date, on_time_payments, total_payments, days_past_due |
| transactions/ | 10,000,000 | Hive-partitioned (365 dirs) | date=YYYY-MM-DD | txn_id, customer_id (FK), amount, merchant, mcc, city, timestamp, channel |
| fraud_labels.parquet | 50,000 | Snappy Parquet | None | txn_id (FK, soft), is_fraud (bool), fraud_type, detection_method |

### Query Patterns

**Stateless per-query model:**
```python
conn = duckdb.connect(":memory:")  # Fresh instance
result = conn.execute("SELECT ... FROM read_parquet(...)")
# ...process result...
# conn closes implicitly (no explicit close needed)
```

**Partition pruning (hive_partitioning=true):**
```python
df = duckdb.sql("""
    SELECT * FROM read_parquet('data/transactions/*/*.parquet', hive_partitioning=true)
    WHERE date >= '2026-01-01' AND customer_id = 'C-00001'
""")
```
DuckDB automatically skips directories not matching the date range predicate.

**Aggregation across 365 partitions (~50-100ms for single customer):**
```python
duckdb.sql("""
    SELECT COUNT(*), AVG(amount), SUM(amount), STDDEV(amount), MAX(timestamp)
    FROM read_parquet('data/transactions/**/*.parquet', hive_partitioning=true)
    WHERE customer_id = ?
""")
```

### Performance Baselines (on 2026 laptop)

| Query | Records Scanned | P50 Latency | P99 Latency |
|-------|---|---|---|
| Single customer 100 transactions lookup | 1,000 | 15ms | 25ms |
| Single customer aggregate (all trans) | 10,000 (avg) | 50ms | 100ms |
| All-customer aggregate (full scan) | 10,000,000 | 2000ms | 3000ms |

---

## Layer 3: IPC Bridge

### Numeric Encoding (Critical)

**PIC 9 (Cobol numeric) encoding:**
- Stored as string, no decimal point
- `format_pic_9(4.75, 1, 2)` → `"0475"` (represents 4.75 with 1 integer + 2 decimal digits)
- Parser divides by 10^decimal_digits: `int("0475") / 100 = 4.75`

**PIC X (Alphanumeric) encoding:**
- `format_pic_x("John", 50)` → `"John" + 46 spaces`
- Parser uses `.rstrip()` only on trailing spaces, never on content

### Three IPC Mechanisms (Benchmarked)

#### Mechanism A: Subprocess + File (Used in Production)
```cobol
CALL "SYSTEM" USING "python python/customer_360.py C-00001 > cust-response.dat"
OPEN INPUT RESPONSE-FILE
READ RESPONSE-FILE INTO WS-RESPONSE
```
- **Latency:** P50 ~50ms, P99 ~120ms (includes Python startup overhead)
- **Reliability:** High (filesystem atomic writes)
- **Complexity:** Medium (file handle management)

#### Mechanism B: Named Pipes (FIFO)
```cobol
mkfifo cust-request.fifo && mkfifo cust-response.fifo
CALL "SYSTEM" USING "python python/customer_360.py < cust-request.fifo > cust-response.fifo"
```
- **Latency:** P50 ~12ms, P99 ~30ms (no file I/O)
- **Reliability:** Medium (requires daemon process, Linux-only)
- **Complexity:** High (process synchronization)

#### Mechanism C: Direct Subprocess + Pipe (Python-native)
```python
result = subprocess.run(
    [sys.executable, "python/customer_360.py", "C-00001"],
    capture_output=True, text=True, timeout=30
)
record = result.stdout.rstrip('\n\r')  # Critical: preserve trailing spaces
```
- **Latency:** Same as Mechanism A (~50ms)
- **Complexity:** Low (Python standard library)

---

## Layer 4: Python Analytics Engine

### Script Execution Model

**Input/Output contract:**
- Input: Command-line arguments only (no stdin, no files read)
- Output: Single fixed-width record to stdout + newline
- Logging: **Always stderr**, never stdout (stdout reserved for IPC record)
- Return: Exit code 0 on success, non-zero on exception

**Example invocation:**
```bash
python python/customer_360.py C-00001
# stdout:  "<145-byte record>\n"
# stderr:  "[2026-04-17 10:30:42] Loaded 100K customers, queried 15K transactions in 45ms"
# exit:    0
```

### Module Reference

#### python/customer_360.py
**Risk Score Calculation** (0–999):
- Transaction frequency: 0 txns=300, <12=250, <50=200, <100=100, <200=50, else=10
- Average amount: >$5000=400, >$2000=300, >$1000=200, >$500=100, >$100=30, else=0
- Recency (days): 0=0, ≤7=10, ≤30=50, ≤90=150, ≤365=250, else=300
- **Total:** Additive, capped at 999

**Balance approximation:** monthly_income × 3 (conservative savings estimate)

#### python/loan_scoring.py
**Credit Score (300–850):**
Five weighted factors:
- Payment history (35%): on_time_payments / total_payments
- Credit utilization (30%): 1 - (active_balance / (monthly_income × 12 × 0.5))
- Credit length (15%): account_age_years / 15 (normalized)
- New credit (10%): 1.0 if no loans in last 6 months, else 0.3
- Credit mix (10%): unique_loan_purposes / 3 (capped at 1.0)
- **Formula:** raw_score (0–1) → 300 + raw_score × 550

**Eligibility:** credit_score ≥ 650 AND DTI < 0.43 AND no defaults in last 730 days

**Interest rates:** base 4.0% + premium based on score

#### python/fraud_detect.py
**Fraud Score (0–100, 6 checks):**
- Amount anomaly (z-score > 3σ): +35 pts
- Geographic anomaly: +25 pts
- High velocity 1h (≥5 txns): +20 pts
- High velocity 24h (≥20 txns): +10 pts
- Category anomaly (MCC not in history): +15 pts
- Unusual hour (< 6 or > 23): +5 pts
- **Classification:** LOW (<40), MEDIUM (40–70), HIGH (≥70)

### Utility Functions

#### python/utils/ipc_formatter.py
```python
def format_pic_x(value, length):
    """Left-justify, space-pad to exactly length chars"""
    return str(value).ljust(length)[:length]

def format_pic_9(value, int_digits, dec_digits=0):
    """Right-justify, zero-pad numeric (no decimal point in output)"""
    # Scales by 10^dec_digits, then zero-pads to total digits
    scaled = int(abs(value) * (10 ** dec_digits))
    total_digits = int_digits + dec_digits
    return str(scaled).zfill(total_digits)[-total_digits:]
```

#### python/utils/parquet_reader.py
Four stateless query wrappers (each creates own DuckDB instance):
- `query_customer(conn, customer_id)` → dict or None
- `query_transactions_agg(conn, customer_id)` → dict with 11 statistics
- `query_loans(conn, customer_id)` → list of loan dicts
- `query_fraud_labels(conn, txn_id)` → dict or None

---

## Layer 5: User Interface

### Streamlit UI (ui/app.py)

**Design system:**
- Color palette: Dark navy (#0f172a) + accent cyan (#00d4ff)
- Dark mode throughout, Epilogue sans-serif font
- CSS injected via `st.markdown(CSS, unsafe_allow_html=True)`
- Responsive layout for desktop (no mobile optimization)

**4 pages:**
1. **Customer 360** — Search → Risk profile + metrics + transaction timeline
2. **Loan Assessment** — Search + form (amount, term, purpose) → Decision card + metrics
3. **Fraud Detection** — Search → Filterable transaction table + batch scoring
4. **Customer Management** — Paginated editable dataframe with 100 rows/page

**User flow:**
```
Search by name (e.g., "Smith") 
  ↓
Dropdown with matching customers + IDs
  ↓
Select a customer (e.g., "Allison Smith, C-00001")
  ↓
Page auto-loads customer data (no second click)
  ↓
View/edit data (e.g., loan form, fraud details)
```

### React UI (frontend/)

**Stack:**
- React 18.2 + TypeScript + Vite (dev: port 3002, prod: Nginx)
- Axios HTTP client with 30s timeout
- Framer Motion for animations
- Recharts for charts (imported, not used in current pages)

**4 pages (mirroring Streamlit):**
1. **Dashboard** (Customer 360°) — SearchWidget → Profile card + metrics
2. **LoanAssessment** — SearchWidget + form → StatusCard with eligibility
3. **FraudDetection** — SearchWidget → Auto-loaded transaction table + filters
4. **CustomerManagement** — Auto-loads 100 customers on mount + search/filter

**Special component: SearchWidget.tsx**
```tsx
<SearchWidget pageKey="c360" onSelect={(customerId, customerName) => {
  // Navigate or fetch customer data
}} />
```
- Searches by name via `GET /customers?search=...`
- Shows dropdown of results
- On selection, shows customer badge + "Change" button
- Page key prevents state collision when used on multiple pages

**Cross-page navigation pattern:**
```tsx
// In App.tsx
const [preSelectedCustomerId, setPreSelectedCustomerId] = useState(null)

// CustomerManagement button: "View 360° Profile"
<Button onClick={() => {
  setPreSelectedCustomerId(customer.customer_id)
  setCurrentPage('dashboard')
}} />

// Dashboard useEffect
useEffect(() => {
  if (preSelectedCustomerId) {
    handleFetch(preSelectedCustomerId)
  }
}, [preSelectedCustomerId])
```

---

## FastAPI Backend (backend/main.py + wrappers.py)

### REST API Endpoints (All mapped to wrappers.py)

| Method | Path | Purpose | Response |
|--------|------|---------|----------|
| GET | `/health` | Health check | `{status: "healthy", ...}` |
| GET | `/customer-360/{customer_id}` | Profile + risk score | Customer360Response |
| POST | `/loan-assessment` | Credit score + eligibility | LoanAssessmentResponse |
| POST | `/fraud-detection` | Single transaction fraud risk | FraudDetectionResponse |
| GET | `/fraud-batch/{customer_id}` | All transactions + scores | BatchFraudResponse |
| GET | `/customers?search=...&skip=0&limit=100` | List/search customers | CustomersListResponse |
| GET | `/customers/{customer_id}` | Single customer detail | CustomerRecord |
| PUT | `/customers/{customer_id}` | Update customer (stub) | CustomerRecord |
| GET | `/transactions/{customer_id}?limit=N` | Transaction list | {..., transactions: [...]} |

### wrappers.py: Direct DuckDB Implementations

**Critical architectural note:** The wrappers do NOT call the Python analytics scripts (`python/customer_360.py`, etc.). Instead, they re-implement the logic directly with DuckDB queries for web performance.

**Example: analyze_customer_360(customer_id)**
```python
def analyze_customer_360(customer_id: str):
    # Direct DuckDB query (NOT calling customer_360.py)
    customer = conn.execute(
        f"SELECT * FROM read_parquet('data/customers.parquet') WHERE customer_id = ?",
        [customer_id]
    )
    # Simplified risk score: (balance / 100000) * 500 + txn_count // 10
    # (Different from the standalone 6-factor algorithm)
```

**Algorithms in wrappers.py vs standalone scripts:**
- **Risk score:** Simplified (wrappers) vs 6-factor (standalone)
- **Fraud score:** 4 checks, 0–999 scale (wrappers) vs 6 checks, 0–100 scale (standalone)
- **Balance calculation:** income - spent (wrappers) vs income × 3 (standalone)

---

## Data Flow Diagrams

### Customer 360° End-to-End

```
User selects "Allison Hill, C-00001" in Streamlit search
        ↓
Dashboard calls: python/customer_360.py C-00001
        ↓
customer_360.py queries DuckDB:
  1. SELECT * FROM customers WHERE customer_id = 'C-00001'  [1ms]
  2. Scan transactions/* for aggregate [45ms]  
  3. Calculate risk score (3 factors)
        ↓
Writes 145-byte CUSTOMER-REC to stdout
        ↓
COBOL (CUSTOMER-LOOKUP) reads response, parses fields
        ↓
Displays: Name, Balance, Risk Score, Transactions, Dates
```

### Fraud Detection: Transaction-by-Transaction

```
User selects customer C-00001, clicks "Analyze All Transactions"
        ↓
ui/app.py calls: python/fraud_batch_analysis.py C-00001
        ↓
fraud_batch_analysis.py:
  1. Query transaction agg stats (COUNT, AVG, STDDEV) [45ms]
  2. Fetch ALL transactions for customer [15ms]
  3. For each txn, call compute_fraud_score() [6 checks]
  4. Join with fraud_labels.parquet (ground truth)
        ↓
Outputs pipe-delimited transaction list with fraud scores
        ↓
Streamlit displays filterable table (LOW/MEDIUM/HIGH tabs)
```

---

## Design Trade-offs

| Decision | Alternative | Why Chosen |
|----------|-------------|-----------|
| In-process DuckDB | Remote SQL server | Eliminates server ops, scales to laptop |
| Fixed-width IPC | JSON/REST | COBOL native (binary format), byte-predictable |
| Subprocess per call | Connection pool | Stateless, eliminates lingering connections |
| Parquet + date partition | Single file | Query pruning, enables parallel processing |
| Streamlit + React | Single UI | Streamlit for rapid iteration, React for production |

---

## Performance Summary

| Operation | Latency | Bottleneck |
|-----------|---------|-----------|
| IPC call (subprocess + file) | ~50ms | Python startup (35ms) + query (15ms) |
| DuckDB query (1M records) | ~50ms | Parquet decoding + memory allocation |
| Full transaction scan (10M) | ~2000ms | I/O, all 365 partitions |
| React page load | ~200ms | API calls + rendering |

---

## Known Limitations

1. **COBOL programs only read customer_id from CLI** — other parameters are hard-coded (documented in source via `TODO` comments)
2. **FastAPI wrappers are simplified** — different risk/fraud algorithms than standalone scripts (for web performance)
3. **No authentication** — assumes trusted internal network
4. **No backup/recovery** — Parquet files are read-only, no transactional guarantees
5. **Single-threaded DuckDB** — not suitable for true concurrent access (works fine for single-user analytics)

---

**Last Updated:** 2026-04-17
