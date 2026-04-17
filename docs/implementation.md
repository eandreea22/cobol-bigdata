# Implementation Reference Guide

## Module-by-Module Overview

### COBOL Programs

| Program | Input | Output | Key Logic |
|---------|-------|--------|-----------|
| CUSTOMER-LOOKUP | customer_id | 145-byte CUSTOMER-REC | Calls python/customer_360.py, parses risk score |
| LOAN-PROCESS | customer_id, amount, term, purpose | 51-byte LOAN-REC | Calculates DTI, determines eligibility |
| FRAUD-CHECK | customer_id, amount, mcc, location, timestamp, channel | 78-byte FRAUD-REC | Computes 6-factor fraud score, classifies risk |
| CUSTOMER-UPDATE | Input file path | Validation response | Validates fields, persists to Parquet |

### Python Analytics Scripts

| Script | Input | Output | Algorithm |
|--------|-------|--------|-----------|
| customer_360.py | customer_id | 145-byte CUSTOMER-REC | Risk score (6 factors, 0–999) |
| loan_scoring.py | customer_id, amount, term, purpose | 51-byte LOAN-REC | Credit score (300–850), DTI calculation |
| fraud_detect.py | customer_id, amount, mcc, location, timestamp, channel | 78-byte FRAUD-REC | Fraud score (6 checks, 0–100) |
| fraud_batch_analysis.py | customer_id | Pipe-delimited transaction list | Scores all transactions with fraud labels |
| customer_update.py | customer_id, name, email, city, street, income | "code\|message" | Validates, updates customers.parquet |

### IPC Formatter (python/utils/ipc_formatter.py)

```python
def format_pic_x(value, length):
    """Left-justify alphanumeric, space-pad"""
    return str(value).ljust(length)[:length]

def format_pic_9(value, int_digits, dec_digits=0):
    """Right-justify numeric, zero-pad (no decimal point)"""
    scaled = int(abs(value) * (10 ** dec_digits))
    return str(scaled).zfill(int_digits + dec_digits)[-(int_digits + dec_digits):]
```

### Parser Reference (ui/parse.py)

8 parser functions decode all IPC and pipe-delimited outputs:
- `parse_customer_360(raw)` → Dict (name, balance in $, txn_count, avg_monthly, risk_score, date)
- `parse_loan_scoring(raw)` → Dict (credit_score, eligible, int_rate as %, max_amount, reason)
- `parse_fraud_detect(raw)` → Dict (risk_level, fraud_score, flags list, recommendation)
- `parse_customer_search(raw)` → List[Dict] (customer_id, name, city, email)
- `parse_customer_list(raw)` → (List[Dict], total_count)
- `parse_fraud_batch_analysis(raw)` → Dict (summary, transactions list)
- `parse_customer_update(raw)` → Dict (code, message, success bool)
- `parse_customer_transactions(raw)` → Dict (count, transactions list)

**Numeric decoding example:**
```python
# 145-byte CUSTOMER-REC
balance = int(raw[50:62]) / 100.0  # 12-digit string ÷ 100 = dollars
avg_monthly = int(raw[70:80]) / 100.0
```

---

## API Reference (FastAPI)

### Endpoints

```
GET    /health
GET    /customer-360/{customer_id}          → Customer360Response
POST   /loan-assessment                      → LoanAssessmentResponse
POST   /fraud-detection                      → FraudDetectionResponse
GET    /fraud-batch/{customer_id}?limit=N   → BatchFraudResponse
GET    /customers?search=&skip=0&limit=100  → CustomersListResponse
GET    /customers/{customer_id}              → CustomerRecord
PUT    /customers/{customer_id}              → CustomerRecord (stub)
GET    /transactions/{customer_id}?limit=N   → {"total", "transactions": [...]}
```

All endpoints delegate to `backend/wrappers.py` functions.

---

## UI Interaction Patterns

### Streamlit (ui/app.py)

**4 pages with consistent search pattern:**
1. Search widget → Name-based customer lookup
2. Click customer in dropdown
3. Page auto-loads customer data (no second click needed)
4. View/edit data in full-width cards

**Key components:**
- Sidebar navigation (radio buttons styled as links)
- Dark navy + cyan color scheme
- CSS injected via st.markdown(..., unsafe_allow_html=True)
- st.data_editor for inline table edits

### React (frontend/)

**4 pages with SearchWidget component:**
1. `<SearchWidget pageKey="c360" onSelect={(id, name) => handleFetch(id)} />`
2. Selected customer shown as badge + "Change" button
3. Page auto-fetches data on selection
4. Cross-page navigation via App.tsx preSelectedCustomerId state

**Key components:**
- SearchWidget: Reusable name search + selection
- MetricCard: Numeric display with icon + color
- StatusCard: Approval/decline decision display
- Layout + Grid: Responsive component containers

---

## Running Components

### COBOL (Compile & Run)
```bash
cd cobol && make customer-lookup
./customer-lookup "C-00001"  # Outputs profile card to stdout
```

### Python Scripts (Direct)
```bash
python python/customer_360.py C-00001
python python/loan_scoring.py C-00001 15000 36 PERS
python python/fraud_detect.py C-00001 500 5411 Manhattan "2026-04-17T10:30:00" POS
```

### Streamlit UI
```bash
streamlit run ui/app.py  # Opens http://localhost:8501
```

### React UI
```bash
cd frontend && npm run dev  # Opens http://localhost:3000
```

### FastAPI Backend
```bash
cd backend && python main.py  # Runs http://localhost:8000
```

---

## Algorithm Details

### Risk Score (customer_360.py)

**Three additive factors (0–999 scale):**
- **Frequency:** 0 txns=300, <12=250, <50=200, <100=100, <200=50, else=10
- **Amount:** >$5000=400, >$2000=300, >$1000=200, >$500=100, >$100=30, else=0
- **Recency (days):** 0=0, ≤7=10, ≤30=50, ≤90=150, ≤365=250, else=300

### Credit Score (loan_scoring.py)

**Five weighted factors (300–850):**
- Payment history (35%), Credit utilization (30%), Credit length (15%), New credit (10%), Credit mix (10%)
- Raw score (0–1) → 300 + raw * 550

**Eligibility:** score ≥ 650 AND DTI < 0.43 AND no defaults in 730 days

### Fraud Score (fraud_detect.py)

**Six additive checks (0–100):**
- Amount anomaly (z-score > 3σ): +35
- Geographic anomaly: +25
- High velocity 1h (≥5): +20
- High velocity 24h (≥20): +10
- Category anomaly: +15
- Unusual hour: +5

**Classification:** LOW (<40), MEDIUM (40–70), HIGH (≥70)

---

**Last Updated:** 2026-04-17
