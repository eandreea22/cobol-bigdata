#!/usr/bin/env python3
"""
Batch Fraud Analysis

Scores ALL transactions for a customer in a single pass.

Usage:
    python3 fraud_batch_analysis.py <customer_id>

Output (pipe-delimited, stdout):
    Line 1 (summary):
        total|high_count|medium_count|low_count

    Lines 2..N (one per transaction, ordered newest-first):
        txn_id|date|amount|mcc|city|channel|score|risk|recommendation|is_fraud

    is_fraud: "true", "false", or "unknown" (when no label record exists)

Return codes:
    0  = success (even if 0 transactions — returns "0|0|0|0")
    99 = unhandled exception
"""

import sys
from pathlib import Path

# Add project python/ dir to import path
sys.path.insert(0, str(Path(__file__).parent))

import duckdb
from utils.parquet_reader import get_connection, query_transactions_agg
from fraud_detect import compute_fraud_score, classify_fraud_risk


def main():
    # ── Parse arguments ──────────────────────────────────
    if len(sys.argv) < 2:
        print("Error: customer_id required", file=sys.stderr)
        sys.exit(99)

    customer_id = sys.argv[1].strip()

    try:
        # ── Create connection and get baseline stats ──────
        conn = get_connection()

        # Compute baseline stats ONCE (reused for all transactions)
        txn_stats = query_transactions_agg(conn, customer_id)

        # ── Fast path: no transactions ───────────────────
        if txn_stats["txn_count"] == 0:
            print("0|0|0|0")
            sys.exit(0)

        # ── Fetch ALL transactions ───────────────────────
        DATA_ROOT = Path(__file__).parent.parent / "data"
        txn_glob = str(DATA_ROOT / "transactions" / "date=*" / "*.parquet")

        rows = conn.execute(
            """
            SELECT txn_id, date, amount, mcc, city, channel, timestamp
            FROM read_parquet(?, hive_partitioning=true)
            WHERE customer_id = ?
            ORDER BY timestamp DESC
            """,
            [txn_glob, customer_id]
        ).fetchall()

        # ── Bulk JOIN with fraud labels ──────────────────
        LABELS_PATH = str(DATA_ROOT / "fraud_labels.parquet")

        # Build set of txn_ids
        txn_ids = [r[0] for r in rows]

        # Bulk label lookup
        label_map = {}
        if txn_ids:
            placeholders = ", ".join("?" * len(txn_ids))
            label_rows = conn.execute(
                f"SELECT txn_id, is_fraud FROM read_parquet(?) WHERE txn_id IN ({placeholders})",
                [LABELS_PATH] + txn_ids
            ).fetchall()
            label_map = {r[0]: r[1] for r in label_rows}

        # ── Score each transaction ───────────────────────
        high_count = medium_count = low_count = 0
        output_lines = []

        for row in rows:
            txn_id, date, amount, mcc, city, channel, timestamp = row

            # Format date
            date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)[:10]

            # Score transaction
            score, flags = compute_fraud_score(
                amount=float(amount),
                mcc=str(mcc),
                location=str(city),
                timestamp=str(timestamp),
                txn_stats=txn_stats
            )

            # Classify risk
            risk_raw, recommendation_raw = classify_fraud_risk(score)
            risk = risk_raw.strip()
            recommendation = recommendation_raw.strip()

            # Ground-truth label
            if txn_id in label_map:
                is_fraud = "true" if label_map[txn_id] else "false"
            else:
                is_fraud = "unknown"

            # Tally by risk
            if risk == "HIGH":
                high_count += 1
            elif risk == "MEDIUM":
                medium_count += 1
            else:
                low_count += 1

            # Sanitize city (remove pipes)
            city_safe = str(city).replace('|', ' ')

            # Build output line
            output_lines.append(
                f"{txn_id}|{date_str}|{float(amount):.2f}|{mcc}|{city_safe}|{channel}"
                f"|{score}|{risk}|{recommendation}|{is_fraud}"
            )

        # ── Emit output ──────────────────────────────────
        total = len(rows)
        print(f"{total}|{high_count}|{medium_count}|{low_count}")

        for line in output_lines:
            print(line)

        sys.exit(0)

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(99)

    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == '__main__':
    main()
