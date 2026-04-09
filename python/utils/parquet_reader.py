#!/usr/bin/env python3
"""
Parquet Reader: DuckDB-based utilities for querying Parquet data lake.

All Python analytics scripts use these functions to query the synthetic
data in a stateless, composable way.
"""

from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import duckdb

# Data root directory: points to the data/ folder at repo root
DATA_ROOT = Path(__file__).parent.parent.parent / "data"


def get_connection() -> duckdb.DuckDBPyConnection:
    """
    Create and return a fresh in-memory DuckDB connection.

    Each Python script creates its own connection (stateless), so no
    shared state persists across invocations.

    Returns:
        A new DuckDB in-memory connection
    """
    return duckdb.connect(database=":memory:")


def query_customer(conn: duckdb.DuckDBPyConnection, customer_id: str) -> Optional[Dict[str, Any]]:
    """
    Query a single customer record from customers.parquet.

    Args:
        conn: DuckDB connection
        customer_id: Customer ID to look up

    Returns:
        Dictionary with customer data (name, dob, city, account_open_date,
        credit_tier, email, monthly_income) or None if not found
    """
    result = conn.execute(
        "SELECT * FROM read_parquet(?) WHERE customer_id = ?",
        [str(DATA_ROOT / "customers.parquet"), customer_id]
    ).fetchall()

    if not result:
        return None

    # Map to dict (assuming specific column order from generate_synthetic.py)
    cols = ["customer_id", "name", "dob", "city", "account_open_date", "credit_tier", "email", "monthly_income"]
    row = result[0]
    return dict(zip(cols, row))


