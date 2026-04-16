#!/usr/bin/env python3
"""
Customer Update with COBOL Validation

Updates customer record in customers.parquet and optionally customer_edits.parquet.
Optional: invokes COBOL/customer-update for business-rule validation (if compiled).

Input args:
  <customer_id> <name> <email> <city> <street> <monthly_income>

Output: <return_code>|<message>
  00 = success
  01 = validation error
  99 = system error

Invocation: python3 customer_update.py C-00001 "John Smith" "john@example.com" "NYC" "123 Main St" 5000
"""

import sys
import logging
import re
import subprocess
import tempfile
from pathlib import Path
from struct import pack

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.ipc_formatter import format_pic_x, format_pic_9
from utils.parquet_reader import get_connection

# Configure logging (stderr only)
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


def validate_fields(customer_id: str, name: str, email: str, city: str, street: str, income_str: str) -> tuple[bool, str]:
    """
    Python-level field validation.

    Returns: (is_valid, error_message)
    """
    # Customer ID format: C-XXXXX
    if not re.match(r'^C-\d{5}$', customer_id):
        return False, "Customer ID must match format C-XXXXX"

    # Name: 2-100 chars, not blank
    if not name or len(name.strip()) < 2 or len(name) > 100:
        return False, "Name must be 2-100 characters"

    # Email: contains @, 5-200 chars
    if '@' not in email or len(email) < 5 or len(email) > 200:
        return False, "Email must be valid (contains @) and 5-200 characters"

    # City: 1-100 chars, not blank
    if not city or len(city.strip()) < 1 or len(city) > 100:
        return False, "City must be 1-100 characters"

    # Street: 0-200 chars (optional)
    if len(street) > 200:
        return False, "Street must be 0-200 characters"

    # Monthly income: 0 <= x <= 10,000,000
    try:
        income = float(income_str)
        if income < 0 or income > 10_000_000:
            return False, "Income must be between 0 and 10,000,000"
    except ValueError:
        return False, "Income must be a valid number"

    return True, ""


def call_cobol_validation(customer_id: str, name: str, email: str, city: str) -> tuple[str, str]:
    """
    Call COBOL/customer-update for business-rule validation.

    Input file format (207 bytes):
    - Bytes 1-7: Customer ID (X(7))
    - Bytes 8-57: Name (X(50))
    - Bytes 58-157: Email (X(100))
    - Bytes 158-207: City (X(50))

    Output: (return_code, message) from COBOL response (52 bytes)

    Returns: ("00", "OK") if validation passed; ("01", reason) if failed; ("99", error) on exception
    """
    try:
        # Build input record (207 bytes)
        record = b""
        record += format_pic_x(customer_id, 7).encode('ascii')      # Bytes 1-7
        record += format_pic_x(name, 50).encode('ascii')            # Bytes 8-57
        record += format_pic_x(email, 100).encode('ascii')          # Bytes 58-157
        record += format_pic_x(city, 50).encode('ascii')            # Bytes 158-207

        assert len(record) == 207, f"Record length mismatch: expected 207, got {len(record)}"

        # Write to temp .dat file
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.dat', delete=False) as f:
            temp_file = f.name
            f.write(record)

        logger.info(f"Wrote COBOL input to {temp_file}")

        # Try to call COBOL binary
        cobol_binary = Path(__file__).parent.parent / "cobol" / "customer-update"
        if not cobol_binary.exists():
            logger.warning(f"COBOL binary not found at {cobol_binary}; skipping COBOL validation")
            return "00", "Python validation passed (COBOL binary not available)"

        # Run COBOL program
        result = subprocess.run(
            [str(cobol_binary), temp_file],
            capture_output=True,
            timeout=5
        )

        # Read 52-byte response
        if result.returncode != 0:
            logger.warning(f"COBOL exited with code {result.returncode}")
            return "99", f"COBOL execution failed (exit code {result.returncode})"

        # Parse stdout: should be 52 bytes
        response = result.stdout
        if len(response) < 52:
            logger.warning(f"COBOL response too short: {len(response)} bytes")
            return "99", "COBOL response malformed"

        # Extract return code (bytes 0-1) and message (bytes 2-51)
        return_code = response[0:2].decode('ascii', errors='ignore').strip()
        message = response[2:52].decode('ascii', errors='ignore').strip()

        return return_code, message

    except subprocess.TimeoutExpired:
        logger.error("COBOL validation timeout (5s)")
        return "99", "COBOL validation timeout"
    except Exception as e:
        logger.error(f"COBOL validation error: {e}")
        return "99", f"COBOL error: {str(e)[:40]}"
    finally:
        # Clean up temp file
        try:
            Path(temp_file).unlink()
        except:
            pass


