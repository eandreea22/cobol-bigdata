#!/usr/bin/env python3
"""
Customer List with Pagination and Filtering

Returns a paginated list of customers with editable fields.
Supports optional name filter for narrowing results.

Output: pipe-delimited records
<total_matching>
<customer_id>|<name>|<email>|<city>|<street>|<balance>|<monthly_income>
...

Invocation: python3 customer_list.py <page> <page_size> [filter]
Example: python3 customer_list.py 1 100 Smith
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.parquet_reader import get_connection

# Configure logging (stderr only)
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


def sanitize(value) -> str:
    """Replace pipe character with space and strip whitespace."""
    if value is None:
        return ""
    s = str(value).replace('|', ' ').strip()
    return s


def format_currency(value: float) -> str:
    """Format numeric value to 2 decimal places."""
    if value is None:
        return "0.00"
    try:
        return f"{float(value):.2f}"
    except (ValueError, TypeError):
        return "0.00"


def fetch_customer_list(page: int, page_size: int, name_filter: str = "") -> tuple[list[dict], int]:
    """
    Fetch paginated customer list with optional name filter.

    Args:
        page: 1-indexed page number
        page_size: number of rows per page
        name_filter: optional substring filter on customer name

    Returns:
        (list of customer dicts, total matching count)
    """
    try:
        conn = get_connection()

        data_dir = Path(__file__).parent.parent / "data"
        customers_file = data_dir / "customers.parquet"
        edits_file = data_dir / "customer_edits.parquet"

        # Build filter WHERE clause
        where_clause = ""
        if name_filter:
            escaped_filter = name_filter.replace("'", "''")
            where_clause = f"WHERE lower(c.name) LIKE lower('%{escaped_filter}%')"

        # Calculate offset (0-indexed)
        offset = (page - 1) * page_size

        # Check if edits file exists
        edits_exist = edits_file.exists()

        # Query: left-join customers with customer_edits (if exists), compute balance
        if edits_exist:
            query = f"""
            SELECT
                c.customer_id,
                c.name,
                c.email,
                c.city,
                COALESCE(e.street, '') as street,
                c.monthly_income * 3 as balance,
                c.monthly_income
            FROM '{customers_file}' c
            LEFT JOIN '{edits_file}' e ON c.customer_id = e.customer_id
            {where_clause}
            ORDER BY c.customer_id
            OFFSET {offset}
            LIMIT {page_size}
            """
        else:
            # If edits file doesn't exist yet, just use customers table
            query = f"""
            SELECT
                c.customer_id,
                c.name,
                c.email,
                c.city,
                '' as street,
                c.monthly_income * 3 as balance,
                c.monthly_income
            FROM '{customers_file}' c
            {where_clause}
            ORDER BY c.customer_id
            OFFSET {offset}
            LIMIT {page_size}
            """

        result = conn.execute(query).fetchall()

        # Convert tuples to dicts
        rows = []
        for row in result:
            rows.append({
                'customer_id': row[0],
                'name': row[1],
                'email': row[2],
                'city': row[3],
                'street': row[4],
                'balance': row[5],
                'monthly_income': row[6]
            })

        # Get total count (with same filter)
        if edits_exist:
            count_query = f"""
            SELECT COUNT(DISTINCT c.customer_id)
            FROM '{customers_file}' c
            LEFT JOIN '{edits_file}' e ON c.customer_id = e.customer_id
            {where_clause}
            """
        else:
            count_query = f"""
            SELECT COUNT(DISTINCT c.customer_id)
            FROM '{customers_file}' c
            {where_clause}
            """
        total = conn.execute(count_query).fetchone()[0]

        return rows, total

    except Exception as e:
        logger.error(f"List fetch failed: {e}")
        raise


def main():
    """Parse arguments and output customer list."""
    if len(sys.argv) < 3:
        logger.error("Usage: customer_list.py <page> <page_size> [name_filter]")
        sys.exit(99)

    try:
        page = int(sys.argv[1])
        page_size = int(sys.argv[2])
        name_filter = sys.argv[3] if len(sys.argv) > 3 else ""

        if page < 1 or page_size < 1:
            logger.error("Page and page_size must be >= 1")
            sys.exit(99)

        rows, total = fetch_customer_list(page, page_size, name_filter)

        # Output format:
        # <total_matching>
        # <customer_id>|<name>|<email>|<city>|<street>|<balance>|<monthly_income>
        # ...

        print(total)
        for row in rows:
            cid = sanitize(row['customer_id'])
            name = sanitize(row['name'])
            email = sanitize(row['email'])
            city = sanitize(row['city'])
            street = sanitize(row['street'])
            balance = format_currency(row['balance'])
            income = format_currency(row['monthly_income'])

            print(f"{cid}|{name}|{email}|{city}|{street}|{balance}|{income}")

        sys.exit(0)

    except Exception as e:
        logger.error(f"Error: {e}")
        print("0")  # Return 0 total on error
        sys.exit(99)


if __name__ == '__main__':
    main()
