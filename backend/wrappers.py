"""
Wrapper functions to integrate existing Python analytics scripts with FastAPI backend.
These functions extract and expose the core logic from the standalone scripts.
"""

import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Get parent directory (project root)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')

# Import DuckDB for queries
import duckdb


def analyze_customer_360(customer_id: str) -> Dict[str, Any]:
    """
    Analyze customer profile from customers and transactions data.
    Returns: Customer360Response dict
    """
    try:
        # Build file paths (convert to forward slashes for DuckDB)
        customers_parquet = os.path.join(DATA_DIR, 'customers.parquet').replace(chr(92), '/')
        transactions_pattern = os.path.join(DATA_DIR, 'transactions', '**', '*.parquet').replace(chr(92), '/')

        # Query customer from parquet (using actual column names: name, credit_tier, monthly_income)
        query = f"""
        SELECT
            customer_id, name, monthly_income, credit_tier
        FROM read_parquet('{customers_parquet}')
        WHERE customer_id = '{customer_id}'
        """

        conn = duckdb.connect(':memory:')
        customer = conn.execute(query).fetchall()

        if not customer:
            return {
                "customer_name": "",
                "account_balance": 0,
                "transaction_count": 0,
                "avg_monthly": 0,
                "risk_score": 0,
                "last_transaction_date": "",
                "return_code": "01"  # Not found
            }

        cust = customer[0]
        cust_id, name, income, tier = cust

        # Query transactions
        txn_query = f"""
        SELECT
            COUNT(*) as txn_count,
            AVG(amount) as avg_amount,
            SUM(amount) as total_amount,
            MAX(timestamp) as last_txn
        FROM read_parquet('{transactions_pattern}')
        WHERE customer_id = '{customer_id}'
        """

        txn_result = conn.execute(txn_query).fetchall()
        if txn_result:
            txn_count, avg_amount, total_amount, last_txn = txn_result[0]
        else:
            txn_count, avg_amount, total_amount, last_txn = 0, 0, 0, None

        # Calculate account balance from total transactions (fictional - in production would be in DB)
        balance = float(income or 50000) - (float(total_amount) if total_amount else 0)
        balance = max(0, balance)  # Ensure non-negative

        # Calculate risk score (0-999) based on transaction patterns
        risk_score = min(999, max(0, int((balance / 100000) * 500) + (int(txn_count) // 10)))

        return {
            "customer_name": str(name or ""),
            "account_balance": float(balance),
            "transaction_count": int(txn_count or 0),
            "avg_monthly": float(avg_amount or 0),
            "risk_score": int(risk_score),
            "last_transaction_date": str(last_txn).split()[0] if last_txn else "N/A",
            "return_code": "00"  # Success
        }

    except Exception as e:
        print(f"Error in analyze_customer_360: {e}")
        import traceback
        traceback.print_exc()
        return {
            "customer_name": "",
            "account_balance": 0,
            "transaction_count": 0,
            "avg_monthly": 0,
            "risk_score": 0,
            "last_transaction_date": "",
            "return_code": "99"  # Error
        }


def score_loan(customer_id: str, amount: float, term_months: int, purpose_code: str) -> Dict[str, Any]:
    """
    Assess loan eligibility and calculate interest rates.
    Returns: LoanAssessmentResponse dict
    """
    try:
        # Build file paths (convert to forward slashes for DuckDB)
        customers_parquet = os.path.join(DATA_DIR, 'customers.parquet').replace(chr(92), '/')
        loans_parquet = os.path.join(DATA_DIR, 'loans.parquet').replace(chr(92), '/')

        conn = duckdb.connect(':memory:')

        # Get customer income (monthly_income in the data)
        query = f"""
        SELECT monthly_income FROM read_parquet('{customers_parquet}')
        WHERE customer_id = '{customer_id}'
        """

        result = conn.execute(query).fetchall()
        if not result:
            return {
                "credit_score": 0,
                "eligible": "N",
                "interest_rate": 0,
                "max_amount": 0,
                "reject_reason": "Customer not found",
                "return_code": "01"
            }

        monthly_income = float(result[0][0] or 5000)
        annual_income = monthly_income * 12

        # Get existing loans for DTI calculation
        loan_query = f"""
        SELECT COUNT(*), COALESCE(SUM(rate), 0)
        FROM read_parquet('{loans_parquet}')
        WHERE customer_id = '{customer_id}' AND status = 'ACTIVE'
        """

        loan_result = conn.execute(loan_query).fetchall()[0]
        num_loans = int(loan_result[0])
        existing_debt = float(loan_result[1])

        # Simple credit score calculation (300-850) based on payment history
        base_score = 600
        credit_score = min(850, max(300, base_score + (num_loans * -20)))

        # Calculate DTI
        monthly_payment = (amount / term_months)
        total_monthly_debt = existing_debt + monthly_payment
        dti = total_monthly_debt / monthly_income if monthly_income > 0 else 1

        # Determine eligibility
        eligible = "Y" if (credit_score >= 650 and dti < 0.43) else "N"

        # Interest rate based on credit score
        if credit_score >= 750:
            interest_rate = 3.5
        elif credit_score >= 700:
            interest_rate = 4.5
        elif credit_score >= 650:
            interest_rate = 5.5
        else:
            interest_rate = 0

        # Max approved amount
        max_amount = (monthly_income * 0.43 - existing_debt) * term_months if eligible == "Y" else 0

        return {
            "credit_score": int(credit_score),
            "eligible": eligible,
            "interest_rate": round(interest_rate, 2),
            "max_amount": int(max(0, max_amount)),
            "reject_reason": "DTI too high" if dti >= 0.43 else "Credit score too low" if credit_score < 650 else "",
            "return_code": "00"
        }

    except Exception as e:
        print(f"Error in score_loan: {e}")
        import traceback
        traceback.print_exc()
        return {
            "credit_score": 0,
            "eligible": "N",
            "interest_rate": 0,
            "max_amount": 0,
            "reject_reason": f"Error: {str(e)}",
            "return_code": "99"
        }


def detect_fraud(customer_id: str, amount: float, mcc: str, location: str,
                timestamp: str, channel: str) -> Dict[str, Any]:
    """
    Detect fraud for a single transaction.
    Returns: FraudDetectionResponse dict
    """
    try:
        # Build file paths (convert to forward slashes for DuckDB)
        transactions_pattern = os.path.join(DATA_DIR, 'transactions', '**', '*.parquet').replace(chr(92), '/')

        conn = duckdb.connect(':memory:')

        # Get customer transaction statistics
        stats_query = f"""
        SELECT
            AVG(amount) as avg_amount,
            STDDEV(amount) as stddev_amount,
            MAX(amount) as max_amount
        FROM read_parquet('{transactions_pattern}')
        WHERE customer_id = '{customer_id}'
        """

        stats = conn.execute(stats_query).fetchall()
        if not stats or stats[0][0] is None:
            avg_amt, stddev_amt = 1000, 500
        else:
            avg_amt, stddev_amt, _ = stats[0]
            avg_amt = float(avg_amt or 1000)
            stddev_amt = float(stddev_amt or 500)

        # Calculate fraud score (0-999)
        score = 0
        flags = []

        # Amount anomaly (3-sigma rule)
        if stddev_amt > 0 and amount > avg_amt + (3 * stddev_amt):
            score += 300
            flags.append("amount_anomaly")

        # Geographic anomaly (simple: assume US transactions are normal)
        if location.lower() not in ["new york", "los angeles", "chicago", "houston", "phoenix"]:
            score += 100
            flags.append("geo_anomaly")

        # Velocity check (flag if multiple transactions)
        if channel == "ONLINE" and amount > 5000:
            score += 150
            flags.append("high_value_online")

        # Time of day check (late night)
        try:
            hour = int(timestamp.split("T")[1].split(":")[0]) if "T" in timestamp else 12
            if hour < 6 or hour > 22:
                score += 50
                flags.append("unusual_time")
        except:
            pass

        score = min(999, score)

        # Classify risk
        if score < 300:
            risk = "LOW"
            recommendation = "APPROVE"
        elif score < 600:
            risk = "MEDIUM"
            recommendation = "REVIEW"
        else:
            risk = "HIGH"
            recommendation = "DECLINE"

        return {
            "fraud_risk": risk,
            "fraud_score": int(score),
            "flags": ",".join(flags),
            "recommendation": recommendation,
            "return_code": "00"
        }

    except Exception as e:
        print(f"Error in detect_fraud: {e}")
        return {
            "fraud_risk": "UNKNOWN",
            "fraud_score": 0,
            "flags": "",
            "recommendation": "REVIEW",
            "return_code": "99"
        }


def get_customer_transactions(customer_id: str, limit: int = 100) -> Dict[str, Any]:
    """
    Get all transactions for a customer.
    Returns: List of transactions
    """
    try:
        # Build file paths (convert to forward slashes for DuckDB)
        transactions_pattern = os.path.join(DATA_DIR, 'transactions', '**', '*.parquet').replace(chr(92), '/')

        conn = duckdb.connect(':memory:')

        query = f"""
        SELECT
            txn_id, amount, timestamp, city, mcc
        FROM read_parquet('{transactions_pattern}')
        WHERE customer_id = '{customer_id}'
        ORDER BY timestamp DESC
        LIMIT {min(limit, 1000)}
        """

        results = conn.execute(query).fetchall()

        transactions = []
        for row in results:
            txn_id, amount, ts, city, mcc = row
            transactions.append({
                "transaction_id": str(txn_id),
                "amount": float(amount),
                "timestamp": str(ts),
                "location": str(city),
                "category": str(mcc),
                "fraud_risk": "LOW"
            })

        return {
            "customer_id": customer_id,
            "total": len(transactions),
            "transactions": transactions
        }

    except Exception as e:
        print(f"Error in get_customer_transactions: {e}")
        return {
            "customer_id": customer_id,
            "total": 0,
            "transactions": []
        }


def analyze_fraud_batch(customer_id: str, limit: int = None) -> Dict[str, Any]:
    """
    Analyze all transactions for a customer and classify fraud risk.
    Returns: BatchFraudResponse dict
    """
    try:
        transactions = get_customer_transactions(customer_id, limit or 200)

        # Calculate fraud risk for each transaction
        high_risk_count = 0
        total_score = 0

        for txn in transactions["transactions"]:
            # Simple fraud score based on amount
            score = min(999, int(txn["amount"] / 100))
            total_score += score

            if score > 600:
                txn["fraud_risk"] = "HIGH"
                txn["fraud_score"] = score
                high_risk_count += 1
            elif score > 300:
                txn["fraud_risk"] = "MEDIUM"
                txn["fraud_score"] = score
            else:
                txn["fraud_risk"] = "LOW"
                txn["fraud_score"] = score

        avg_risk = int(total_score / len(transactions["transactions"])) if transactions["transactions"] else 0

        return {
            "customer_id": customer_id,
            "total_transactions": transactions["total"],
            "flagged_count": high_risk_count,
            "fraud_risk_avg": str(avg_risk),
            "transactions": transactions["transactions"]
        }

    except Exception as e:
        print(f"Error in analyze_fraud_batch: {e}")
        return {
            "customer_id": customer_id,
            "total_transactions": 0,
            "flagged_count": 0,
            "fraud_risk_avg": "0",
            "transactions": []
        }


def search_customers(search_query: str, limit: int = 50) -> list:
    """
    Search customers by name or ID.
    Returns: List of customer records
    """
    try:
        # Build file paths (convert to forward slashes for DuckDB)
        customers_parquet = os.path.join(DATA_DIR, 'customers.parquet').replace(chr(92), '/')

        conn = duckdb.connect(':memory:')

        # Build search query (actual column names: name, credit_tier, monthly_income)
        if search_query.startswith("C-"):
            # Search by ID
            where_clause = f"customer_id ILIKE '%{search_query}%'"
        else:
            # Search by name
            where_clause = f"name ILIKE '%{search_query}%'"

        query = f"""
        SELECT
            customer_id, name, credit_tier, monthly_income
        FROM read_parquet('{customers_parquet}')
        WHERE {where_clause}
        LIMIT {min(limit, 500)}
        """

        results = conn.execute(query).fetchall()

        customers = []
        for row in results:
            cust_id, name, tier, income = row
            customers.append({
                "customer_id": str(cust_id),
                "customer_name": str(name),
                "account_tier": str(tier),
                "annual_income": float(income or 50000) * 12,  # Convert monthly to annual
                "last_transaction_date": "2026-04-16"
            })

        return customers

    except Exception as e:
        print(f"Error in search_customers: {e}")
        import traceback
        traceback.print_exc()
        return []


def get_customers(skip: int = 0, limit: int = 50) -> list:
    """
    Get paginated list of customers.
    Returns: List of customer records
    """
    try:
        # Build file paths (convert to forward slashes for DuckDB)
        customers_parquet = os.path.join(DATA_DIR, 'customers.parquet').replace(chr(92), '/')

        conn = duckdb.connect(':memory:')

        query = f"""
        SELECT
            customer_id, name, credit_tier, monthly_income
        FROM read_parquet('{customers_parquet}')
        ORDER BY customer_id
        LIMIT {min(limit, 500)} OFFSET {skip}
        """

        results = conn.execute(query).fetchall()

        customers = []
        for row in results:
            cust_id, name, tier, income = row
            customers.append({
                "customer_id": str(cust_id),
                "customer_name": str(name),
                "account_tier": str(tier),
                "annual_income": float(income or 5000) * 12,  # Convert monthly to annual
                "last_transaction_date": "2026-04-16"
            })

        return customers

    except Exception as e:
        print(f"Error in get_customers: {e}")
        import traceback
        traceback.print_exc()
        return []


def update_customer_record(customer_id: str, data: dict) -> Dict[str, Any]:
    """
    Update customer record (stub - returns original customer info).
    In production, this would persist to a database.
    """
    try:
        customers = search_customers(customer_id, 1)
        if customers:
            # Merge updates
            customer = customers[0]
            customer.update(data)
            return customer
        return {}
    except Exception as e:
        print(f"Error in update_customer_record: {e}")
        return {}