def update_parquet(customer_id: str, name: str, email: str, city: str, street: str, monthly_income: float) -> tuple[bool, str]:
    """
    Update customers.parquet and customer_edits.parquet.

    Returns: (success, error_message)
    """
    try:
        conn = get_connection()
        data_dir = Path(__file__).parent.parent / "data"

        # Read customers.parquet, find and update row
        customers_file = data_dir / "customers.parquet"
        customers_df = conn.execute(f"SELECT * FROM '{customers_file}'").df()

        # Find the matching customer
        mask = customers_df['customer_id'] == customer_id
        if not mask.any():
            return False, f"Customer {customer_id} not found"

        # Update fields
        customers_df.loc[mask, 'name'] = name
        customers_df.loc[mask, 'email'] = email
        customers_df.loc[mask, 'city'] = city
        customers_df.loc[mask, 'monthly_income'] = monthly_income

        # Write back to parquet
        conn.execute(f"COPY (SELECT * FROM customers_df) TO '{customers_file}' (FORMAT PARQUET)")

        logger.info(f"Updated customer {customer_id} in customers.parquet")

        # Upsert customer_edits.parquet with street
        edits_file = data_dir / "customer_edits.parquet"

        if edits_file.exists():
            edits_df = conn.execute(f"SELECT * FROM '{edits_file}'").df()
            # Update or insert
            if (edits_df['customer_id'] == customer_id).any():
                edits_df.loc[edits_df['customer_id'] == customer_id, 'street'] = street
            else:
                # Add new row
                new_row = {'customer_id': customer_id, 'street': street}
                edits_df = conn.execute(f"SELECT * FROM edits_df UNION ALL SELECT '{customer_id}' as customer_id, '{street}' as street").df()
        else:
            # Create new file
            edits_df = conn.execute(f"SELECT '{customer_id}' as customer_id, '{street}' as street").df()

        # Write edits
        conn.execute(f"COPY (SELECT * FROM edits_df) TO '{edits_file}' (FORMAT PARQUET)")

        logger.info(f"Updated customer {customer_id} in customer_edits.parquet")

        return True, "Update successful"

    except Exception as e:
        logger.error(f"Parquet update failed: {e}")
        return False, f"Database update failed: {str(e)[:40]}"


def main():
    """Parse arguments and perform update."""
    if len(sys.argv) < 7:
        logger.error("Usage: customer_update.py <id> <name> <email> <city> <street> <income>")
        print("01|Missing arguments")
        sys.exit(1)

    customer_id = sys.argv[1]
    name = sys.argv[2]
    email = sys.argv[3]
    city = sys.argv[4]
    street = sys.argv[5]
    income_str = sys.argv[6]

    # Step 1: Python validation
    is_valid, error_msg = validate_fields(customer_id, name, email, city, street, income_str)
    if not is_valid:
        print(f"01|{error_msg}")
        sys.exit(1)

    income = float(income_str)

    # Step 2: COBOL validation (if available)
    cobol_code, cobol_msg = call_cobol_validation(customer_id, name, email, city)
    if cobol_code != "00":
        print(f"{cobol_code}|{cobol_msg}")
        sys.exit(1)

    # Step 3: Update parquet files
    success, db_msg = update_parquet(customer_id, name, email, city, street, income)
    if not success:
        print(f"99|{db_msg}")
        sys.exit(99)

    # Success
    print("00|Update successful")
    sys.exit(0)


if __name__ == '__main__':
    main()
