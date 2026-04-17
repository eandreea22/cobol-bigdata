"""
FastAPI Backend for BankCore Analytics
Wraps existing Python analytics scripts into REST APIs
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import sys
import os

# Add parent directory to path to import existing Python scripts
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from wrappers import (
    analyze_customer_360,
    score_loan,
    detect_fraud,
    get_customer_transactions,
    analyze_fraud_batch,
    search_customers,
    get_customers,
    update_customer_record
)

# Initialize FastAPI app
app = FastAPI(
    title="BankCore Analytics API",
    description="REST API for banking analytics system",
    version="1.0.0"
)

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Request/Response Models
# ============================================================================

class Customer360Response(BaseModel):
    customer_name: str
    account_balance: float
    transaction_count: int
    avg_monthly: float
    risk_score: int
    last_transaction_date: str
    return_code: str

class LoanAssessmentRequest(BaseModel):
    customer_id: str
    amount: float
    term_months: int
    purpose_code: str

class LoanAssessmentResponse(BaseModel):
    credit_score: int
    eligible: str  # 'Y' or 'N'
    interest_rate: float
    max_amount: float
    reject_reason: str
    return_code: str

class FraudDetectionRequest(BaseModel):
    customer_id: str
    amount: float
    mcc: str
    location: str
    timestamp: str
    channel: str

class FraudDetectionResponse(BaseModel):
    fraud_risk: str  # 'LOW', 'MEDIUM', 'HIGH'
    fraud_score: int
    flags: str
    recommendation: str
    return_code: str

class Transaction(BaseModel):
    transaction_id: str
    amount: float
    fraud_risk: str
    fraud_score: int
    timestamp: str
    location: str
    category: str

class BatchFraudResponse(BaseModel):
    customer_id: str
    total_transactions: int
    flagged_count: int
    fraud_risk_avg: str
    transactions: List[Transaction]

class CustomerRecord(BaseModel):
    customer_id: str
    customer_name: str
    account_tier: str
    annual_income: float
    last_transaction_date: str

class CustomersListResponse(BaseModel):
    total: int
    customers: List[CustomerRecord]

# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "BankCore Analytics API",
        "version": "1.0.0"
    }

# ============================================================================
# Customer 360° Endpoint
# ============================================================================

@app.get("/customer-360/{customer_id}", response_model=Customer360Response)
async def get_customer_360(customer_id: str):
    """
    Get comprehensive customer profile (360° view)

    Args:
        customer_id: Customer ID (e.g., C-00001)

    Returns:
        Customer360Response with balance, transactions, risk score
    """
    try:
        result = analyze_customer_360(customer_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Loan Assessment Endpoint
# ============================================================================

@app.post("/loan-assessment", response_model=LoanAssessmentResponse)
async def assess_loan(request: LoanAssessmentRequest):
    """
    Assess loan eligibility and calculate rates

    Args:
        request: LoanAssessmentRequest with customer, amount, term, purpose

    Returns:
        LoanAssessmentResponse with credit score, eligibility, rate
    """
    try:
        result = score_loan(
            request.customer_id,
            request.amount,
            request.term_months,
            request.purpose_code
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Fraud Detection Endpoints
# ============================================================================

@app.post("/fraud-detection", response_model=FraudDetectionResponse)
async def analyze_transaction_fraud(request: FraudDetectionRequest):
    """
    Analyze single transaction for fraud risk

    Args:
        request: FraudDetectionRequest with transaction details

    Returns:
        FraudDetectionResponse with risk level and score
    """
    try:
        result = detect_fraud(
            request.customer_id,
            request.amount,
            request.mcc,
            request.location,
            request.timestamp,
            request.channel
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/fraud-batch/{customer_id}", response_model=BatchFraudResponse)
async def batch_fraud_analysis(customer_id: str, limit: Optional[int] = None):
    """
    Analyze all transactions for a customer for fraud risk

    Args:
        customer_id: Customer ID
        limit: Maximum number of transactions to analyze

    Returns:
        BatchFraudResponse with all transactions and risk metrics
    """
    try:
        result = analyze_fraud_batch(customer_id, limit)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Customer Management Endpoints
# ============================================================================

@app.get("/customers", response_model=CustomersListResponse)
async def list_customers(search: Optional[str] = None, skip: int = 0, limit: int = 100):
    """
    List customers with optional search

    Args:
        search: Search query (name or ID)
        skip: Offset for pagination
        limit: Number of results to return

    Returns:
        CustomersListResponse with list of customers
    """
    try:
        if search:
            results = search_customers(search, limit)
        else:
            results = get_customers(skip, limit)

        return {
            "total": len(results),
            "customers": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/customers/{customer_id}", response_model=CustomerRecord)
async def get_customer(customer_id: str):
    """
    Get single customer details

    Args:
        customer_id: Customer ID

    Returns:
        CustomerRecord with customer details
    """
    try:
        result = search_customers(customer_id, 1)
        if not result:
            raise HTTPException(status_code=404, detail="Customer not found")
        return result[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/customers/{customer_id}", response_model=CustomerRecord)
async def update_customer(customer_id: str, data: dict):
    """
    Update customer record

    Args:
        customer_id: Customer ID
        data: Fields to update

    Returns:
        Updated CustomerRecord
    """
    try:
        result = update_customer_record(customer_id, data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Transaction Endpoints
# ============================================================================

@app.get("/transactions/{customer_id}")
async def get_transactions(customer_id: str, limit: Optional[int] = None):
    """
    Get all transactions for a customer

    Args:
        customer_id: Customer ID
        limit: Maximum number of transactions to return

    Returns:
        List of transactions
    """
    try:
        transactions = get_customer_transactions(customer_id, limit)
        return {
            "customer_id": customer_id,
            "total": len(transactions),
            "transactions": transactions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Root Endpoint
# ============================================================================

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "BankCore Analytics API",
        "docs": "http://localhost:8000/docs",
        "version": "1.0.0"
    }

# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return {
        "error": str(exc),
        "status": "error"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
