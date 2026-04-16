#!/usr/bin/env python3
"""
Fetch ALL transactions for a customer from Parquet data (no limit).

Usage:
    python3 customer_transactions.py <customer_id>

Example:
    python3 customer_transactions.py C-00001

Output (pipe-delimited, 8 fields):
    <count>
    <txn_id>|<date>|<time>|<amount>|<merchant>|<mcc>|<city>|<channel>
    ...

where <time> is HH:MM extracted from timestamp.

Error Cases:
    - Customer not found: count=0 (empty list)
    - Query error: error message to stderr, exit code 99
"""

import sys
import duckdb

def main():
    # Parse arguments
    if len(sys.argv) < 2:
        print("Error: customer_id required", file=sys.stderr)
        sys.exit(99)

    customer_id = sys.argv[1].strip()

    try:
        # Connect to DuckDB
        conn = duckdb.connect(':memory:')

        # Query ALL transactions for this customer, newest first
        result = conn.execute("""
            SELECT
                txn_id,
                date,
                strftime(CAST(timestamp AS TIMESTAMP), '%H:%M') AS time,
                amount,
                merchant,
                mcc,
                city,
                channel
            FROM 'data/transactions/*/part-0000.parquet'
            WHERE customer_id = ?
            ORDER BY timestamp DESC
        """, [customer_id]).fetchall()

        # Output format: count as first line
        print(len(result))

        # Then output each transaction as pipe-delimited (8 fields)
        for row in result:
            txn_id, date, time, amount, merchant, mcc, city, channel = row

            # Format date as YYYY-MM-DD if it's a date object
            if hasattr(date, 'strftime'):
                date_str = date.strftime('%Y-%m-%d')
            else:
                date_str = str(date)[:10]

            # Format amount as decimal
            amount_str = f"{amount:.2f}"

            # Clean strings (remove pipes to avoid parsing issues)
            merchant = str(merchant).replace('|', ' ')
            city = str(city).replace('|', ' ')

            # Output pipe-delimited row (8 fields)
            print(f"{txn_id}|{date_str}|{time}|{amount_str}|{merchant}|{mcc}|{city}|{channel}")

        sys.exit(0)

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(99)


if __name__ == '__main__':
    main()
