#!/usr/bin/env python3
"""
Fraud Detection Scoring

Accepts transaction details and returns fraud risk assessment:
- Fraud risk level (LOW, MEDIUM, HIGH)
- Fraud score (0-100)
- Fraud flags (comma-separated anomalies detected)
- Recommendation (APPROVE, REVIEW, DECLINE)

Anomaly scoring:
  - Amount anomaly (> 3σ): 35 points
  - Geographic anomaly: 25 points
  - High velocity (1h): 20 points
  - High velocity (24h): 10 points
  - New merchant category: 15 points
  - Unusual time-of-day: 5 points

Output: 78-byte fixed-width record to stdout
Return codes: 00=success, 99=error

Invocation: python3 fraud_detect.py <customer_id> <amount> <mcc> <location> <timestamp> <channel>
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.ipc_formatter import format_pic_x, format_pic_9
from utils.parquet_reader import get_connection, query_transactions_agg

logging.basicConfig(
    level=logging.ERROR,
    format='%(name)s: %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


def compute_fraud_score(amount: float, mcc: str, location: str, timestamp: str,
                       txn_stats: dict) -> tuple[int, list[str]]:
    """
    Compute fraud score (0-100) and list of triggered flags.

    Additive scoring system with multiple checks.
    """
    score = 0
    flags = []

    # ============ Check 1: Amount Anomaly ============
    if txn_stats["std_amount"] > 0:
        z_score = (amount - txn_stats["avg_amount"]) / txn_stats["std_amount"]
        if z_score > 3:  # More than 3 standard deviations
            score += 35
            flags.append("AMOUNT_ANOMALY")

    # ============ Check 2: Geographic Anomaly ============
    # Customer has never transacted in this location
    if location not in txn_stats["locations"]:
        score += 25
        flags.append("GEO_ANOMALY")

    # ============ Check 3: Velocity - Last 1 Hour ============
    if txn_stats["recent_1h"] >= 5:
        score += 20
        flags.append("HIGH_VELOCITY_1H")
    elif txn_stats["recent_1h"] >= 3:
        score += 10
        flags.append("MEDIUM_VELOCITY_1H")

    # ============ Check 4: Velocity - Last 24 Hours ============
    if txn_stats["recent_24h"] >= 20:
        score += 10
        flags.append("HIGH_VELOCITY_24H")

    # ============ Check 5: Category Anomaly ============
    # Customer has never transacted in this MCC
    if mcc not in txn_stats["mccs"]:
        score += 15
        flags.append("NEW_MERCHANT_CAT")

    # ============ Check 6: Time-of-Day Analysis ============
    try:
        txn_hour = datetime.fromisoformat(timestamp).hour
        if txn_hour < 6 or txn_hour > 23:
            score += 5
            flags.append("UNUSUAL_HOUR")
    except (ValueError, TypeError):
        logger.warning(f"Invalid timestamp format: {timestamp}")
        score += 5
        flags.append("INVALID_TIMESTAMP")

    # Cap score at 100
    score = min(score, 100)

    return score, flags


def classify_fraud_risk(score: int) -> tuple[str, str]:
    """
    Classify fraud risk level and recommendation based on score.

    Returns: (risk_level, recommendation)
    """
    if score >= 70:
        return "HIGH  ", "DECLINE"
    elif score >= 40:
        return "MEDIUM", "REVIEW "
    else:
        return "LOW   ", "APPROVE"


def build_response_record(fraud_risk: str, fraud_score: int, fraud_flags: str,
                         recommend: str, return_code: str) -> str:
    """
    Build the 78-byte response record.

    Byte layout:
      1-6:    Fraud risk level (PIC X(6), "LOW   ", "MEDIUM", "HIGH  ")
      7-9:    Fraud score (PIC 9(3), 0-100, zero-padded)
      10-69:  Fraud flags (PIC X(60), comma-separated)
      70-76:  Recommendation (PIC X(7), "APPROVE", "REVIEW ", "DECLINE")
      77-78:  Return code (PIC 99)
    """
    record = (
        format_pic_x(fraud_risk, 6)            # bytes 1-6 (6 chars)
        + format_pic_9(fraud_score, 3)         # bytes 7-9 (3 chars)
        + format_pic_x(fraud_flags, 60)        # bytes 10-69 (60 chars)
        + format_pic_x(recommend, 7)           # bytes 70-76 (7 chars)
        + format_pic_x(return_code, 2)         # bytes 77-78 (2 chars)
    )

    assert len(record) == 78, f"Record length {len(record)} != 78"
    return record


def main():
    """Main entry point."""
    try:
        # Parse arguments
        if len(sys.argv) < 7:
            logger.error("Usage: python3 fraud_detect.py <customer_id> <amount> <mcc> <location> <timestamp> <channel>")
            sys.stdout.write(build_response_record("UNKNOW", 0, "", "REVIEW ", "99") + "\n")
            sys.exit(1)

        customer_id = sys.argv[1].strip()
        try:
            amount = float(sys.argv[2].strip())
            mcc = sys.argv[3].strip()
            location = sys.argv[4].strip()
            timestamp = sys.argv[5].strip()
            channel = sys.argv[6].strip()
        except (ValueError, IndexError):
            logger.error("Invalid argument format")
            sys.stdout.write(build_response_record("UNKNOW", 0, "", "REVIEW ", "99") + "\n")
            sys.exit(1)

        # Create DuckDB connection
        conn = get_connection()

        try:
            # Query transaction aggregates for customer
            txn_stats = query_transactions_agg(conn, customer_id)

            # Handle case where customer has no transaction history
            if txn_stats["txn_count"] == 0:
                # No history: default to REVIEW
                record = build_response_record("MEDIUM", 50, "NO_HISTORY", "REVIEW ", "00")
                sys.stdout.write(record + "\n")
                sys.stdout.flush()
                return

            # Compute fraud score
            fraud_score, flags = compute_fraud_score(
                amount=amount,
                mcc=mcc,
                location=location,
                timestamp=timestamp,
                txn_stats=txn_stats
            )

            # Classify risk
            risk_level, recommendation = classify_fraud_risk(fraud_score)

            # Build flags string
            flags_str = ",".join(flags) if flags else ""

            # Build response record
            record = build_response_record(
                fraud_risk=risk_level,
                fraud_score=fraud_score,
                fraud_flags=flags_str,
                recommend=recommendation,
                return_code="00"
            )

            # Output record
            sys.stdout.write(record + "\n")
            sys.stdout.flush()

        finally:
            conn.close()

    except Exception as e:
        logger.exception("Unhandled exception in fraud_detect.py")
        sys.stdout.write(build_response_record("UNKNOW", 0, "", "REVIEW ", "99") + "\n")
        sys.stdout.flush()
        sys.exit(1)


if __name__ == "__main__":
    main()
