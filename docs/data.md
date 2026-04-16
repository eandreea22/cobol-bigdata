# Data Architecture & Management

**Comprehensive reference for the Parquet + DuckDB data layer**

---

## Table of Contents

1. [Overview](#overview)
2. [Why Parquet + DuckDB?](#why-parquet--duckdb)
3. [Data Generation Flow](#data-generation-flow)
4. [Database Schema & Relationships](#database-schema--relationships)
5. [How DuckDB Queries the Data](#how-duckdb-queries-the-data)
6. [File Locations & Access Patterns](#file-locations--access-patterns)
7. [Data Contracts by Table](#data-contracts-by-table)
8. [Performance Characteristics](#performance-characteristics)
9. [Common Queries & Patterns](#common-queries--patterns)

---

## Overview

### What Is the "Database"?

The system does **NOT use a traditional SQL database server**. Instead:

- **Data is stored as Parquet files** on disk (`data/customers.parquet`, `data/transactions/`, etc.)
- **Queries are executed by DuckDB**, an in-memory analytical SQL query engine
- **Each analytics script spawns its own DuckDB instance**, queries the Parquet files, then exits

This design is **serverless, stateless, and lightweight** — perfect for a thesis project that needs to run on Windows without external dependencies.

### Data Flow Architecture

```
┌──────────────────────────────────────────────────┐
│ Data Generation (one-time)                       │
│ data/generate_synthetic.py creates Parquet files │
│ ├─ customers.parquet (100K rows)                 │
│ ├─ loans.parquet (500K rows)                     │
│ ├─ transactions/ (10M rows, 365 partitions)      │
│ └─ fraud_labels.parquet (50K rows)               │
└──────────────────┬───────────────────────────────┘
                   ↓
┌──────────────────────────────────────────────────┐
│ Query Execution (on-demand, per script)          │
│ Each Python script:                              │
│ 1. Create in-memory DuckDB instance              │
│ 2. Execute SQL against Parquet files             │
│ 3. Aggregate results                             │
│ 4. Format as fixed-width record (COBOL contract) │
│ 5. Print to stdout                               │
└──────────────────┬───────────────────────────────┘
                   ↓
┌──────────────────────────────────────────────────┐
│ COBOL Integration (optional)                     │
│ COBOL programs call analytics scripts            │
│ Parse fixed-width output records                 │
│ Display or aggregate results                     │
└──────────────────────────────────────────────────┘
```

---

## Why Parquet + DuckDB?

### Design Rationale Comparison

| Criterion | Choice | Reason |
|-----------|--------|--------|
| **Storage Format** | Apache Parquet | Columnar, compressed, fast SQL-compatible queries |
| **Query Engine** | DuckDB | In-memory SQL-native, no server setup required |
| **Server** | None (serverless) | Stateless analytics; perfect for thesis/demo |
| **Dependencies** | Minimal (`pip install duckdb pyarrow`) | Works on Windows, macOS, Linux |
| **Data Volume** | 10M+ records | Parquet handles scale efficiently; DuckDB loads in-memory |

### Advantages

✅ **No server to deploy or manage** — No PostgreSQL, MySQL, or other RDBMS overhead  
✅ **Fast columnar queries** — DuckDB optimizes for analytical workloads (reads only needed columns)  
✅ **Compression built-in** — Snappy codec reduces disk footprint from ~1GB (raw) to ~100MB (compressed)  
✅ **Native partitioning** — Hive-style `date=YYYY-MM-DD/` directory structure enables automatic partition pruning  
✅ **SQL standard** — Familiar to any developer; queries are readable and maintainable  
✅ **Cross-platform** — Same code runs on Windows, Linux, macOS without modification  
✅ **No schema migration** — Schema changes don't require ALTER TABLE; just regenerate Parquet files  

### Disadvantages

❌ Query performance degrades for very large joins (10M+ × 10M+ record combinations)  
❌ No multi-user concurrency (each process spawns its own DuckDB instance)  
❌ No transactions (stateless; writes are file-based)  
❌ Limited to analysis; not suitable for real-time transactional workloads

---

## Data Generation Flow

### Step 1: Generate Customers (100K records)

**File:** `data/generate_synthetic.py:39-65`  
**Output:** `data/customers.parquet`

**Generation Logic:**
```python
def generate_customers() -> pd.DataFrame:
    customer_ids = [f"C-{i:05d}" for i in range(1, 100_001)]  # C-00001 to C-100000
    names = [fake.name() for _ in range(100_000)]  # Faker-generated names
    dobs = [fake.date_of_birth(minimum_age=18, maximum_age=80) for _ in range(100_000)]
    cities = [fake.city() for _ in range(100_000)]  # US cities
    account_open_dates = [...]  # Random dates 1–15 years ago
    credit_tiers = rng.choice(['EXCELLENT', 'GOOD', 'FAIR', 'POOR'], 100_000)
    monthly_incomes = rng.normal(4500, 2000, 100_000)  # Avg $4.5K, std $2K
    
    df = pd.DataFrame({
        'customer_id': customer_ids,
        'name': names,
        'dob': dobs,
        'city': cities,
        'account_open_date': account_open_dates,
        'credit_tier': credit_tiers,
        'email': emails,
        'monthly_income': monthly_incomes,
    })
    
    pq.write_table(pa.Table.from_pandas(df), "data/customers.parquet", compression='snappy')
```

**Schema:**

| Field | Type | Range/Distribution | Primary Key? |
|-------|------|---------------------|---|
| customer_id | String | C-00001 to C-100000 | ✅ Yes |
| name | String | Faker-generated US names | No |
| dob | Date | Birth dates (age 18–80) | No |
| city | String | US cities (~1000 unique) | No |
| account_open_date | Date | 1–15 years ago | No |
| credit_tier | String | EXCELLENT, GOOD, FAIR, POOR (categorical) | No |
| email | String | Faker-generated emails | No |
| monthly_income | Float | Normal(4500, 2000) dollars | No |

**Size:** ~50MB on disk (compressed)

---

### Step 2: Generate Loans (500K records)

**File:** `data/generate_synthetic.py:68-101`  
**Output:** `data/loans.parquet`

**Key Relationship:**
```
loans.customer_id → customers.customer_id (FOREIGN KEY)
```
Some customers have 0 loans, others have 5–10 loans (distributed).

**Schema:**

| Field | Type | Range/Distribution | Notes |
|-------|------|---------------------|-------|
| loan_id | String | L-000001 to L-500000 | PK |
| customer_id | String | C-00001 to C-100000 | FK → customers |
| amount | Float | LogNormal(9.5, 0.7) ≈ $10K–$30K | Interest calculation |
| term | Integer | 12, 24, 36, 48, 60, 84, 120 months | Fixed set |
| rate | Float | 3.5%–24.0% | Annual interest rate |
| status | String | ACTIVE, PAID, DEFAULT, DELINQUENT | 4 states |
| purpose | String | HOME, AUTO, PERS, EDUC | Categorical |
| origination_date | Date | 10–1825 days ago | For age calculation |
| on_time_payments | Integer | 0 to term | For payment history scoring |
| total_payments | Integer | 50%–110% of term | Over/under payment |
| days_past_due | Integer | 0 or 1–365 days | 0 = no delinquency |

**Size:** ~150MB on disk (compressed)

---

### Step 3: Generate Transactions (10M records, 365 partitions)

**File:** `data/generate_synthetic.py:104-178`  
**Output:** `data/transactions/date=YYYY-MM-DD/*.parquet`

**Key Relationship:**
```
transactions.customer_id → customers.customer_id (FOREIGN KEY)
transactions.date = Hive partition key (enables efficient filtering)
```

**Partitioning Strategy:**
```
data/transactions/
  date=2025-01-01/part-0000.parquet  (27K rows)
  date=2025-01-02/part-0000.parquet  (27K rows)
  date=2025-01-03/part-0000.parquet  (27K rows)
  ...
  date=2025-12-31/part-0000.parquet  (27K rows)

Total: 365 partitions × 27K rows/partition ≈ 10M rows
```

**Why Daily Partitions?**
- DuckDB automatically prunes directories based on WHERE clauses
- Query on date range `2025-06-01` to `2025-12-31` reads only 214 partitions (skips Jan–May)
- Partition granularity (daily vs hourly vs monthly) affects pruning efficiency

**Schema:**

| Field | Type | Range/Distribution | Notes |
|-------|------|---------------------|-------|
| txn_id | String | T-00000001 to T-10000000 | PK |
| customer_id | String | C-00001 to C-100000 | FK → customers |
| amount | Float | LogNormal(5.5, 1.0) ≈ $250 typical | Fraud detection scoring |
| merchant | String | ~1000 unique merchants | Company names |
| mcc | String | 4-digit merchant category code | 1000+ unique codes |
| city | String | 90% customer's home, 10% random | Geographic anomaly |
| timestamp | ISO8601 | Date + time (hours ≈ Normal(14, 4)) | Full timestamp |
| channel | String | POS (50%), ATM (20%), ONL (20%), MOB (10%) | Categorical |
| date | Date | YYYY-MM-DD (Hive partition key) | Partition column |

**Size:** ~1GB on disk (compressed)

**Generation Details:**
- **Zipf-distributed usage:** Some customers transact 100x more than others (realistic)
- **10% geographic anomalies:** Random city injected (fraud signal for testing)
- **Business hour bias:** Hours ≈ Normal(14, 4) with clipping to 0–23 (most txns 10am–6pm)
- **Channel distribution:** POS (point-of-sale) dominant, ATM/ONL/MOB secondary
- **Day-by-day loop:** 365 iterations, ~27K rows per day (avoids RAM explosion on all-at-once generation)

---

### Step 4: Generate Fraud Labels (50K records)

**File:** `data/generate_synthetic.py:181-200`  
**Output:** `data/fraud_labels.parquet`

**Purpose:** Ground-truth labels for model training/validation. Not all 10M transactions have labels (only sampled subset).

**Schema:**

| Field | Type | Range/Distribution | Notes |
|-------|------|---------------------|-------|
| txn_id | String | T-00000001 to T-10000000 | References transactions (may not exist) |
| is_fraud | Boolean | True (15%), False (85%) | Ground truth label |
| fraud_type | String | CARD_NOT_PRESENT, ACCOUNT_TAKEOVER, IDENTITY_THEFT, NONE | 4 fraud types |
| detection_method | String | VELOCITY_CHECK, GEO_ANOMALY, ML_MODEL, MANUAL_REVIEW, NONE | How it was caught |

**Size:** ~10MB on disk (compressed)

**Notes:**
- Only 50K of 10M transactions have labels (realistic — most fraud undetected)
- 15% fraud rate is higher than real-world (typical is 0.1%–1%) to make benchmarking easier
- Labels are used to evaluate fraud detection model accuracy

---

## Database Schema & Relationships

### Entity-Relationship Diagram

```
┌─────────────────┐
│   CUSTOMERS     │
├─────────────────┤
│ customer_id (PK)│◄───┐
│ name            │    │
│ dob             │    │
│ city            │    │
│ credit_tier     │    │
│ monthly_income  │    │
└─────────────────┘    │
                       │ FK
        ┌──────────────┴─────────────┐
        │                            │
        ▼                            ▼
┌─────────────────┐      ┌──────────────────────┐
│     LOANS       │      │   TRANSACTIONS       │
├─────────────────┤      ├──────────────────────┤
│ loan_id (PK)    │      │ txn_id (PK)          │
│ customer_id(FK) │      │ customer_id (FK)     │
│ amount          │      │ amount               │
│ term            │      │ merchant             │
│ rate            │      │ mcc                  │
│ status          │      │ city                 │
│ on_time_payments│      │ timestamp            │
│ days_past_due   │      │ channel              │
└─────────────────┘      │ date (partition key) │
                         └──────────────────────┘
                                   │
                                   │ FK (txn_id)
                                   ▼
                         ┌──────────────────────┐
                         │   FRAUD_LABELS       │
                         ├──────────────────────┤
                         │ txn_id (PK)          │
                         │ is_fraud             │
                         │ fraud_type           │
                         │ detection_method     │
                         └──────────────────────┘
```

### Cardinality

| Relationship | Cardinality | Notes |
|---|---|---|
| CUSTOMERS → LOANS | 1:N | One customer has 0–10 loans |
| CUSTOMERS → TRANSACTIONS | 1:N | One customer has 1–1000 transactions |
| TRANSACTIONS → FRAUD_LABELS | 1:0..1 | One transaction has 0 or 1 label |

---

## How DuckDB Queries the Data

### Query Pattern: In-Memory Instance per Script

Every Python script follows this pattern:

```python
import duckdb

# 1. Create in-memory instance
conn = duckdb.connect(':memory:')

# 2. Execute SQL against Parquet files
result = conn.execute("""
    SELECT customer_id, COUNT(*) as txn_count
    FROM read_parquet('data/transactions/date=*/part-*.parquet', 
                      hive_partitioning=true)
    WHERE customer_id = ?
    GROUP BY customer_id
""", ['C-00001']).fetchall()

# 3. Process results and format output
for row in result:
    print(format_output(row))

# 4. Connection closes; in-memory DB is freed
conn.close()
```

### Example 1: Customer 360 Lookup

**Query:**
```sql
SELECT customer_id, name, balance, COUNT(*) as txn_count, AVG(amount) as avg_amount
FROM customers.parquet c
LEFT JOIN transactions c
  ON c.customer_id = txn.customer_id
WHERE c.customer_id = 'C-00001'
GROUP BY c.customer_id, c.name, c.balance
```

**Execution:**
1. Load `customers.parquet` (100K rows) → hash index on customer_id
2. Load `transactions/date=*/` (10M rows across 365 partitions)
3. Predicate filter: `customer_id = 'C-00001'` (reduces to ~97 rows after partition pruning)
4. Join with customers table on customer_id
5. Compute aggregates: COUNT, AVG
6. Return result

**Performance:** ~50–100ms (dominated by I/O reading partition headers)

### Example 2: Fraud Detection Check

**Query:**
```sql
SELECT * FROM transactions
WHERE customer_id = 'C-00001' 
  AND date >= CURRENT_DATE - INTERVAL 7 DAY
ORDER BY timestamp DESC
```

**Execution:**
1. Hive partitioning prunes to last 7 days of partitions
2. Read only matching partitions
3. Filter by customer_id (in-memory)
4. Sort by timestamp
5. Return all rows

**Performance:** ~20–50ms (partition pruning saves 90% of I/O)

### Example 3: Loan Scoring (Multi-Table Join)

**Query:**
```sql
SELECT 
    c.credit_tier,
    COUNT(l.loan_id) as loan_count,
    AVG(CASE WHEN l.status = 'DEFAULT' THEN 1 ELSE 0 END) as default_rate
FROM customers c
LEFT JOIN loans l ON c.customer_id = l.customer_id
WHERE c.customer_id = 'C-00001'
GROUP BY c.credit_tier
```

**Execution:**
1. Hash load customers table (100K rows) → single-pass lookup
2. Probe loans table (500K rows) for matching records
3. Aggregate defaults
4. Return result

**Performance:** ~30–80ms (disk I/O dominant)

---

## File Locations & Access Patterns

### Directory Structure

```
data/
├── generate_synthetic.py        (225 lines, creates all Parquet files)
├── customers.parquet            (100K rows, ~50MB compressed)
├── loans.parquet                (500K rows, ~150MB compressed)
├── transactions/                (10M rows across 365 partitions)
│   ├── date=2025-01-01/
│   │   └── part-0000.parquet    (~27K rows, ~1.5MB)
│   ├── date=2025-01-02/
│   │   └── part-0000.parquet
│   ├── ...
│   └── date=2025-12-31/
│       └── part-0000.parquet
└── fraud_labels.parquet         (50K rows, ~10MB compressed)
```

### Access Patterns Used

**Pattern 1: Full Scan (Customers)**
```python
conn.execute("SELECT * FROM read_parquet('data/customers.parquet')")
# Reads: 100K rows, ~50MB disk I/O
# Time: ~100–200ms
```

**Pattern 2: Partition-Pruned Scan (Transactions by Date)**
```python
conn.execute("""
    SELECT * FROM read_parquet('data/transactions/date=*/part-*.parquet', 
                               hive_partitioning=true)
    WHERE date >= '2025-06-01' AND date <= '2025-12-31'
""")
# Reads: Only 214 of 365 partitions (~6M rows, ~400MB)
# Skips: 151 partitions (~4M rows, ~250MB)
# Time: ~500–800ms
```

**Pattern 3: Single-Customer Lookup (Transactions)**
```python
conn.execute("""
    SELECT * FROM read_parquet('data/transactions/date=*/part-*.parquet', 
                               hive_partitioning=true)
    WHERE customer_id = 'C-00001'
""")
# Reads: All 365 partitions (must scan all, no index on customer_id)
# Filters: ~97 matching rows out of 10M
# Time: ~1–2s (full scan required)
```

---

## Data Contracts by Table

### CUSTOMERS.PARQUET

| Field | Type | Constraints | Notes |
|-------|------|-----------|-------|
| customer_id | String | PK, NOT NULL, format C-XXXXX | 5-digit padded |
| name | String | NOT NULL, max 100 chars | Faker-generated |
| dob | Date | NOT NULL, age 18–80 | ISO format |
| city | String | max 50 chars | US cities |
| account_open_date | Date | max current date | 1–15 years ago |
| credit_tier | String | ENUM(EXCELLENT, GOOD, FAIR, POOR) | 4-value categorical |
| email | String | max 100 chars | Faker-generated |
| monthly_income | Float | >= 0 | Normal(4500, 2000) |

### LOANS.PARQUET

| Field | Type | Constraints | Notes |
|-------|------|-----------|-------|
| loan_id | String | PK, format L-XXXXXX | 6-digit padded |
| customer_id | String | FK → customers.customer_id | 1:N with customers |
| amount | Float | > 0 | LogNormal(9.5, 0.7) |
| term | Integer | IN(12, 24, 36, 48, 60, 84, 120) | Months |
| rate | Float | 3.5–24.0 | Annual % |
| status | String | IN(ACTIVE, PAID, DEFAULT, DELINQUENT) | 4-state |
| purpose | String | IN(HOME, AUTO, PERS, EDUC) | 4-value |
| origination_date | Date | <= today | For age calc |
| on_time_payments | Integer | 0 to term | Count |
| total_payments | Integer | >= 0 | Count or days |
| days_past_due | Integer | >= 0 | 0 = current |

### TRANSACTIONS.PARQUET (Partitioned by date)

| Field | Type | Constraints | Notes |
|-------|------|-----------|-------|
| txn_id | String | PK, format T-XXXXXXXX | 8-digit padded |
| customer_id | String | FK → customers.customer_id | 1:N with customers |
| amount | Float | > 0 | LogNormal(5.5, 1.0) |
| merchant | String | max 100 chars | Company names |
| mcc | String | 4-digit code | Merchant category |
| city | String | max 50 chars | 90% home, 10% random |
| timestamp | ISO8601 | format YYYY-MM-DDTHH:MM:SS | Full timestamp |
| channel | String | IN(POS, ATM, ONL, MOB) | 4-value |
| date | Date | Hive partition key | YYYY-MM-DD |

### FRAUD_LABELS.PARQUET

| Field | Type | Constraints | Notes |
|-------|------|-----------|-------|
| txn_id | String | FK → transactions.txn_id (soft) | May not exist |
| is_fraud | Boolean | NOT NULL | Ground truth |
| fraud_type | String | IN(..., NONE) | Categorical |
| detection_method | String | IN(..., NONE) | Categorical |

---

## Performance Characteristics

### Query Performance Baselines

| Query Type | Data Size | Expected Time | Notes |
|---|---|---|---|
| Single customer lookup (transactions) | 97 txns | 50–100ms | Full 365-partition scan required |
| Customer 360 aggregate | 100K customers | 100–150ms | Index on customer_id helps |
| Loan payment history | 500K loans | 80–120ms | Filter + small join |
| Full date-range scan | 1M transactions | 500–800ms | Multiple partitions |
| Full table scan (customers) | 100K rows | 100–200ms | Small table, fast |

### Memory Usage

| Operation | RAM Required | Notes |
|---|---|---|
| customers.parquet in-memory | ~200MB | 100K rows, 8 columns |
| Single customer's txns | ~5MB | ~97 rows |
| Full 1-month txns (all customers) | ~100MB | ~810K rows |
| Full year txns (all customers) | ~1.2GB | ~10M rows |
| All tables in-memory | ~2GB | All data loaded at once |

**Note:** Most scripts only load specific customer data (~5–10MB), not full table. Full 10M-row scan is rare.

### Disk I/O Characteristics

| Metric | Value | Notes |
|---|---|---|
| Total data on disk (compressed) | ~1.2GB | 50MB + 150MB + 1GB + 10MB |
| Avg partition size | 1.5MB | Compressed |
| Avg row size (Parquet) | ~200 bytes | (compressed) |
| Partition pruning savings | ~50–90% | Depending on date range |

---

## Common Queries & Patterns

### Pattern 1: Single-Customer Analysis

```python
# Fetch all transactions for one customer
result = conn.execute("""
    SELECT txn_id, timestamp, amount, merchant, city, channel
    FROM read_parquet('data/transactions/date=*/part-*.parquet', 
                      hive_partitioning=true)
    WHERE customer_id = ?
    ORDER BY timestamp DESC
""", ['C-00001']).fetchall()
```

**Used by:** customer_transactions.py, fraud_detect.py  
**Performance:** ~50–100ms

### Pattern 2: Aggregation with Partition Pruning

```python
# Get monthly spending stats
result = conn.execute("""
    SELECT 
        DATE_TRUNC('month', timestamp) as month,
        COUNT(*) as txn_count,
        AVG(amount) as avg_amount,
        MAX(amount) as max_amount
    FROM read_parquet('data/transactions/date=*/part-*.parquet', 
                      hive_partitioning=true)
    WHERE customer_id = ? AND date >= CURRENT_DATE - INTERVAL 12 MONTH
    GROUP BY DATE_TRUNC('month', timestamp)
""", ['C-00001']).fetchall()
```

**Used by:** customer_360.py  
**Performance:** ~100–150ms (partition pruning to last 365 days)

### Pattern 3: Loan History Lookup

```python
# Get all loans for customer with payment stats
result = conn.execute("""
    SELECT loan_id, amount, term, rate, status, on_time_payments, days_past_due
    FROM read_parquet('data/loans.parquet')
    WHERE customer_id = ?
    ORDER BY origination_date DESC
""", ['C-00001']).fetchall()
```

**Used by:** loan_scoring.py  
**Performance:** ~30–50ms

### Pattern 4: Fraud Label Lookup (Bulk)

```python
# Get ground-truth labels for a set of transaction IDs
txn_ids = [row[0] for row in transactions]
result = conn.execute(f"""
    SELECT txn_id, is_fraud, fraud_type
    FROM read_parquet('data/fraud_labels.parquet')
    WHERE txn_id IN ({','.join(['?'] * len(txn_ids))})
""", txn_ids).fetchall()
```

**Used by:** fraud_batch_analysis.py  
**Performance:** ~20–40ms

---

## Regenerating Data

If you need to regenerate the synthetic data:

```bash
cd /path/to/cobol-bigdata

# Remove old data
rm -rf data/customers.parquet data/loans.parquet data/transactions data/fraud_labels.parquet

# Regenerate
python3 data/generate_synthetic.py

# Verify (check file sizes)
ls -lh data/*.parquet data/transactions/date=2025-*/
# Expected: 
#   customers.parquet  ~50MB
#   loans.parquet     ~150MB
#   transactions/     ~1GB (365 directories)
#   fraud_labels.parquet ~10MB
```

**Time:** ~5–10 minutes (depending on system RAM and disk speed)

---

## References

- **architecture.md** — System design and IPC bridge
- **implementation.md** — Python scripts that query this data
- **progress.md** — Data generation verification steps

