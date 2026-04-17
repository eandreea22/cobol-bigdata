# 🏗️ BankCore Analytics: Architecture & Integration Guide

This document explains the new **React + FastAPI** architecture and how it replaces the Streamlit UI while preserving all core analytics logic.

---

## 📊 System Architecture

### Before (Streamlit)
```
User Browser
    ↓
Streamlit App (UI + Logic Combined)
    ↓
Python Analytics Scripts
    ↓
DuckDB/Parquet Data
```

### After (React + FastAPI)
```
┌─────────────────────────────────────────┐
│        React Frontend (Port 3000)       │
│  • Dashboard                            │
│  • Loan Assessment                      │
│  • Fraud Detection                      │
│  • Customer Management                  │
│  • Modern UI with Design System         │
└────────────────┬────────────────────────┘
                 │ REST API Calls (JSON)
                 │ Axios HTTP Client
                 ▼
┌─────────────────────────────────────────┐
│        FastAPI Backend (Port 8000)      │
│  • /customer-360/{id}                   │
│  • /loan-assessment                     │
│  • /fraud-detection                     │
│  • /fraud-batch/{id}                    │
│  • /customers                           │
│  • /transactions/{id}                   │
└────────────────┬────────────────────────┘
                 │ Calls Existing Python Scripts
                 │ (UNCHANGED)
                 ▼
┌─────────────────────────────────────────┐
│  Python Analytics Layer (No Changes)    │
│  • customer_360.py                      │
│  • loan_scoring.py                      │
│  • fraud_detect.py                      │
│  • Utilities & helpers                  │
└────────────────┬────────────────────────┘
                 │ DuckDB Queries
                 ▼
┌─────────────────────────────────────────┐
│  Data Layer: DuckDB + Parquet           │
│  • customers.parquet (100K)             │
│  • loans.parquet (500K)                 │
│  • transactions/ (10M)                  │
│  • fraud_labels.parquet (50K)           │
└─────────────────────────────────────────┘
```

---

## 🔄 Request Flow Example: Customer 360°

### Frontend Flow

**1. User Input (React Component)**
```tsx
// src/pages/Dashboard.tsx
const handleFetch = async () => {
  setLoading(true)
  try {
    const result = await apiClient.getCustomer360('C-00001')
    setData(result)
  } catch (err) {
    setError(err.message)
  }
  setLoading(false)
}
```

**2. API Client Call (Axios)**
```typescript
// src/api/client.ts
async getCustomer360(customerId: string) {
  const response = await this.client.get(`/customer-360/${customerId}`)
  return response.data
}
```

**3. HTTP Request**
```
GET http://localhost:8000/api/customer-360/C-00001
```

### Backend Flow

**4. FastAPI Endpoint**
```python
# backend/main.py
@app.get("/customer-360/{customer_id}", response_model=Customer360Response)
async def get_customer_360(customer_id: str):
    result = analyze_customer_360(customer_id)
    return result
```

**5. Call Existing Analytics Script**
```python
# backend/main.py imports:
from python.customer_360 import analyze_customer_360

# This function:
# - Takes customer_id
# - Queries DuckDB for customer data
# - Queries DuckDB for transaction data
# - Calculates metrics
# - Returns fixed-width formatted response
```

**6. DuckDB Queries**
```sql
-- Query customers.parquet
SELECT * FROM 'data/customers.parquet' WHERE customer_id = 'C-00001'

-- Query transactions/ (partitioned by date)
SELECT * FROM 'data/transactions/**/*.parquet' WHERE customer_id = 'C-00001'
```

**7. Response Back to Frontend**
```json
{
  "customer_name": "John Doe",
  "account_balance": 12450.50,
  "transaction_count": 247,
  "avg_monthly": 3500.00,
  "risk_score": 234,
  "last_transaction_date": "2026-04-17",
  "return_code": "00"
}
```

