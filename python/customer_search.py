#!/usr/bin/env python3
"""
Customer Search by Last Name

Searches customers.parquet for records matching a last name (partial or full).
Returns up to 50 matching customers sorted by name.

Output: pipe-delimited records
<count>
<customer_id>|<name>|<city>|<email>
...

Invocation: python3 customer_search.py <last_name>
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.parquet_reader import get_connection

# Configure logging (stderr only, stdout reserved for IPC output)
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


def sanitize(value: str) -> str:
    """Replace pipe character with space to preserve delimiter integrity."""
    return value.replace('|', ' ').strip() if value else ""


def search_customers(last_name: str, max_results: int = 50) -> list[dict]:
    """
    Search customers.parquet by last name (partial or full match).

    Query logic:
    - Case-insensitive match on 'name' field
    - WHERE lower(name) LIKE lower('% ' || last_name) OR lower(name) = lower(last_name)

    Returns: list of dicts with keys: customer_id, name, city, email (max 50 results)
    """
    try:
        conn = get_connection()

        # Escape single quotes in input
        escaped_name = last_name.replace("'", "''")

        # Query: match names ending with " LastName" or exactly matching the search term
        query = f"""
        SELECT customer_id, name, city, email
        FROM '{Path(__file__).parent.parent / "data" / "customers.parquet"}'
        WHERE lower(name) LIKE lower('%{escaped_name}%')
        ORDER BY name
        LIMIT {max_results}
        """

        result = conn.execute(query).fetchall()

        # Convert tuples to dicts
        rows = []
        for row in result:
            rows.append({
                'customer_id': row[0],
                'name': row[1],
                'city': row[2],
                'email': row[3]
            })

        return rows

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise


def main():
    """Parse arguments and output search results."""
    if len(sys.argv) < 2:
        logger.error("Usage: customer_search.py <last_name>")
        sys.exit(99)

    last_name = sys.argv[1].strip()

    if not last_name:
        logger.error("Last name cannot be empty")
        sys.exit(99)

    try:
        results = search_customers(last_name)

        # Output format:
        # <count>
        # <customer_id>|<name>|<city>|<email>
        # ...

        print(len(results))
        for row in results:
            cid = sanitize(row['customer_id'])
            name = sanitize(row['name'])
            city = sanitize(row['city'])
            email = sanitize(row['email'])

            print(f"{cid}|{name}|{city}|{email}")

        sys.exit(0)

    except Exception as e:
        logger.error(f"Error: {e}")
        print("0")  # Return 0 results on error
        sys.exit(99)


if __name__ == '__main__':
    main()
