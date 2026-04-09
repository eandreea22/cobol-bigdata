# Data Architecture: Parquet Files + DuckDB

**Version:** 1.0  
**Date:** 2026-04-09  
**Audience:** Thesis readers, developers, architects  

---

## Table of Contents

1. [Overview](#overview)
2. [Why Parquet + DuckDB?](#why-parquet--duckdb)
3. [Data Generation Flow](#data-generation-flow)
4. [Database Schema & Relationships](#database-schema--relationships)
5. [How DuckDB Queries the Data](#how-duckdb-queries-the-data)
6. [File Locations & Code References](#file-locations--code-references)
7. [Data Contracts](#data-contracts)

---

## Overview

### What Is the "Database"?

The system does **NOT use a traditional SQL database server** (no PostgreSQL, MySQL, etc.). Instead:

- **Data is stored as Parquet files** on disk (`data/customers.parquet`, `data/transactions/`, etc.)
- **Queries are executed by DuckDB**, an in-memory SQL query engine
- **Each analytics script spawns its own DuckDB instance**, queries the Parquet files, then exits

This design is **serverless, stateless, and lightweight** — perfect for a thesis project that needs to run on Windows without external dependencies.

### The Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ Data Generation (one-time)                                       │
│  data/generate_synthetic.py creates Parquet files                │
│  └─ customers.parquet (100K rows)                                │
│  └─ loans.parquet (500K rows)                                    │
│  └─ transactions/date=*/*.parquet (10M rows, 365 partitions)     │
│  └─ fraud_labels.parquet (50K rows)                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Query Execution (on-demand, per analytics script)                │
│  Each script: python/customer_360.py, loan_scoring.py, etc.      │
│  1. Create in-memory DuckDB instance                              │
│  2. Execute SQL against Parquet files                             │
│  3. Aggregate results                                             │
│  4. Format as fixed-width record (COBOL contract)                │
│  5. Print to stdout                                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ COBOL Integration (optional)                                     │
│  COBOL programs call analytics scripts via subprocess             │
│  Parse fixed-width output records                                 │
│  Display or aggregate results                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Why Parquet + DuckDB?

### Design Rationale

| Criterion | Choice | Reason |
|-----------|--------|--------|
| **Storage Format** | Apache Parquet | Columnar, compressed, fast SQL-compatible queries |
| **Query Engine** | DuckDB | In-memory, SQL-native, no server setup required |
| **Server** | None (serverless) | Stateless analytics; perfect for thesis/demo |
| **Dependencies** | Minimal (`pip install duckdb pyarrow`) | Works on Windows, macOS, Linux |
| **Data Volume** | 10M+ records | Parquet handles scale efficiently; DuckDB can load in-memory |

### Advantages

✅ **No server to deploy or manage**  
✅ **Fast columnar queries** (DuckDB optimizes for analytical workloads)  
✅ **Compression built-in** (Snappy codec reduces disk footprint)  
✅ **Native partitioning** (Hive-style `date=YYYY-MM-DD/` directory structure)  
✅ **SQL standard** (familiar to any developer)  
✅ **Cross-platform** (same code runs on Windows, Linux, macOS)  

---

## Data Generation Flow

### Step 1: Generate Customers (100K records)

**File:** `data/generate_synthetic.py:39-65`

```python
def generate_customers() -> pd.DataFrame:
    """Generate 100K customer records."""
    customer_ids = [f"C-{i:05d}" for i in range(1, 100_001)]  # C-00001 to C-100000
    names = [fake.name() for _ in range(100_000)]
    dobs = [fake.date_of_birth(minimum_age=18, maximum_age=80) for _ ...]
    cities = [fake.city() for _ in range(100_000)]
    account_open_dates = [...]  # When account was opened (1-15 years ago)
    credit_tiers = rng.choice(['EXCELLENT', 'GOOD', 'FAIR', 'POOR'], ...)
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

**Output:** `data/customers.parquet`

| Field | Type | Range/Distribution |
|-------|------|---------------------|
| customer_id | String | C-00001 to C-100000 (PK) |
| name | String | Faker-generated US names |
| dob | Date | Birth dates (age 18–80) |
| city | String | US cities |
| account_open_date | Date | 1–15 years ago |
| credit_tier | String | EXCELLENT, GOOD, FAIR, POOR |
| email | String | Faker-generated emails |
| monthly_income | Float | ~Normal(4500, 2000) |

---

### Step 2: Generate Loans (500K records)

**File:** `data/generate_synthetic.py:68-101`

```python
def generate_loans(customers_df: pd.DataFrame) -> pd.DataFrame:
    """Generate 500K loan records referencing existing customers."""
    # IMPORTANT: Sample customer IDs from Step 1
    customer_ids = rng.choice(
        customers_df['customer_id'].values,  # ← FROM STEP 1
        500_000,
        replace=True  # Some customers have 0, 1, or multiple loans
    )
    
    loan_ids = [f"L-{i:06d}" for i in range(1, 500_001)]
    amounts = rng.lognormal(mean=9.5, sigma=0.7, size=500_000)  # $10K–$30K typical
    terms = rng.choice([12, 24, 36, 48, 60, 84, 120], ...)  # Months
    rates = rng.uniform(3.5, 24.0, 500_000)  # Interest rates
    statuses = rng.choice(['ACTIVE', 'PAID', 'DEFAULT', 'DELINQUENT'], ...)
    purposes = rng.choice(['HOME', 'AUTO', 'PERS', 'EDUC'], ...)
    
    df = pd.DataFrame({
        'loan_id': loan_ids,
        'customer_id': customer_ids,  # ← FOREIGN KEY (references Step 1)
        'amount': amounts,
        'term': terms,
        'rate': rates,
        'status': statuses,
        'purpose': purposes,
        'origination_date': origination_dates,
        'on_time_payments': on_time_payments,
        'total_payments': total_payments,
        'days_past_due': days_past_due,
    })
    
    pq.write_table(pa.Table.from_pandas(df), "data/loans.parquet", compression='snappy')
```

**Output:** `data/loans.parquet`

**Key Relationship:**
```
loans.customer_id → customers.customer_id (foreign key)
```

Each loan points to a customer created in Step 1. Some customers have 0 loans, others have 10+.

| Field | Type | Relationship |
|-------|------|--------------|
| loan_id | String | L-000001 to L-500000 (PK) |
| customer_id | String | C-00001 to C-100000 (FK → customers) |
| amount | Float | LogNormal(9.5, 0.7) ≈ $10K–$30K |
| term | Integer | 12, 24, 36, 48, 60, 84, 120 months |
| rate | Float | 3.5%–24.0% |
| status | String | ACTIVE, PAID, DEFAULT, DELINQUENT |
| purpose | String | HOME, AUTO, PERS, EDUC |
| origination_date | Date | 10–1825 days ago |
| on_time_payments | Integer | 0 to term |
| total_payments | Integer | 50%–110% of term |
| days_past_due | Integer | 0 or 1–365 days |

---

### Step 3: Generate Transactions (10M records, 365 partitions)

**File:** `data/generate_synthetic.py:104-178`

```python
def generate_transactions(customers_df: pd.DataFrame) -> None:
    """Generate 10M transaction records (27K/day for 365 days)."""
    customer_ids_array = customers_df['customer_id'].values  # ← FROM STEP 1
    cities_array = customers_df['city'].values
    city_map = dict(zip(customer_ids_array, cities_array))  # Map customer → home city
    
    for day_idx in range(365):  # 365 daily partitions
        current_date = start_date + timedelta(days=day_idx)
        
        # Zipf-distributed: some customers transact more frequently
        customer_ids = rng.choice(customer_ids_array, 27_000, replace=True)
        amounts = rng.lognormal(mean=5.5, sigma=1.0, size=27_000)  # ~$250 typical
        merchants_sel = rng.choice(pre_generated_merchants, 27_000)
        mccs_sel = rng.choice(merchant_category_codes, 27_000)
        channels = rng.choice(['POS', 'ATM', 'ONL', 'MOB'], 27_000, p=[0.50, 0.20, 0.20, 0.10])
        
        # Geographic: 90% home city, 10% anomaly (fraud detection signal)
        cities = []
        for cid in customer_ids:
            if rng.random() < 0.1:  # 10% geo anomaly
                cities.append(fake.city())  # Random city
            else:
                cities.append(city_map.get(cid))  # Customer's home city
        
        # Time: business hours weighted (most 10am–6pm, rare at 2am)
        hours = rng.normal(loc=14, scale=4, size=27_000)  # Mean 2pm
        hours = np.clip(hours, 0, 23).astype(int)
        minutes = rng.integers(0, 60, 27_000)
        seconds = rng.integers(0, 60, 27_000)
        timestamps = [datetime(...).isoformat() for ...]
        
        df = pd.DataFrame({
            'txn_id': txn_ids,
            'customer_id': customer_ids,  # ← FOREIGN KEY (references Step 1)
            'amount': amounts,
            'merchant': merchants_sel,
            'mcc': mccs_sel,
            'city': cities,
            'timestamp': timestamps,
            'channel': channels,
            'date': [current_date] * 27_000,
        })
        
        # Write to date-partitioned directory
        partition_dir = Path(f"data/transactions/date={current_date}")
        partition_dir.mkdir(exist_ok=True)
        pq.write_table(pa.Table.from_pandas(df), partition_dir / "part-0000.parquet", compression='snappy')
```

**Output:** `data/transactions/date=YYYY-MM-DD/*.parquet` (365 directories, each with ~27K rows)

**Key Relationship:**
```
transactions.customer_id → customers.customer_id (foreign key)
transactions.date = Hive partition key (for efficient filtering)
```

| Field | Type | Relationship |
|-------|------|--------------|
| txn_id | String | T-00000001 to T-10000000 (PK) |
| customer_id | String | C-00001 to C-100000 (FK → customers) |
| amount | Float | LogNormal(5.5, 1.0) ≈ $250 typical |
| merchant | String | Company name (1000 unique) |
| mcc | String | 4-digit merchant category code |
| city | String | 90% customer's home city, 10% random (anomaly) |
| timestamp | ISO8601 | Date + time (hour ≈ Normal(14, 4)) |
| channel | String | POS (50%), ATM (20%), ONL (20%), MOB (10%) |
| date | Date | Partition key: YYYY-MM-DD |

**Why Partitioning Matters:**
```
├── date=2025-01-01/part-0000.parquet  (27K rows)
├── date=2025-01-02/part-0000.parquet  (27K rows)
├── ...
└── date=2025-12-31/part-0000.parquet  (27K rows)
```

DuckDB uses **Hive partitioning** — it automatically prunes directories based on WHERE clauses:
```sql
SELECT * FROM read_parquet('transactions/date=*/part-*.parquet', hive_partitioning=true)
WHERE customer_id = 'C-00001' AND date >= '2025-06-01'
-- DuckDB only reads: transactions/date=2025-06-01/ through date=2025-12-31/
-- Skips: date=2025-01-01/ through date=2025-05-31/
```

---

### Step 4: Generate Fraud Labels (50K records)

**File:** `data/generate_synthetic.py:181-200`

```python
def generate_fraud_labels() -> None:
    """Generate fraud labels for sample transactions."""
    # Create 50K random transaction IDs (some may not exist in actual txn table)
    txn_ids = [f"T-{rng.integers(0, 10_000_000):08d}" for _ in range(50_000)]
    
    is_fraud = rng.choice([True, False], 50_000, p=[0.15, 0.85])  # 15% fraud rate
    fraud_types = rng.choice(['CARD_NOT_PRESENT', 'ACCOUNT_TAKEOVER', 'IDENTITY_THEFT', 'NONE'], ...)
    detection_methods = rng.choice(['RULE_BASED', 'ML_MODEL', 'MANUAL_REVIEW'], ...)
    
    df = pd.DataFrame({
        'txn_id': txn_ids,
        'is_fraud': is_fraud,
        'fraud_type': fraud_types,
        'detection_method': detection_methods,
    })
    
    pq.write_table(pa.Table.from_pandas(df), "data/fraud_labels.parquet", compression='snappy')
```

**Output:** `data/fraud_labels.parquet`

**Key Relationship:**
```
fraud_labels.txn_id → transactions.txn_id (foreign key, sparse)
```

Not all transactions have fraud labels; this table is a sample of 50K labeled examples.

| Field | Type | Relationship |
|-------|------|--------------|
| txn_id | String | T-00000001 to T-10000000 (FK → transactions) |
| is_fraud | Boolean | 15% true, 85% false |
| fraud_type | String | CARD_NOT_PRESENT, ACCOUNT_TAKEOVER, IDENTITY_THEFT, NONE |
| detection_method | String | RULE_BASED, ML_MODEL, MANUAL_REVIEW |

---

## Database Schema & Relationships

### Entity-Relationship Diagram

```
┌──────────────────────────────────────────────────────────────┐
│ CUSTOMERS (100K rows)                                        │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ customer_id (PK) │ name │ city │ monthly_income │ ... │  │
│ │ C-00001          │ John │ NYC  │ $3,500         │ ... │  │
│ │ C-00002          │ Mary │ LA   │ $4,200         │ ... │  │
│ │ ... (100K total)                                        │  │
│ └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
           ▲                              ▲
           │ (1:many)                    │ (1:many)
           └─────────────┬────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                 │
        ▼                                 ▼
┌────────────────────┐        ┌──────────────────────────────────┐
│ LOANS (500K rows)  │        │ TRANSACTIONS (10M rows)          │
│ ┌────────────────┐ │        │ ┌──────────────────────────────┐ │
│ │ loan_id (PK)   │ │        │ │ txn_id (PK)                  │ │
│ │ customer_id    │ │        │ │ customer_id (FK)             │ │
│ │ (FK) ──────────┼─┼────────┼─┼→ customer_id (from Step 1)   │ │
│ │ amount, term   │ │        │ │ amount, merchant, mcc        │ │
│ │ rate, status   │ │        │ │ city, timestamp, channel     │ │
│ │ purpose        │ │        │ │ date (partition key)         │ │
│ │ origination    │ │        │ │ [Hive partitioned by date]   │ │
│ │ ... (500K)     │ │        │ │ ... (10M total, 365 parts)   │ │
│ └────────────────┘ │        │ └──────────────────────────────┘ │
└────────────────────┘        └──────────────────────────────────┘
                                           ▲
                                           │ (1:many)
                                           │
                        ┌──────────────────┴──────────────────┐
                        │ FRAUD_LABELS (50K rows)             │
                        │ ┌────────────────────────────────┐  │
                        │ │ txn_id (FK, sparse)            │  │
                        │ │ → txn_id (from Step 3)         │  │
                        │ │ is_fraud (boolean)             │  │
                        │ │ fraud_type, detection_method   │  │
                        │ │ ... (50K labeled examples)     │  │
                        │ └────────────────────────────────┘  │
                        └────────────────────────────────────┘
```

### Key-Value Relationships

| Relationship | Type | Notes |
|--------------|------|-------|
| customers.customer_id | PK | Unique identifier; C-00001 to C-100000 |
| loans.customer_id | FK | References customers.customer_id; many loans per customer |
| transactions.customer_id | FK | References customers.customer_id; many txns per customer |
| fraud_labels.txn_id | FK | References transactions.txn_id; sparse (50K of 10M) |
| transactions.date | Partition Key | Hive-style: `date=YYYY-MM-DD` |

---

## How DuckDB Queries the Data

### Concept: In-Memory SQL

When a Python script runs, it:

1. **Creates a fresh DuckDB instance** in memory (no disk I/O)
2. **Executes SQL queries** against Parquet files
3. **DuckDB loads only needed rows** (predicate pushdown)
4. **Results returned to Python** as rows
5. **Script exits** (DuckDB instance garbage collected)

### Example 1: Customer 360 Query

**File:** `python/utils/parquet_reader.py:31-54` and `python/customer_360.py`

```python
from python.utils.parquet_reader import get_connection, query_customer, query_transactions_agg

conn = get_connection()  # Create in-memory DuckDB instance

# Query 1: Get customer info
customer = query_customer(conn, "C-00001")
# Executes:
# SELECT * FROM read_parquet('data/customers.parquet') WHERE customer_id = 'C-00001'
# Returns: {'customer_id': 'C-00001', 'name': 'John Smith', 'city': 'NYC', ...}

# Query 2: Get transaction aggregates
txn_agg = query_transactions_agg(conn, "C-00001")
# Executes:
# SELECT
#     COUNT(*) as txn_count,
#     SUM(amount) as total_amount,
#     AVG(amount) as avg_amount,
#     STDDEV_POP(amount) as std_amount,
#     MAX(amount) as max_amount,
#     MIN(amount) as min_amount,
#     MAX(date) as last_txn_date
# FROM read_parquet('data/transactions/date=*/part-*.parquet', hive_partitioning=true)
# WHERE customer_id = 'C-00001'
# Returns: {'txn_count': 1247, 'total_amount': 45231.92, 'avg_amount': 36.34, ...}

# Query 3: Get loans
loans = query_loans(conn, "C-00001")
# Executes:
# SELECT * FROM read_parquet('data/loans.parquet') WHERE customer_id = 'C-00001'
# Returns: [{'loan_id': 'L-000042', 'amount': 25000, ...}, ...]

# Aggregate data + format as 145-byte COBOL record
output = format_output(customer, txn_agg, loans)

# Print to stdout (captured by COBOL or UI)
print(output)  # 145 bytes
```

**What Makes This Efficient:**

1. **Partition Pruning:** DuckDB skips `date=2025-01-01/` directories if query filters for later dates
2. **Column Projection:** DuckDB only reads columns used in SELECT (not the entire row)
3. **Predicate Pushdown:** WHERE clause applied at file read time (not in-memory filtering)
4. **Compression:** Parquet files are Snappy-compressed; DuckDB decompresses on-the-fly

### Example 2: Loan Scoring Query

**File:** `python/loan_scoring.py`

```python
# Calculate credit score based on:
# 1. Payment history: loans.on_time_payments / loans.total_payments
# 2. Credit utilization: txn amounts vs. customer monthly_income
# 3. Credit length: customer account_open_date
# 4. New credit: recent loans (origination_date)
# 5. Credit mix: loan purposes (HOME, AUTO, PERS, EDUC)

customer = query_customer(conn, customer_id)
loans = query_loans(conn, customer_id)
txn_agg = query_transactions_agg(conn, customer_id)

# Extract values and compute credit score
payment_history_score = (loans['on_time_payments'] / loans['total_payments']) * 100
credit_utilization_score = (txn_agg['avg_amount'] / customer['monthly_income']) * 100
# ... more calculations

# Credit score formula (FICO-like, 300–850)
credit_score = calculate_credit_score(payment_history_score, credit_utilization_score, ...)

# Determine eligibility: score >= 650 AND DTI < 0.43 AND no recent defaults
eligible = (credit_score >= 650) and (dti_ratio < 0.43) and (days_past_due == 0)

# Return 51-byte COBOL record
```

### Example 3: Fraud Detection Query

**File:** `python/fraud_detect.py`

```python
# Detect fraud based on:
# 1. Amount anomaly: 3σ above customer's average
# 2. Geo anomaly: location != customer's home city
# 3. Velocity: too many txns in short time
# 4. Category anomaly: MCC never seen before
# 5. Time-of-day: unusual hour (e.g., 3am)

customer = query_customer(conn, customer_id)
txn_agg = query_transactions_agg(conn, customer_id)

# Check amount anomaly
mean_amount = txn_agg['avg_amount']
std_amount = txn_agg['std_amount']
if amount > mean_amount + 3 * std_amount:
    flags.append('AMOUNT_ANOMALY')

# Check geo anomaly
if location != customer['city']:
    flags.append('GEO_ANOMALY')

# Check velocity (recent_24h transactions)
if recent_24h_count > customer['monthly_income'] / 1000:
    flags.append('VELOCITY')

# ... more checks

# Determine risk level
risk_level = 'LOW' if len(flags) == 0 else 'MEDIUM' if len(flags) < 3 else 'HIGH'
fraud_score = len(flags) * 20  # Simplistic: 1 flag = 20 points

# Return 78-byte COBOL record
```

---

## File Locations & Code References

### Data Generation

| File | Lines | Purpose |
|------|-------|---------|
| `data/generate_synthetic.py` | 1–227 | Main data generation script |
| `data/generate_synthetic.py:39–65` | `generate_customers()` | Create 100K customer records |
| `data/generate_synthetic.py:68–101` | `generate_loans()` | Create 500K loan records (ref: customers) |
| `data/generate_synthetic.py:104–178` | `generate_transactions()` | Create 10M transaction records (ref: customers, partitioned by date) |
| `data/generate_synthetic.py:181–200` | `generate_fraud_labels()` | Create 50K fraud labels (ref: transactions) |

### Query Utilities (Using DuckDB)

| File | Lines | Purpose |
|------|-------|---------|
| `python/utils/parquet_reader.py` | 1–227+ | DuckDB query helpers |
| `python/utils/parquet_reader.py:18–28` | `get_connection()` | Create in-memory DuckDB instance |
| `python/utils/parquet_reader.py:31–54` | `query_customer()` | Query customers.parquet by ID |
| `python/utils/parquet_reader.py:57–100+` | `query_transactions_agg()` | Aggregate transactions for a customer (with Hive partitioning) |
| `python/utils/parquet_reader.py:...` | `query_loans()` | Query loans.parquet by customer ID |
| `python/utils/parquet_reader.py:...` | `query_fraud_labels()` | Query fraud_labels.parquet |

### Analytics Scripts (Using Query Utilities)

| File | Purpose | Queries Used |
|------|---------|--------------|
| `python/customer_360.py` | 360° customer view | `query_customer()`, `query_transactions_agg()`, `query_loans()` |
| `python/loan_scoring.py` | Loan eligibility | `query_customer()`, `query_loans()`, `query_transactions_agg()` |
| `python/fraud_detect.py` | Fraud assessment | `query_customer()`, `query_transactions_agg()`, `query_fraud_labels()` |

---

## Data Contracts

### Parquet File Specifications

#### customers.parquet

| Column | Type | Size | Example |
|--------|------|------|---------|
| customer_id | String | — | C-00001 |
| name | String | — | John Smith |
| dob | Date | — | 1980-05-15 |
| city | String | — | New York |
| account_open_date | Date | — | 2015-03-20 |
| credit_tier | String | — | GOOD |
| email | String | — | john.smith@example.com |
| monthly_income | Float64 | — | 4567.89 |

**File Size:** ~4.5 MB (compressed Snappy)  
**Row Count:** 100,000  
**Primary Key:** customer_id  

---

#### loans.parquet

| Column | Type | Size | Example |
|--------|------|------|---------|
| loan_id | String | — | L-000042 |
| customer_id | String | — | C-00001 |
| amount | Float64 | — | 25000.00 |
| term | Int32 | — | 36 |
| rate | Float64 | — | 4.50 |
| status | String | — | ACTIVE |
| purpose | String | — | AUTO |
| origination_date | Date | — | 2023-06-15 |
| on_time_payments | Int32 | — | 24 |
| total_payments | Int32 | — | 36 |
| days_past_due | Int32 | — | 0 |

**File Size:** ~15 MB (compressed Snappy)  
**Row Count:** 500,000  
**Primary Key:** loan_id  
**Foreign Key:** customer_id → customers.customer_id  

---

#### transactions/date=YYYY-MM-DD/*.parquet (365 partitions)

| Column | Type | Size | Example |
|--------|------|------|---------|
| txn_id | String | — | T-00000001 |
| customer_id | String | — | C-00001 |
| amount | Float64 | — | 234.56 |
| merchant | String | — | Walmart Inc. |
| mcc | String | — | 5411 |
| city | String | — | New York |
| timestamp | String (ISO8601) | — | 2025-01-15T14:30:00 |
| channel | String | — | POS |
| date | Date | — | 2025-01-15 |

**Total Size:** ~50 MB (compressed Snappy, all 365 partitions)  
**Row Count:** 10,000,000 (27K/day × 365 days)  
**Primary Key:** txn_id  
**Foreign Key:** customer_id → customers.customer_id  
**Partition Key:** date (Hive-style: `date=2025-01-01/`, `date=2025-01-02/`, etc.)  

---

#### fraud_labels.parquet

| Column | Type | Size | Example |
|--------|------|------|---------|
| txn_id | String | — | T-00000001 |
| is_fraud | Boolean | — | false |
| fraud_type | String | — | CARD_NOT_PRESENT |
| detection_method | String | — | RULE_BASED |

**File Size:** ~482 KB (compressed Snappy)  
**Row Count:** 50,000  
**Foreign Key:** txn_id → transactions.txn_id (sparse; not all txns have labels)  

---

## Summary

### Key Takeaways

1. **No database server** — Parquet files on disk + DuckDB in memory
2. **Data generation** — 4-step process: customers → loans → transactions → fraud_labels
3. **Relationships** — Foreign keys via customer_id and txn_id
4. **Querying** — Each script creates fresh DuckDB instance, executes SQL, exits
5. **Efficiency** — Partition pruning + column projection + predicate pushdown
6. **Reproducibility** — Fixed seeds (42) for Faker and NumPy; same data every run

### For Thesis Writing

**Chapter 3 (System Design):**
- Explain why Parquet + DuckDB (serverless, cross-platform, efficient)
- Data relationships diagram

**Chapter 4 (Implementation):**
- Data generation workflow (4 steps, customer → loan → transaction → fraud label)
- DuckDB query patterns (aggregate, join, filter)
- Code references for each step

**Chapter 5 (Methodology):**
- Data scale: 100K customers, 500K loans, 10M transactions, 50K fraud labels
- Synthetic data generation (Faker, NumPy, distributions)
- Query performance (partition pruning, compression)

**Appendix C (Data Contracts):**
- Parquet schema tables (column names, types, examples)
- Foreign key relationships
- File locations