**8. Frontend Renders**
```tsx
<MetricCard label="Balance" value={`$${data.account_balance}`} />
<MetricCard label="Risk Score" value={data.risk_score} />
// ... UI updates with data
```

---

## 🔌 API Endpoints Reference

### Customer 360° Analytics

```
Endpoint: GET /customer-360/{customer_id}

Request:
  GET http://localhost:8000/api/customer-360/C-00001

Response (200 OK):
{
  "customer_name": "Margaret Johnson",
  "account_balance": 24750.50,
  "transaction_count": 312,
  "avg_monthly": 4250.00,
  "risk_score": 145,
  "last_transaction_date": "2026-04-16",
  "return_code": "00"
}

Error Response (404):
{
  "detail": "Customer not found"
}
```

### Loan Assessment

```
Endpoint: POST /loan-assessment

Request Body:
{
  "customer_id": "C-00001",
  "amount": 25000,
  "term_months": 48,
  "purpose_code": "HOME"
}

Response (200 OK):
{
  "credit_score": 720,
  "eligible": "Y",
  "interest_rate": 4.8,
  "max_amount": 100000,
  "reject_reason": "",
  "return_code": "00"
}

Error Response (400):
{
  "detail": "Invalid loan parameters"
}
```

### Fraud Detection (Single Transaction)

```
Endpoint: POST /fraud-detection

Request Body:
{
  "customer_id": "C-00001",
  "amount": 500.00,
  "mcc": "5411",
  "location": "Bucharest",
  "timestamp": "2026-04-17T14:30:00",
  "channel": "POS"
}

Response (200 OK):
{
  "fraud_risk": "LOW",
  "fraud_score": 85,
  "flags": "",
  "recommendation": "APPROVE",
  "return_code": "00"
}

Possible Fraud Risks: LOW, MEDIUM, HIGH
```

### Fraud Detection (Batch Analysis)

```
Endpoint: GET /fraud-batch/{customer_id}?limit=100

Request:
  GET http://localhost:8000/api/fraud-batch/C-00001?limit=200

Response (200 OK):
{
  "customer_id": "C-00001",
  "total_transactions": 2847,
  "flagged_count": 12,
  "fraud_risk_avg": "245",
  "transactions": [
    {
      "transaction_id": "TXN-2847-01",
      "amount": 500.00,
      "fraud_risk": "LOW",
      "fraud_score": 85,
      "timestamp": "2026-04-17T14:30:00",
      "location": "Bucharest",
      "category": "Groceries"
    },
    {
      "transaction_id": "TXN-2847-02",
      "amount": 5000.00,
      "fraud_risk": "MEDIUM",
      "fraud_score": 425,
      "timestamp": "2026-04-17T15:45:00",
      "location": "New York",
      "category": "Travel"
    },
    ...
  ]
}
```

### Customer List & Search

```
Endpoint: GET /customers

Query Parameters:
  - search: Optional search string (name or ID)
  - skip: Pagination offset (default: 0)
  - limit: Results per page (default: 50)

Request:
  GET http://localhost:8000/api/customers?search=John&limit=10

Response (200 OK):
{
  "total": 3,
  "customers": [
    {
      "customer_id": "C-00001",
      "customer_name": "John Doe",
      "account_tier": "GOLD",
      "annual_income": 65000,
      "last_transaction_date": "2026-04-16"
    },
    {
      "customer_id": "C-00215",
      "customer_name": "Johnny Depp",
      "account_tier": "SILVER",
      "annual_income": 55000,
      "last_transaction_date": "2026-04-15"
    },
    ...
  ]
}
```

### Customer Details

```
Endpoint: GET /customers/{customer_id}

Request:
  GET http://localhost:8000/api/customers/C-00001

Response (200 OK):
{
  "customer_id": "C-00001",
  "customer_name": "John Doe",
  "account_tier": "GOLD",
  "annual_income": 65000,
  "last_transaction_date": "2026-04-16"
}
```

### Update Customer

