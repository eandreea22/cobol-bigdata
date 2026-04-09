"""
Output parsing utilities for analytics scripts.

Parses fixed-width records from customer_360.py, loan_scoring.py, and fraud_detect.py.
Each function validates byte length and return code, raising descriptive exceptions on error.
"""

from typing import Dict, List, Any


class ParseError(Exception):
    """Raised when output parsing fails."""
    pass


def parse_customer_360(raw: str) -> Dict[str, Any]:
    """
    Parse 145-byte customer 360 response record.

    Args:
        raw: Output line from customer_360.py (should be 145 bytes)

    Returns:
        Dict with: name, balance, txn_count, avg_monthly, risk_score, last_txn_date, return_code

    Raises:
        ParseError: If record is malformed or return_code is "99" or "01"
    """
    if len(raw) != 145:
        raise ParseError(f"Expected 145 bytes, got {len(raw)}")

    try:
        return_code = raw[93:95]

        if return_code == "99":
            raise ParseError("Customer script error — system failure or invalid input")
        if return_code == "01":
            raise ParseError("Customer not found — check customer ID")
        if return_code != "00":
            raise ParseError(f"Unknown return code: {return_code}")

        return {
            "name": raw[0:50].strip(),
            "balance": int(raw[50:62]) / 100.0,  # dollars
            "txn_count": int(raw[62:70]),
            "avg_monthly": int(raw[70:80]) / 100.0,  # dollars
            "risk_score": int(raw[80:83]),  # 0-999
            "last_txn_date": raw[83:93].strip(),  # YYYY-MM-DD
            "return_code": return_code,
        }
    except (ValueError, IndexError) as e:
        raise ParseError(f"Failed to parse customer 360 record: {e}")


def parse_loan_scoring(raw: str) -> Dict[str, Any]:
    """
    Parse 51-byte loan scoring response record.

    Args:
        raw: Output line from loan_scoring.py (should be 51 bytes)

    Returns:
        Dict with: credit_score, eligible, int_rate, max_amount, reason, return_code

    Raises:
        ParseError: If record is malformed or return_code is "99"
    """
    if len(raw) != 51:
        raise ParseError(f"Expected 51 bytes, got {len(raw)}")

    try:
        return_code = raw[49:51]

        if return_code == "99":
            reason = raw[19:49].strip()
            raise ParseError(f"Loan scoring error: {reason if reason else 'System failure'}")
        if return_code != "00":
            raise ParseError(f"Unknown return code: {return_code}")

        eligible = raw[3]
        if eligible not in ("Y", "N"):
            raise ParseError(f"Invalid eligible value: {eligible}")

        int_rate_raw = int(raw[4:9])  # PIC 9(1)V9(4) → divide by 10000
        int_rate = int_rate_raw / 10000.0

        max_amount = int(raw[9:19]) / 100.0  # dollars

        return {
            "credit_score": int(raw[0:3]),  # 300-850
            "eligible": eligible == "Y",  # boolean
            "int_rate": int_rate,  # percentage (e.g. 0.045 = 4.5%)
            "max_amount": max_amount,  # dollars
            "reason": raw[19:49].strip(),  # rejection reason if not eligible
            "return_code": return_code,
        }
    except (ValueError, IndexError) as e:
        raise ParseError(f"Failed to parse loan scoring record: {e}")


def parse_fraud_detect(raw: str) -> Dict[str, Any]:
    """
    Parse 78-byte fraud detection response record.

    Args:
        raw: Output line from fraud_detect.py (should be 78 bytes)

    Returns:
        Dict with: risk_level, fraud_score, flags, recommendation, return_code

    Raises:
        ParseError: If record is malformed or return_code is "99"
    """
    if len(raw) != 78:
        raise ParseError(f"Expected 78 bytes, got {len(raw)}")

    try:
        return_code = raw[76:78]

        if return_code == "99":
            raise ParseError("Fraud detection error — system failure or invalid input")
        if return_code != "00":
            raise ParseError(f"Unknown return code: {return_code}")

        risk_level_raw = raw[0:6].strip()  # "LOW", "MEDIUM", or "HIGH"
        if risk_level_raw not in ("LOW", "MEDIUM", "HIGH"):
            raise ParseError(f"Invalid risk level: {risk_level_raw}")

        fraud_score = int(raw[6:9])  # 0-100
        if not 0 <= fraud_score <= 100:
            raise ParseError(f"Fraud score out of range: {fraud_score}")

        # Parse comma-separated flags
        flags_raw = raw[9:69].strip()
        flags = [f.strip() for f in flags_raw.split(",") if f.strip()]

        recommendation = raw[69:76].strip()  # "APPROVE", "REVIEW", or "DECLINE"
        if recommendation not in ("APPROVE", "REVIEW", "DECLINE"):
            raise ParseError(f"Invalid recommendation: {recommendation}")

        return {
            "risk_level": risk_level_raw,  # "LOW", "MEDIUM", "HIGH"
            "fraud_score": fraud_score,  # 0-100
            "flags": flags,  # list of flag names
            "recommendation": recommendation,  # "APPROVE", "REVIEW", "DECLINE"
            "return_code": return_code,
        }
    except (ValueError, IndexError) as e:
        raise ParseError(f"Failed to parse fraud detection record: {e}")
