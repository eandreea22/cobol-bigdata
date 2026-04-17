# Data Layer Reference

## Architecture Decision

**Why DuckDB + Parquet?**
- **No server**: In-process SQL engine, zero operations overhead
- **Parquet columnar format**: 10:1 compression vs CSV
- **Hive partitioning**: Automatic date-based partition pruning
- **Python integration**: Seamless PyArrow bindings
- **Scale proven**: 10M transactions on laptop hardware, <2sec full-scan

---

## Datasets

| Dataset | Records | Format | Partitioning |
|---------|---------|--------|---|
| customers.parquet | 100,000 | Snappy Parquet | None |
| loans.parquet | 500,000 | Snappy Parquet | None |
| transactions/ | 10,000,000 | Hive-partitioned | date=YYYY-MM-DD |
| fraud_labels.parquet | 50,000 | Snappy Parquet | None |

**Schemas:**
- customers: customer_id (PK), name, dob, city, account_open_date, credit_tier, email, monthly_income
- loans: loan_id (PK), customer_id (FK), amount, term, rate, status, purpose, origination_date, on_time_payments, total_payments, days_past_due
- transactions: txn_id (PK), customer_id (FK), amount, merchant, mcc, city, timestamp, channel, date (partition key)
- fraud_labels: txn_id (FK, soft), is_fraud, fraud_type, detection_method

---

## Generation & Reproducibility

**Fixed seeds (FAKE_SEED=42, RNG_SEED=42):**
- Ensures identical datasets across all runs
- Enables reproducible benchmarks
- Suitable for thesis appendix

**Disk size:** customers (50MB) + loans (150MB) + transactions (1GB) + fraud_labels (10MB) = **~1.2GB total**

---

## Hive Partitioning

**Benefits:**
- Automatic partition pruning: date range queries skip irrelevant directories
- 75% I/O reduction for quarterly queries
- 365 daily files instead of single monolithic file

**Query example:**
```python
df = duckdb.sql("""
    SELECT * FROM read_parquet('data/transactions/*/*.parquet', hive_partitioning=true)
    WHERE date >= '2025-01-01' AND date < '2025-04-01'
""")
# DuckDB scans only Q1 files automatically
```

---

## Performance Baselines

| Query | P50 Latency | Bottleneck |
|-------|---|---|
| Customer lookup (1 record) | 5ms | Parquet seek |
| Customer aggregate (10K txns) | 50ms | Decompression |
| Full scan (10M txns) | 2000ms | I/O + decompression |

---

**Last Updated:** 2026-04-17