def query_transactions_agg(conn: duckdb.DuckDBPyConnection, customer_id: str) -> Dict[str, Any]:
    """
    Query and aggregate transaction data for a customer.

    Uses Hive partitioning on the transactions table for efficient partition pruning.

    Args:
        conn: DuckDB connection
        customer_id: Customer ID to analyze

    Returns:
        Dictionary with aggregation results:
        - txn_count: Total number of transactions
        - total_amount: Sum of all transaction amounts
        - avg_amount: Average transaction amount
        - std_amount: Standard deviation of transaction amounts
        - max_amount: Highest single transaction
        - min_amount: Lowest single transaction
        - last_txn_date: Most recent transaction date (YYYY-MM-DD)
        - locations: List of unique transaction cities
        - mccs: List of unique merchant category codes
        - hourly_counts: Dict of hour -> transaction count
        - recent_1h: Transaction count in last hour (simulated)
        - recent_24h: Transaction count in last 24 hours (simulated)
    """
    txn_glob = str(DATA_ROOT / "transactions" / "date=*" / "*.parquet")

    # Main aggregation query
    agg_result = conn.execute(
        """
        SELECT
            COUNT(*) as txn_count,
            SUM(amount) as total_amount,
            AVG(amount) as avg_amount,
            STDDEV_POP(amount) as std_amount,
            MAX(amount) as max_amount,
            MIN(amount) as min_amount,
            MAX(date) as last_txn_date
        FROM read_parquet(?, hive_partitioning=true)
        WHERE customer_id = ?
        """,
        [txn_glob, customer_id]
    ).fetchone()

    if agg_result[0] == 0:  # No transactions
        return {
            "txn_count": 0,
            "total_amount": 0.0,
            "avg_amount": 0.0,
            "std_amount": 0.0,
            "max_amount": 0.0,
            "min_amount": 0.0,
            "last_txn_date": None,
            "locations": [],
            "mccs": [],
            "hourly_counts": {},
            "recent_1h": 0,
            "recent_24h": 0,
        }

    txn_count, total, avg_amt, std_amt, max_amt, min_amt, last_date = agg_result

    # Query for unique locations
    loc_result = conn.execute(
        """
        SELECT DISTINCT city
        FROM read_parquet(?, hive_partitioning=true)
        WHERE customer_id = ?
        ORDER BY city
        """,
        [txn_glob, customer_id]
    ).fetchall()
    locations = [loc[0] for loc in loc_result]

    # Query for unique MCCs
    mcc_result = conn.execute(
        """
        SELECT DISTINCT mcc
        FROM read_parquet(?, hive_partitioning=true)
        WHERE customer_id = ?
        ORDER BY mcc
        """,
        [txn_glob, customer_id]
    ).fetchall()
    mccs = [mcc[0] for mcc in mcc_result]

    # Simulate hourly distribution (extract hour from timestamp)
    # Try to extract hour from timestamp, with fallback if timestamp format differs
    try:
        hourly_result = conn.execute(
            """
            SELECT CAST(STRFTIME(CAST(timestamp AS TIMESTAMP), '%H') AS INTEGER) as hour, COUNT(*) as cnt
            FROM read_parquet(?, hive_partitioning=true)
            WHERE customer_id = ?
            GROUP BY hour
            ORDER BY hour
            """,
            [txn_glob, customer_id]
        ).fetchall()
    except Exception:
        # Fallback: if timestamp casting fails, just use a dummy distribution
        hourly_result = []
    hourly_counts = {hour: cnt for hour, cnt in hourly_result} if hourly_result else {}

    # Recent transaction counts (simulated with row_number since we don't have exact timestamps in all rows)
    # Count transactions in last 7 days (proxy for 1h and 24h patterns)
    recent_result = conn.execute(
        """
        SELECT
            SUM(CASE WHEN date >= CURRENT_DATE - INTERVAL '1 day' THEN 1 ELSE 0 END) as recent_24h,
            SUM(CASE WHEN date >= CURRENT_DATE - INTERVAL '7 days' THEN 1 ELSE 0 END) as recent_7d
        FROM read_parquet(?, hive_partitioning=true)
        WHERE customer_id = ?
        """,
        [txn_glob, customer_id]
    ).fetchone()
    recent_24h = recent_result[0] or 0
    recent_1h = max(0, (recent_24h // 24))  # Rough estimate for 1h

    return {
        "txn_count": int(txn_count),
        "total_amount": float(total or 0),
        "avg_amount": float(avg_amt or 0),
        "std_amount": float(std_amt or 0),
        "max_amount": float(max_amt or 0),
        "min_amount": float(min_amt or 0),
        "last_txn_date": str(last_date) if last_date else "0000-00-00",
        "locations": locations,
        "mccs": mccs,
        "hourly_counts": hourly_counts,
        "recent_1h": recent_1h,
        "recent_24h": recent_24h,
    }


def query_loans(conn: duckdb.DuckDBPyConnection, customer_id: str) -> List[Dict[str, Any]]:
    """
    Query all loan records for a customer from loans.parquet.

    Args:
        conn: DuckDB connection
        customer_id: Customer ID to analyze

    Returns:
        List of loan dictionaries (amount, term, rate, status, purpose,
        origination_date, on_time_payments, total_payments, days_past_due)
    """
    results = conn.execute(
        "SELECT * FROM read_parquet(?) WHERE customer_id = ?",
        [str(DATA_ROOT / "loans.parquet"), customer_id]
    ).fetchall()

    if not results:
        return []

    cols = [
        "loan_id", "customer_id", "amount", "term", "rate", "status",
        "purpose", "origination_date", "on_time_payments", "total_payments", "days_past_due"
    ]

    loans = [dict(zip(cols, row)) for row in results]
    return loans


def query_fraud_labels(conn: duckdb.DuckDBPyConnection, txn_id: str) -> Optional[Dict[str, Any]]:
    """
    Query fraud label data for a specific transaction.

    Args:
        conn: DuckDB connection
        txn_id: Transaction ID to look up

    Returns:
        Dictionary with fraud label info (is_fraud, fraud_type, detection_method) or None
    """
    result = conn.execute(
        "SELECT * FROM read_parquet(?) WHERE txn_id = ?",
        [str(DATA_ROOT / "fraud_labels.parquet"), txn_id]
    ).fetchone()

    if not result:
        return None

    cols = ["txn_id", "is_fraud", "fraud_type", "detection_method"]
    return dict(zip(cols, result))