```
Endpoint: PUT /customers/{customer_id}

Request Body:
{
  "annual_income": 75000,
  "account_tier": "GOLD"
}

Response (200 OK):
{
  "customer_id": "C-00001",
  "customer_name": "John Doe",
  "account_tier": "GOLD",
  "annual_income": 75000,
  "last_transaction_date": "2026-04-16"
}
```

### Get Customer Transactions

```
Endpoint: GET /transactions/{customer_id}

Query Parameters:
  - limit: Maximum transactions to return

Request:
  GET http://localhost:8000/api/transactions/C-00001?limit=100

Response (200 OK):
{
  "customer_id": "C-00001",
  "total": 2847,
  "transactions": [
    {
      "transaction_id": "TXN-001",
      "amount": 500.00,
      "timestamp": "2026-04-17T14:30:00",
      "location": "Bucharest",
      "category": "Groceries",
      "fraud_risk": "LOW"
    },
    ...
  ]
}
```

---

## 💻 Frontend Integration Examples

### Example 1: Fetch Customer 360° Data

```typescript
import { apiClient } from '../api/client'

async function loadCustomerData(customerId: string) {
  try {
    const data = await apiClient.getCustomer360(customerId)
    
    console.log(`Customer: ${data.customer_name}`)
    console.log(`Balance: $${(data.account_balance / 100).toFixed(2)}`)
    console.log(`Risk Score: ${data.risk_score}`)
    
    return data
  } catch (error) {
    console.error('Failed to load customer:', error)
  }
}
```

### Example 2: Assess Loan Eligibility

```typescript
async function assessLoan(
  customerId: string,
  loanAmount: number,
  termMonths: number
) {
  const result = await apiClient.assessLoan(
    customerId,
    loanAmount,
    termMonths,
    'PERS' // Personal loan
  )
  
  if (result.eligible === 'Y') {
    console.log(`✓ APPROVED`)
    console.log(`Credit Score: ${result.credit_score}`)
    console.log(`Interest Rate: ${result.interest_rate}%`)
    console.log(`Max Approved: $${result.max_amount}`)
  } else {
    console.log(`✗ DECLINED`)
    console.log(`Reason: ${result.reject_reason}`)
  }
}
```

### Example 3: Analyze Fraud Risk (Batch)

```typescript
async function analyzeCustomerFraud(customerId: string) {
  const result = await apiClient.batchFraudAnalysis(customerId, 200)
  
  console.log(`Total Transactions: ${result.total_transactions}`)
  console.log(`Flagged: ${result.flagged_count}`)
  console.log(`Avg Risk: ${result.fraud_risk_avg}/999`)
  
  // Group by risk level
  const byRisk = {
    HIGH: result.transactions.filter(t => t.fraud_risk === 'HIGH'),
    MEDIUM: result.transactions.filter(t => t.fraud_risk === 'MEDIUM'),
    LOW: result.transactions.filter(t => t.fraud_risk === 'LOW')
  }
  
  console.log(`High Risk Transactions: ${byRisk.HIGH.length}`)
  byRisk.HIGH.forEach(t => {
    console.log(`  - ${t.transaction_id}: $${t.amount} in ${t.location}`)
  })
}
```

### Example 4: Search Customers

```typescript
async function findCustomers(searchQuery: string) {
  const result = await apiClient.getCustomers(searchQuery)
  
  console.log(`Found ${result.total} customers:`)
  result.customers.forEach(customer => {
    console.log(`  - ${customer.customer_name} (${customer.account_tier})`)
  })
  
  return result.customers
}
```

---

## 🔗 Frontend-to-Backend Integration Points

### 1. Dashboard Page → Customer 360° API

**File:** `src/pages/Dashboard.tsx`

```tsx
import { apiClient } from '../api/client'

const handleFetch = async () => {
  const result = await apiClient.getCustomer360(customerId)
  setData(result)
}
```

**Backend:** `backend/main.py` → `GET /customer-360/{id}`

### 2. Loan Assessment Page → Loan API

