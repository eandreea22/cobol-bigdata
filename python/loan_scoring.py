#!/usr/bin/env python3
"""
Loan Eligibility Scoring

Accepts loan application details and returns:
- Computed credit score (300-850)
- Eligibility decision (Y/N)
- Recommended interest rate
- Maximum approvable amount
- Rejection reason (if applicable)

Credit score formula (normalized to 300-850):
  - Payment history: 35%
  - Credit utilization: 30%
  - Credit length: 15%
  - New credit: 10%
  - Credit mix: 10%

Output: 51-byte fixed-width record to stdout
Return codes: 00=success, 99=error

Invocation: python3 loan_scoring.py <customer_id> <amount> <term_months> <purpose_code>
"""

import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.ipc_formatter import format_pic_x, format_pic_9
from utils.parquet_reader import get_connection, query_customer, query_loans

logging.basicConfig(
    level=logging.ERROR,
    format='%(name)s: %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


def compute_credit_score(loans: list, customer_income: float) -> tuple[int, float, bool, str]:
    """
    Compute credit score (300-850) and additional metrics.

    Returns:
      (credit_score, dti_ratio, has_recent_default, reason)
    """
    if not loans:
        # No loan history: neutral score
        return 650, 0.0, False, ""

    # ============ Factor 1: Payment History (35%) ============
    total_payments = sum(l.get("total_payments", 0) for l in loans)
    on_time_payments = sum(l.get("on_time_payments", 0) for l in loans)

    if total_payments > 0:
        payment_history_ratio = on_time_payments / total_payments
    else:
        payment_history_ratio = 0.5  # No history: neutral

    # ============ Factor 2: Credit Utilization (30%) ============
    # Active loan balance vs. estimated credit limit
    active_balance = sum(l["amount"] for l in loans if l.get("status") == "ACTIVE")
    credit_limit = customer_income * 12 * 0.5  # Estimated: 6 months income

    if credit_limit > 0:
        utilization_ratio = min(active_balance / credit_limit, 1.0)
        credit_util_score = 1.0 - utilization_ratio  # Lower utilization = better
    else:
        credit_util_score = 0.5  # No limit data: neutral

    # ============ Factor 3: Credit Length (15%) ============
    # Account age: older = better (normalized to 0-1)
    if loans:
        def parse_date(d):
            if isinstance(d, str):
                return datetime.strptime(d, "%Y-%m-%d").date()
            else:
                return d  # Already a date object

        oldest_loan_date = min(
            parse_date(l.get("origination_date", "2020-01-01"))
            for l in loans
        )
        account_age_years = (datetime.now().date() - oldest_loan_date).days / 365.25
        credit_length_score = min(account_age_years / 15.0, 1.0)  # Normalized at 15 years
    else:
        credit_length_score = 0.0

    # ============ Factor 4: New Credit (10%) ============
    # No new loans in last 6 months = good
    recent_loans = [
        l for l in loans
        if (datetime.now().date() - parse_date(l.get("origination_date", "2020-01-01"))).days < 180
    ]
    new_credit_score = 1.0 if not recent_loans else 0.3

    # ============ Factor 5: Credit Mix (10%) ============
    # Variety of loan purposes (HOME, AUTO, PERS, EDUC)
    purposes = [l.get("purpose", "PERS") for l in loans]
    unique_purposes = len(set(purposes))
    credit_mix_score = min(unique_purposes / 3.0, 1.0)  # Normalized at 3+ types

    # ============ Combine Factors ============
    raw_score = (
        payment_history_ratio * 0.35
        + credit_util_score * 0.30
        + credit_length_score * 0.15
        + new_credit_score * 0.10
        + credit_mix_score * 0.10
    )

    # Normalize to 300-850 range
    credit_score = int(300 + raw_score * 550)

    # ============ Debt-to-Income Ratio ============
    monthly_obligations = sum(
        l["amount"] / max(l.get("term", 36), 1)
        for l in loans
        if l.get("status") in ["ACTIVE"]
    )
    dti = monthly_obligations / max(customer_income, 1)

    # ============ Recent Defaults ============
    has_recent_default = any(
        l.get("status") == "DEFAULT"
        and (datetime.now().date() - parse_date(l.get("origination_date", "2020-01-01"))).days < 730
        for l in loans
    )

    return credit_score, dti, has_recent_default, ""


def compute_interest_rate(credit_score: int, base_rate: float = 4.0) -> float:
    """
    Compute interest rate based on credit score tier.

    Base rate ~4.0%, adjusted by tier:
      750-850: base + 0.5% = 4.5%
      700-749: base + 1.5% = 5.5%
      650-699: base + 3.0% = 7.0%
      < 650:   ineligible
    """
    if credit_score >= 750:
        return base_rate + 0.5
    elif credit_score >= 700:
        return base_rate + 1.5
    elif credit_score >= 650:
        return base_rate + 3.0
    else:
        return 0.0  # Ineligible


def compute_max_amount(customer_income: float, dti: float) -> float:
    """
    Compute maximum approvable loan amount based on DTI.

    Target DTI: < 0.43 (43% of monthly income to loan payments)
    """
    # Available monthly payment capacity
    available_monthly = customer_income * 0.43 - (customer_income * dti)

    # Assuming 36-month term at ~5% interest
    # Monthly payment ≈ principal / 36 (simplified)
    max_amount = max(available_monthly * 36, 0)

    return max_amount


def build_response_record(credit_score: int, eligible: str, int_rate: float,
                         max_amount: float, reason: str, return_code: str) -> str:
    """
    Build the 51-byte response record.

    Byte layout:
      1-3:    Credit score (PIC 9(3), 300-850)
      4:      Eligible (PIC X(1), Y or N)
      5-9:    Interest rate (PIC 9V9(4), 5 chars, e.g., "04750" = 4.75%)
      10-19:  Max approvable amount (PIC 9(8)V99, 10 chars)
      20-49:  Rejection reason (PIC X(30))
      50-51:  Return code (PIC 99)
    """
    record = (
        format_pic_9(credit_score, 3)          # bytes 1-3 (3 chars)
        + format_pic_x(eligible, 1)            # byte 4 (1 char)
        + format_pic_9(int_rate, 1, 4)         # bytes 5-9 (5 chars: 9V9999)
        + format_pic_9(max_amount, 8, 2)       # bytes 10-19 (10 chars)
        + format_pic_x(reason, 30)             # bytes 20-49 (30 chars)
        + format_pic_x(return_code, 2)         # bytes 50-51 (2 chars)
    )

    assert len(record) == 51, f"Record length {len(record)} != 51"
    return record


def main():
    """Main entry point."""
    try:
        # Parse arguments
        if len(sys.argv) < 5:
            logger.error("Usage: python3 loan_scoring.py <customer_id> <amount> <term_months> <purpose_code>")
            sys.stdout.write(build_response_record(300, "N", 0, 0, "INVALID_ARGUMENTS", "99") + "\n")
            sys.exit(1)

        customer_id = sys.argv[1].strip()
        try:
            requested_amount = float(sys.argv[2].strip())
            term_months = int(sys.argv[3].strip())
            purpose_code = sys.argv[4].strip()
        except (ValueError, IndexError):
            logger.error("Invalid argument format")
            sys.stdout.write(build_response_record(300, "N", 0, 0, "INVALID_FORMAT", "99") + "\n")
            sys.exit(1)

        # Create DuckDB connection
        conn = get_connection()

        try:
            # Query customer data
            customer = query_customer(conn, customer_id)
            if customer is None:
                # Customer not found
                record = build_response_record(300, "N", 0, 0, "CUSTOMER_NOT_FOUND", "99")
                sys.stdout.write(record + "\n")
                sys.stdout.flush()
                return

            # Query loan history
            loans = query_loans(conn, customer_id)

            # Compute credit score and metrics
            credit_score, dti, has_recent_default, _ = compute_credit_score(loans, customer["monthly_income"])

            # Determine eligibility
            eligible = (
                credit_score >= 650
                and dti < 0.43
                and not has_recent_default
            )

            # Compute interest rate
            int_rate = compute_interest_rate(credit_score)

            # Compute max approvable amount
            max_approvable = compute_max_amount(customer["monthly_income"], dti)

            # Rejection reason
            reason = ""
            if not eligible:
                if credit_score < 650:
                    reason = "LOW_CREDIT_SCORE"
                elif dti >= 0.43:
                    reason = "HIGH_DTI"
                elif has_recent_default:
                    reason = "RECENT_DEFAULT"

            # Build response record
            record = build_response_record(
                credit_score=credit_score,
                eligible="Y" if eligible else "N",
                int_rate=int_rate,
                max_amount=max_approvable,
                reason=reason,
                return_code="00"
            )

            # Output record
            sys.stdout.write(record + "\n")
            sys.stdout.flush()

        finally:
            conn.close()

    except Exception as e:
        logger.exception("Unhandled exception in loan_scoring.py")
        sys.stdout.write(build_response_record(300, "N", 0, 0, "SYSTEM_ERROR", "99") + "\n")
        sys.stdout.flush()
        sys.exit(1)


if __name__ == "__main__":
    main()
