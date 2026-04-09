#!/usr/bin/env python3
"""
Report Aggregator

Batch processor that reads customer IDs from CSV and runs analytics
on each, aggregating results into a summary report.

Invocation:
  python3 report_aggregator.py <input_csv> <output_report>

Input CSV format:
  customer_id,amount,term,purpose
  C-00001,10000,36,PERS
  C-00002,25000,60,HOME
  ...

Output: Summary report with aggregated statistics
"""

import sys
import csv
import subprocess
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)


def parse_customer_360_record(record: str) -> dict:
    """Parse 145-byte customer 360 record."""
    if len(record) < 95:
        return None

    return {
        "name": record[0:50].strip(),
        "balance": float(record[50:62].strip() or "0") / 100,
        "txn_count": int(record[62:70].strip() or "0"),
        "avg_monthly": float(record[70:80].strip() or "0") / 100,
        "risk_score": int(record[80:83].strip() or "0"),
        "last_txn_date": record[83:93].strip(),
        "return_code": int(record[93:95].strip() or "99"),
    }


def parse_loan_scoring_record(record: str) -> dict:
    """Parse 51-byte loan scoring record."""
    if len(record) < 51:
        return None

    return {
        "credit_score": int(record[0:3].strip() or "300"),
        "eligible": record[3].strip() == "Y",
        "int_rate": float(record[4:9].strip() or "0") / 10000,
        "max_amount": float(record[9:19].strip() or "0") / 100,
        "reject_reason": record[19:49].strip(),
        "return_code": int(record[49:51].strip() or "99"),
    }


def parse_fraud_detect_record(record: str) -> dict:
    """Parse 78-byte fraud detection record."""
    if len(record) < 78:
        return None

    return {
        "fraud_risk": record[0:6].strip(),
        "fraud_score": int(record[6:9].strip() or "0"),
        "fraud_flags": record[9:69].strip(),
        "recommend": record[69:76].strip(),
        "return_code": int(record[76:78].strip() or "99"),
    }


def run_customer_360(customer_id: str) -> dict:
    """Run customer_360.py and parse response."""
    try:
        result = subprocess.run(
            ["python3", "python/customer_360.py", customer_id],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            logger.warning(f"customer_360.py failed for {customer_id}")
            return None

        record = result.stdout.strip()
        return parse_customer_360_record(record)
    except Exception as e:
        logger.error(f"Error running customer_360.py for {customer_id}: {e}")
        return None


def run_loan_scoring(customer_id: str, amount: float, term: int, purpose: str) -> dict:
    """Run loan_scoring.py and parse response."""
    try:
        result = subprocess.run(
            ["python3", "python/loan_scoring.py", customer_id, str(amount), str(term), purpose],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            logger.warning(f"loan_scoring.py failed for {customer_id}")
            return None

        record = result.stdout.strip()
        return parse_loan_scoring_record(record)
    except Exception as e:
        logger.error(f"Error running loan_scoring.py for {customer_id}: {e}")
        return None


def run_fraud_detect(customer_id: str, amount: float, mcc: str, location: str, timestamp: str, channel: str) -> dict:
    """Run fraud_detect.py and parse response."""
    try:
        result = subprocess.run(
            ["python3", "python/fraud_detect.py", customer_id, str(amount), mcc, location, timestamp, channel],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            logger.warning(f"fraud_detect.py failed for {customer_id}")
            return None

        record = result.stdout.strip()
        return parse_fraud_detect_record(record)
    except Exception as e:
        logger.error(f"Error running fraud_detect.py for {customer_id}: {e}")
        return None


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        logger.error("Usage: python3 report_aggregator.py <input_csv> <output_report>")
        sys.exit(1)

    input_csv = sys.argv[1]
    output_report = sys.argv[2]

    # Verify input exists
    if not Path(input_csv).exists():
        logger.error(f"Input file not found: {input_csv}")
        sys.exit(1)

    # Aggregate results
    results = []
    successful = 0
    failed = 0

    logger.info(f"Processing {input_csv}...")

    try:
        with open(input_csv, 'r') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, start=1):
                customer_id = row.get("customer_id", "").strip()
                amount = float(row.get("amount", "0"))
                term = int(row.get("term", "36"))
                purpose = row.get("purpose", "PERS").strip()

                if not customer_id:
                    logger.warning(f"Row {i}: missing customer_id")
                    failed += 1
                    continue

                logger.info(f"Row {i}: Processing {customer_id}...")

                # Run analytics
                cust_360 = run_customer_360(customer_id)
                loan = run_loan_scoring(customer_id, amount, term, purpose)
                fraud = run_fraud_detect(customer_id, amount, "5411", "Bucharest", datetime.now().isoformat(), "POS")

                if cust_360 and loan and fraud:
                    results.append({
                        "customer_id": customer_id,
                        "name": cust_360.get("name", ""),
                        "risk_score": cust_360.get("risk_score", 0),
                        "credit_score": loan.get("credit_score", 0),
                        "eligible": loan.get("eligible", False),
                        "fraud_risk": fraud.get("fraud_risk", ""),
                        "fraud_score": fraud.get("fraud_score", 0),
                    })
                    successful += 1
                else:
                    failed += 1

    except Exception as e:
        logger.error(f"Error reading input file: {e}")
        sys.exit(1)

    # Generate report
    logger.info(f"Aggregating {successful} successful results, {failed} failures...")

    avg_risk_score = sum(r["risk_score"] for r in results) / len(results) if results else 0
    avg_credit_score = sum(r["credit_score"] for r in results) / len(results) if results else 0
    eligible_count = sum(1 for r in results if r["eligible"])
    high_fraud_count = sum(1 for r in results if r["fraud_score"] >= 70)

    with open(output_report, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("BANKING ANALYTICS SUMMARY REPORT\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"Total Records Processed: {len(results)}\n")
        f.write(f"Successful: {successful}\n")
        f.write(f"Failed: {failed}\n\n")

        f.write("AGGREGATED METRICS:\n")
        f.write("-" * 80 + "\n")
        f.write(f"Average Risk Score: {avg_risk_score:.1f}\n")
        f.write(f"Average Credit Score: {avg_credit_score:.1f}\n")
        f.write(f"Loan Eligible: {eligible_count} ({100*eligible_count/len(results):.1f}%)\n")
        f.write(f"High Fraud Risk (score >= 70): {high_fraud_count} ({100*high_fraud_count/len(results):.1f}%)\n\n")

        f.write("DETAILED RESULTS:\n")
        f.write("-" * 80 + "\n")
        f.write(f"{'Customer ID':<12} {'Name':<20} {'Risk':<5} {'Credit':<7} {'Eligible':<9} {'Fraud':<6}\n")
        f.write("-" * 80 + "\n")
        for r in results:
            eligible_str = "Y" if r["eligible"] else "N"
            f.write(f"{r['customer_id']:<12} {r['name']:<20} {r['risk_score']:<5} "
                   f"{r['credit_score']:<7} {eligible_str:<9} {r['fraud_score']:<6}\n")

    logger.info(f"Report written to {output_report}")


if __name__ == "__main__":
    main()