**File:** `src/pages/LoanAssessment.tsx`

```tsx
const handleSubmit = async (e: React.FormEvent) => {
  const res = await apiClient.assessLoan(
    formData.customerId,
    parseFloat(formData.amount),
    parseInt(formData.term),
    formData.purpose
  )
}
```

**Backend:** `backend/main.py` → `POST /loan-assessment`

### 3. Fraud Detection Page → Fraud APIs

**File:** `src/pages/FraudDetection.tsx`

```tsx
const result = await apiClient.batchFraudAnalysis(customerId)
// Display transactions, filter by risk, etc.
```

**Backend:** 
- `POST /fraud-detection` (single transaction)
- `GET /fraud-batch/{id}` (all transactions)

### 4. Customer Management → Customer APIs

**File:** `src/pages/CustomerManagement.tsx`

```tsx
const result = await apiClient.getCustomers(searchQuery)
const details = await apiClient.getCustomerDetails(customerId)
await apiClient.updateCustomer(customerId, newData)
```

**Backend:**
- `GET /customers`
- `GET /customers/{id}`
- `PUT /customers/{id}`

---

## 🏛️ Data Flow Through Layers

### Flow: Get Customer 360°

```
┌────────────────────────────────────────┐
│ React Component (src/pages/Dashboard) │
│ User clicks "Search" for C-00001       │
└──────────────┬─────────────────────────┘
               │ Call apiClient.getCustomer360('C-00001')
               ▼
┌────────────────────────────────────────┐
│ Axios Client (src/api/client.ts)      │
│ GET /api/customer-360/C-00001          │
└──────────────┬─────────────────────────┘
               │ HTTP Request
               ▼
┌────────────────────────────────────────┐
│ Vite Dev Server (localhost:5173)      │
│ Proxy to backend /api → localhost:8000 │
└──────────────┬─────────────────────────┘
               │ HTTP GET
               ▼
┌────────────────────────────────────────┐
│ FastAPI Backend (backend/main.py)     │
│ @app.get("/customer-360/{customer_id}")│
│ Call analyze_customer_360('C-00001')   │
└──────────────┬─────────────────────────┘
               │ Call Python function
               ▼
┌────────────────────────────────────────┐
│ Python Analytics (python/customer_360) │
│ Query: SELECT * FROM customers WHERE.. │
│ Query: SELECT * FROM transactions..    │
│ Calculate: balance, count, avg, risk   │
└──────────────┬─────────────────────────┘
               │ DuckDB execution
               ▼
┌────────────────────────────────────────┐
│ DuckDB (in-process)                    │
│ Read from parquet files                │
│ • data/customers.parquet               │
│ • data/transactions/**/*.parquet       │
└──────────────┬─────────────────────────┘
               │ Return results
               ▼
┌────────────────────────────────────────┐
│ Python Analytics                       │
│ Format as Customer360Response           │
│ Return to FastAPI                      │
└──────────────┬─────────────────────────┘
               │ JSON response
               ▼
┌────────────────────────────────────────┐
│ FastAPI Backend                        │
│ HTTP 200 response                      │
│ {                                      │
│   "customer_name": "...",              │
│   "account_balance": 12450.50,         │
│   ...                                  │
│ }                                      │
└──────────────┬─────────────────────────┘
               │ HTTP Response
               ▼
┌────────────────────────────────────────┐
│ Axios Client                           │
│ Parse JSON response                    │
│ Return to React component              │
└──────────────┬─────────────────────────┘
               │ setData(result)
               ▼
┌────────────────────────────────────────┐
│ React Component                        │
│ Render UI with data                    │
│ • MetricCard for balance               │
│ • MetricCard for risk score            │
│ • Profile card with name               │
│ • Activity summary                     │
└────────────────────────────────────────┘
```

---

## 🔐 No Changes to Core Logic

The key innovation: **COBOL + Python analytics remain untouched.**

