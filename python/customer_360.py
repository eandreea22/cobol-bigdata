#!/usr/bin/env python3
"""
Customer 360° Lookup

Accepts a customer ID and returns a comprehensive 360-degree view:
- Customer demographics
- Account balance
- Transaction analytics (count, average spending)
- Risk score (composite metric)

Output: 145-byte fixed-width record to stdout
Return codes: 00=success, 01=not found, 99=error

Invocation: python3 customer_360.py <customer_id>
"""

import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.ipc_formatter import format_pic_x, format_pic_9
from utils.parquet_reader import get_connection, query_customer, query_transactions_agg

# Configure logging (stderr only, stdout reserved for IPC record)
logging.basicConfig(
    level=logging.ERROR,
    format='%(name)s: %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


def compute_risk_score(txn_count: int, avg_amount: float, days_since_last_txn: int) -> int:
    """
    Compute risk score (0-999) based on transaction patterns.

    Higher score = higher risk.

    Factors:
    - Transaction frequency: more frequent = lower risk
    - Average amount: higher amounts = higher risk
    - Recency: older last transaction = higher risk
    """
    score = 0

    # Factor 1: Transaction frequency (0-300 points)
    # Higher frequency = lower risk
    # Target: ~100 txns/year = low risk
    if txn_count == 0:
        score += 300  # No transactions = highest risk
    elif txn_count < 12:
        score += 250  # Very infrequent
    elif txn_count < 50:
        score += 200  # Infrequent
    elif txn_count < 100:
        score += 100  # Moderate
    elif txn_count < 200:
        score += 50   # Frequent
    else:
        score += 10   # Very frequent (low risk)

    # Factor 2: Average amount (0-400 points)
    # Higher average = higher risk
    if avg_amount > 5000:
        score += 400  # Very high average
    elif avg_amount > 2000:
        score += 300  # High average
    elif avg_amount > 1000:
        score += 200  # Moderate-high average
    elif avg_amount > 500:
        score += 100  # Moderate average
    elif avg_amount > 100:
        score += 30   # Low average
    else:
        score += 0    # Very low average

    # Factor 3: Recency (0-300 points)
    # Older last transaction = higher risk
    if days_since_last_txn < 0:
        score += 0    # Transaction in future (invalid, but treat as recent)
    elif days_since_last_txn == 0:
        score += 0    # Today
    elif days_since_last_txn <= 7:
        score += 10   # This week (low risk)
    elif days_since_last_txn <= 30:
        score += 50   # This month
    elif days_since_last_txn <= 90:
        score += 150  # This quarter
    elif days_since_last_txn <= 365:
        score += 250  # This year
    else:
        score += 300  # Dormant account (highest risk)

    # Cap at 999 (max PIC 9(3))
    return min(score, 999)


def build_response_record(name: str, balance: float, txn_count: int, avg_amount: float,
                         risk_score: int, last_txn_date: str, return_code: str) -> str:
    """
    Build the 145-byte response record.

    Byte layout:
      1-50:   Customer name (PIC X(50))
     51-62:   Account balance (PIC 9(10)V99, 12 chars)
     63-70:   Transaction count (PIC 9(8), 8 chars)
     71-80:   Average monthly spending (PIC 9(8)V99, 10 chars)
     81-83:   Risk score (PIC 9(3), 3 chars)
     84-93:   Last transaction date (YYYY-MM-DD, 10 chars)
     94-95:   Return code (PIC 99, 2 chars)
     96-145:  Reserved (50 chars)
    """
    record = (
        format_pic_x(name, 50)                 # bytes 1-50
        + format_pic_9(balance, 10, 2)         # bytes 51-62 (12 chars)
        + format_pic_9(txn_count, 8)           # bytes 63-70 (8 chars)
        + format_pic_9(avg_amount, 8, 2)       # bytes 71-80 (10 chars)
        + format_pic_9(risk_score, 3)          # bytes 81-83 (3 chars)
        + format_pic_x(last_txn_date, 10)      # bytes 84-93
        + format_pic_x(return_code, 2)         # bytes 94-95
        + format_pic_x("", 50)                 # bytes 96-145 (reserved)
    )

    assert len(record) == 145, f"Record length {len(record)} != 145"
    return record


def main():
    """Main entry point."""
    try:
        # Parse arguments
        if len(sys.argv) < 2:
            logger.error("Usage: python3 customer_360.py <customer_id>")
            sys.stdout.write(build_response_record("", 0, 0, 0, 0, "0000-00-00", "99") + "\n")
            sys.exit(1)

        customer_id = sys.argv[1].strip()

        # Create DuckDB connection
        conn = get_connection()

        try:
            # Query customer data
            customer = query_customer(conn, customer_id)
            if customer is None:
                # Customer not found
                record = build_response_record("", 0, 0, 0, 0, "0000-00-00", "01")
                sys.stdout.write(record + "\n")
                sys.stdout.flush()
                return

            # Query transaction aggregates
            txn_agg = query_transactions_agg(conn, customer_id)

            # Compute risk score
            days_since_last = 0
            if txn_agg["last_txn_date"] and txn_agg["last_txn_date"] != "0000-00-00":
                try:
                    last_date = datetime.strptime(txn_agg["last_txn_date"], "%Y-%m-%d").date()
                    days_since_last = (datetime.now().date() - last_date).days
                except (ValueError, TypeError):
                    days_since_last = 999
            else:
                days_since_last = 999

            risk_score = compute_risk_score(
                txn_agg["txn_count"],
                txn_agg["avg_amount"],
                days_since_last
            )

            # Build response record
            record = build_response_record(
                name=customer["name"],
                balance=customer["monthly_income"] * 3,  # Approximate: 3 months savings
                txn_count=txn_agg["txn_count"],
                avg_amount=txn_agg["avg_amount"],
                risk_score=risk_score,
                last_txn_date=txn_agg["last_txn_date"],
                return_code="00"
            )

            # Output record
            sys.stdout.write(record + "\n")
            sys.stdout.flush()

        finally:
            conn.close()

    except Exception as e:
        logger.exception("Unhandled exception in customer_360.py")
        # Return error record (return code 99)
        sys.stdout.write(build_response_record("", 0, 0, 0, 0, "0000-00-00", "99") + "\n")
        sys.stdout.flush()
        sys.exit(1)


if __name__ == "__main__":
    main()
