"""
Output parsing utilities for analytics scripts and customer management features.

Parses fixed-width records from customer_360.py, loan_scoring.py, and fraud_detect.py.
Also parses pipe-delimited output from customer_search.py, customer_list.py, and customer_update.py.
Each function validates format and return code, raising descriptive exceptions on error.
"""

from typing import Dict, List, Any, Tuple


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


def parse_customer_search(raw: str) -> List[Dict[str, str]]:
    """
    Parse pipe-delimited customer search results.

    Format:
        <count>
        <customer_id>|<name>|<city>|<email>
        <customer_id>|<name>|<city>|<email>
        ...

    Args:
        raw: Output from customer_search.py (multi-line, pipe-delimited)

    Returns:
        List of dicts with: customer_id, name, city, email

    Raises:
        ParseError: If format is invalid or count mismatches actual results
    """
    try:
        lines = raw.strip().split('\n')
        if not lines:
            raise ParseError("Empty search results")

        count_str = lines[0].strip()
        try:
            count = int(count_str)
        except ValueError:
            raise ParseError(f"Invalid result count: {count_str}")

        # Count=0 means no results
        if count == 0:
            return []

        # Should have count+1 lines (count line + result lines)
        if len(lines) != count + 1:
            raise ParseError(f"Count mismatch: expected {count + 1} lines, got {len(lines)}")

        results = []
        for i in range(1, count + 1):
            line = lines[i]
            parts = line.split('|')

            if len(parts) != 4:
                raise ParseError(f"Line {i}: expected 4 pipe-delimited fields, got {len(parts)}")

            customer_id, name, city, email = parts
            results.append({
                'customer_id': customer_id.strip(),
                'name': name.strip(),
                'city': city.strip(),
                'email': email.strip(),
            })

        return results

    except ParseError:
        raise
    except Exception as e:
        raise ParseError(f"Failed to parse customer search results: {e}")


def parse_customer_list(raw: str) -> Tuple[List[Dict[str, Any]], int]:
    """
    Parse pipe-delimited paginated customer list.

    Format:
        <total_matching>
        <customer_id>|<name>|<email>|<city>|<street>|<balance>|<monthly_income>
        <customer_id>|<name>|<email>|<city>|<street>|<balance>|<monthly_income>
        ...

    Args:
        raw: Output from customer_list.py (multi-line, pipe-delimited)

    Returns:
        Tuple of (list of customer dicts, total_matching count)
        Each dict has: customer_id, name, email, city, street, balance, monthly_income

    Raises:
        ParseError: If format is invalid
    """
    try:
        lines = raw.strip().split('\n')
        if not lines:
            raise ParseError("Empty customer list results")

        total_str = lines[0].strip()
        try:
            total = int(total_str)
        except ValueError:
            raise ParseError(f"Invalid total count: {total_str}")

        # If total=0, no data rows
        if total == 0:
            return [], 0

        # Parse data rows (all lines after the first)
        rows = []
        for i in range(1, len(lines)):
            line = lines[i]
            parts = line.split('|')

            if len(parts) != 7:
                raise ParseError(f"Line {i}: expected 7 pipe-delimited fields, got {len(parts)}")

            customer_id, name, email, city, street, balance_str, income_str = parts

            try:
                balance = float(balance_str.strip())
                monthly_income = float(income_str.strip())
            except ValueError:
                raise ParseError(f"Line {i}: invalid numeric values in balance/income")

            rows.append({
                'customer_id': customer_id.strip(),
                'name': name.strip(),
                'email': email.strip(),
                'city': city.strip(),
                'street': street.strip(),
                'balance': balance,
                'monthly_income': monthly_income,
            })

        return rows, total

    except ParseError:
        raise
    except Exception as e:
        raise ParseError(f"Failed to parse customer list results: {e}")


def parse_customer_update(raw: str) -> Dict[str, Any]:
    """
    Parse customer update response (pipe-delimited).

    Format:
        <return_code>|<message>

    Args:
        raw: Output from customer_update.py

    Returns:
        Dict with: code, message, success (boolean)

    Raises:
        ParseError: If format is invalid or code is "99"
    """
    try:
        line = raw.strip()
        parts = line.split('|', 1)  # Split on first | only (message may contain |)

        if len(parts) != 2:
            raise ParseError(f"Expected 'code|message' format, got: {line}")

        code_str, message = parts
        code = code_str.strip()

        # Validate return code format
        if code not in ("00", "01", "99"):
            raise ParseError(f"Invalid return code: {code}")

        # Check for system error
        if code == "99":
            raise ParseError(f"Update system error: {message.strip()}")

        # Check for validation error
        if code == "01":
            raise ParseError(f"Update validation error: {message.strip()}")

        return {
            'code': code,
            'message': message.strip(),
            'success': code == "00",
        }

    except ParseError:
        raise
    except Exception as e:
        raise ParseError(f"Failed to parse customer update response: {e}")