```
OLD (Streamlit):
  User Input (Web Browser)
      ↓
  Streamlit UI Layer (Python/HTML)
      ↓
  Analytics Scripts (Python)
      ↓
  DuckDB + Parquet

NEW (React + FastAPI):
  User Input (React/Browser)
      ↓ (JSON via REST)
  FastAPI Wrapper
      ↓ (Python function calls)
  Analytics Scripts (SAME Python) ← NO CHANGES
      ↓
  DuckDB + Parquet (SAME)
```

The Python scripts (`customer_360.py`, `loan_scoring.py`, `fraud_detect.py`) remain **identical**. The FastAPI backend simply wraps them as HTTP endpoints.

---

## 🚀 Deployment Architecture

### Local Development
```
Frontend: http://localhost:3000 (npm run dev)
Backend: http://localhost:8000 (python main.py)
```

### Production Deployment
```
┌──────────────────────────────────────────────────────────┐
│ CDN / Vercel / Netlify (Frontend)                        │
│ • Compiled React (HTML/CSS/JS)                           │
│ • Static assets cached globally                          │
│ • CORS enabled for API requests                          │
└─────────────────────┬──────────────────────────────────┘
                      │ HTTPS API Calls
                      ▼
┌──────────────────────────────────────────────────────────┐
│ Cloud Provider (AWS/GCP/Azure) Backend                   │
│ • Docker container running FastAPI                       │
│ • Load balancer / reverse proxy                          │
│ • Auto-scaling based on traffic                          │
│ • Health checks & monitoring                             │
└─────────────────────┬──────────────────────────────────┘
                      │ Imports Python Scripts
                      ▼
┌──────────────────────────────────────────────────────────┐
│ Data Layer                                               │
│ • S3 / Cloud Storage (Parquet files)                     │
│ • In-process DuckDB (queries parquet)                    │
│ • Optional: PostgreSQL for cached results                │
└──────────────────────────────────────────────────────────┘
```

---

## 📈 Performance Characteristics

### Request Latency

| Operation | Typical Time | Bottleneck |
|-----------|------------|-----------|
| Customer 360° | 200-500ms | DuckDB query (10M+ records) |
| Loan Assessment | 50-100ms | Credit scoring algorithm |
| Fraud Detection (single) | 100-200ms | Anomaly detection |
| Fraud Batch (200 txns) | 500-1000ms | DuckDB partitioned query |
| Customer Search | 100-300ms | Index scan + filter |

### Optimization Opportunities

1. **Frontend caching** — Axios + React Query for request deduplication
2. **Backend caching** — Redis for frequently queried customers
3. **Data optimization** — Parquet statistics for faster pushdown
4. **Query optimization** — DuckDB prepared statements for repeat queries

---

## ✅ Architecture Advantages

✨ **Separation of Concerns**
- Frontend: UI, routing, animations
- Backend: API, validation, orchestration
- Analytics: Business logic (unchanged)

⚡ **Scalability**
- Frontend deployed to CDN (static assets)
- Backend scales independently (auto-scaling)
- Analytics layer remains lightweight (no UI overhead)

🔧 **Maintainability**
- Easy to add new pages / endpoints
- Analytics changes don't affect UI
- Clear API contracts via Swagger docs

🎨 **User Experience**
- Modern, responsive UI
- Fast page transitions
- Real-time feedback (loading states)

🛡️ **Reliability**
- Error boundaries in React
- Proper HTTP status codes
- Fallback error handling

---

## 🔗 Integration Checklist

- [x] React frontend with 4 pages
- [x] FastAPI backend with all endpoints
- [x] Axios client with all API methods
- [x] Design system (colors, fonts, animations)
- [x] Request/response models (Pydantic)
- [x] CORS configuration
- [x] Swagger API documentation
- [x] Error handling (frontend + backend)
- [x] Proxy configuration (frontend to backend)
- [x] All existing Python scripts imported (unchanged)

---

This architecture represents the **ideal balance** between modern frontend development, clean API design, and preserving battle-tested analytics logic. 🎯