def parse_customer_transactions(raw: str) -> Dict[str, Any]:
    """
    Parse customer transactions response (pipe-delimited, 8 fields).

    Format:
        <count>
        <txn_id>|<date>|<time>|<amount>|<merchant>|<mcc>|<city>|<channel>
        <txn_id>|<date>|<time>|<amount>|<merchant>|<mcc>|<city>|<channel>
        ...

    Args:
        raw: Output from customer_transactions.py

    Returns:
        Dict with:
            'count': total number of transactions for this customer
            'transactions': list of dicts with txn_id, date, time, amount, merchant, mcc, city, channel

    Raises:
        ParseError: If format is invalid
    """
    try:
        lines = raw.strip().split('\n')
        if not lines:
            raise ParseError("Empty response")

        # First line is count
        count_str = lines[0].strip()
        try:
            count = int(count_str)
        except ValueError:
            raise ParseError(f"Invalid count in first line: {count_str}")

        transactions = []

        # If count is 0, no transactions
        if count == 0:
            return {'count': 0, 'transactions': []}

        # Parse remaining lines (one transaction per line, 8 fields)
        for i, line in enumerate(lines[1:], start=1):
            if not line.strip():
                continue

            parts = line.split('|')
            if len(parts) != 8:
                raise ParseError(f"Line {i}: Expected 8 fields, got {len(parts)}")

            try:
                txn_id = parts[0].strip()
                date = parts[1].strip()
                time = parts[2].strip()
                amount = float(parts[3])
                merchant = parts[4].strip()
                mcc = parts[5].strip()
                city = parts[6].strip()
                channel = parts[7].strip()

                transaction = {
                    'txn_id': txn_id,
                    'date': date,
                    'time': time,
                    'amount': amount,
                    'merchant': merchant,
                    'mcc': mcc,
                    'city': city,
                    'channel': channel
                }
                transactions.append(transaction)
            except ValueError as e:
                raise ParseError(f"Line {i}: Failed to parse transaction: {str(e)}")

        return {
            'count': count,
            'transactions': transactions
        }

    except ParseError:
        raise
    except Exception as e:
        raise ParseError(f"Failed to parse customer transactions: {e}")


def parse_fraud_batch_analysis(raw: str) -> Dict[str, Any]:
    """
    Parse batch fraud analysis results (pipe-delimited).

    Format:
        Line 1: total|high_count|medium_count|low_count
        Lines 2..N: txn_id|date|amount|mcc|city|channel|score|risk|recommendation|is_fraud

    Args:
        raw: Output from fraud_batch_analysis.py

    Returns:
        Dict with:
            'summary': {total, high_count, medium_count, low_count}
            'transactions': list of dicts with all fields above

    Raises:
        ParseError: If format is invalid
    """
    try:
        lines = raw.strip().split('\n')
        if not lines:
            raise ParseError("Empty response from fraud batch analysis")

        # ── Parse summary line ──────────────────────────────
        summary_parts = lines[0].strip().split('|')
        if len(summary_parts) != 4:
            raise ParseError(
                f"Summary line: expected 4 pipe-delimited fields, got {len(summary_parts)}"
            )

        try:
            total, high_count, medium_count, low_count = (int(p) for p in summary_parts)
        except ValueError as e:
            raise ParseError(f"Summary line contains non-integer value: {e}")

        # ── Zero-transaction fast path ──────────────────────
        if total == 0:
            return {
                'summary': {
                    'total': 0,
                    'high_count': 0,
                    'medium_count': 0,
                    'low_count': 0,
                },
                'transactions': [],
            }

        # ── Parse transaction lines ─────────────────────────
        transactions = []
        for i, line in enumerate(lines[1:], start=1):
            if not line.strip():
                continue

            parts = line.split('|')
            if len(parts) != 10:
                raise ParseError(
                    f"Transaction line {i}: expected 10 fields, got {len(parts)}"
                )

            txn_id, date, amount_str, mcc, city, channel, \
            score_str, risk, recommendation, is_fraud = parts

            # Validate numeric fields
            try:
                amount = float(amount_str)
            except ValueError:
                raise ParseError(f"Line {i}: invalid amount '{amount_str}'")

            try:
                score = int(score_str)
            except ValueError:
                raise ParseError(f"Line {i}: invalid score '{score_str}'")

            # Validate enum fields
            if risk not in ("LOW", "MEDIUM", "HIGH"):
                raise ParseError(f"Line {i}: invalid risk level '{risk}'")
            if recommendation not in ("APPROVE", "REVIEW", "DECLINE"):
                raise ParseError(f"Line {i}: invalid recommendation '{recommendation}'")
            if is_fraud not in ("true", "false", "unknown"):
                raise ParseError(f"Line {i}: invalid is_fraud value '{is_fraud}'")

            transactions.append({
                'txn_id':         txn_id.strip(),
                'date':           date.strip(),
                'amount':         amount,
                'mcc':            mcc.strip(),
                'city':           city.strip(),
                'channel':        channel.strip(),
                'score':          score,
                'risk':           risk.strip(),
                'recommendation': recommendation.strip(),
                'is_fraud':       is_fraud.strip(),
            })

        # ── Consistency check ───────────────────────────────
        if len(transactions) != total:
            raise ParseError(
                f"Count mismatch: summary says {total} transactions, "
                f"but parsed {len(transactions)} lines"
            )

        return {
            'summary': {
                'total':        total,
                'high_count':   high_count,
                'medium_count': medium_count,
                'low_count':    low_count,
            },
            'transactions': transactions,
        }

    except ParseError:
        raise
    except Exception as e:
        raise ParseError(f"Failed to parse fraud batch analysis output: {e}")
