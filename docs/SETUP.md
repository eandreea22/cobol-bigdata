# 🚀 BankCore Analytics: Production Setup Guide

This guide walks you through setting up and running the complete React + FastAPI banking analytics platform.

## 📋 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     React Frontend (Port 3000)                  │
│                     • Sidebar Navigation                        │
│                     • 4 Pages (Dashboard, Loans, Fraud, Mgmt)   │
│                     • Design System (Syne + Epilogue)           │
│                     • Real-time UI Updates                      │
└──────────────────────────┬──────────────────────────────────────┘
                           │ REST API (JSON)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              FastAPI Backend (Port 8000)                        │
│              • Customer 360° Endpoint                           │
│              • Loan Assessment Endpoint                         │
│              • Fraud Detection Endpoints                        │
│              • Customer Management Endpoints                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Imports & Wraps
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│           Existing Python Analytics Layer (No Changes)          │
│           • customer_360.py                                     │
│           • loan_scoring.py                                     │
│           • fraud_detect.py                                     │
│           • Batch analysis & search utilities                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │ DuckDB Queries
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│        Data Layer: DuckDB + Apache Parquet                      │
│        • customers.parquet (100K)                               │
│        • loans.parquet (500K)                                   │
│        • transactions/ (10M, date-partitioned)                  │
│        • fraud_labels.parquet (50K)                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Prerequisites

- **Node.js** 18+ (for React frontend)
- **Python** 3.11+ (for FastAPI backend)
- **Git** (for version control)

### Install Node.js

**Mac/Linux:**
```bash
# Using Homebrew (Mac)
brew install node

# Using apt (Linux/Ubuntu)
sudo apt install nodejs npm
```

**Windows:**
Download from https://nodejs.org/ (LTS version)

### Install Python

**Ubuntu/Debian:**
```bash
sudo apt install python3.11 python3.11-venv python3-pip
```

**Mac:**
```bash
brew install python@3.11
```

**Windows:**
Download from https://www.python.org/downloads/

---

## 📦 Setup Instructions

### Step 1: Install Frontend Dependencies

```bash
cd frontend
npm install
```

This installs:
- React 18
- Vite (fast dev server)
- Framer Motion (animations)
- Recharts (charting)
- Axios (HTTP client)

### Step 2: Install Backend Dependencies

```bash
cd backend
python3 -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### Step 3: Ensure Data is Generated

Make sure the data files exist:

```bash
# From project root
python3 data/generate_synthetic.py

# Verify files exist:
ls -la data/*.parquet
ls -la data/transactions/
```

---

## 🚀 Running the System

### Terminal 1: Start Backend API

```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python3 main.py
```

Output should show:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

The API is now running at **http://localhost:8000**

- **API Docs:** http://localhost:8000/docs (interactive Swagger UI)
- **Health Check:** http://localhost:8000/health

### Terminal 2: Start Frontend Development Server

```bash
cd frontend
npm run dev
```

Output should show:
```
  VITE v5.0.0  ready in 1234 ms

  ➜  Local:   http://localhost:3000/
  ➜  press h to show help
```

The frontend is now running at **http://localhost:3000**

### Open in Browser

Navigate to **http://localhost:3000** to access the complete banking analytics platform.

---

## 🎨 Frontend Structure

```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── Card.tsx         # Card & metric card components
│   │   ├── Button.tsx       # Button variants
│   │   ├── Layout.tsx       # Sidebar, Header, Grid layout
│   │   └── *.css            # Component styles
│   ├── pages/               # Full pages
│   │   ├── Dashboard.tsx    # Customer 360° view
│   │   ├── LoanAssessment.tsx
│   │   ├── FraudDetection.tsx
│   │   ├── CustomerManagement.tsx
│   │   └── *.css            # Page-specific styles
│   ├── api/
│   │   └── client.ts        # API client (Axios wrapper)
│   ├── styles/
│   │   └── globals.css      # Design system & global styles
│   ├── App.tsx              # Main app component
│   └── main.tsx             # React entry point
├── index.html               # HTML template
├── package.json
└── vite.config.ts           # Vite configuration
```

### Key Frontend Files

| File | Purpose |
|------|---------|
| `src/styles/globals.css` | Design system (colors, fonts, spacing, animations) |
| `src/api/client.ts` | Axios client with all API methods |
| `src/App.tsx` | Page routing and state management |
| `src/components/*.tsx` | Reusable component library |

---

## 🔌 Backend Structure

```
backend/
├── main.py                  # FastAPI app with all endpoints
├── requirements.txt         # Python dependencies
└── venv/                    # Virtual environment (created on setup)
```

### API Endpoints

#### Customer 360°
```
GET /customer-360/{customer_id}
Response: {
  "customer_name": "John Doe",
  "account_balance": 12450.50,
  "transaction_count": 247,
  "avg_monthly": 3500.00,
  "risk_score": 234,
  "last_transaction_date": "2026-04-17",
  "return_code": "00"
}
```

#### Loan Assessment
```
POST /loan-assessment
Request: {
  "customer_id": "C-00001",
  "amount": 15000,
  "term_months": 36,
  "purpose_code": "PERS"
}
Response: {
  "credit_score": 720,
  "eligible": "Y",
  "interest_rate": 5.2,
  "max_amount": 25000,
  "reject_reason": "",
  "return_code": "00"
}
```

#### Fraud Detection (Single)
```
POST /fraud-detection
Request: {
  "customer_id": "C-00001",
  "amount": 500.00,
  "mcc": "5411",
  "location": "Bucharest",
  "timestamp": "2026-04-17T14:30:00",
  "channel": "POS"
}
Response: {
  "fraud_risk": "LOW",
  "fraud_score": 85,
  "flags": "",
  "recommendation": "APPROVE",
  "return_code": "00"
}
```

#### Fraud Detection (Batch)
```
GET /fraud-batch/{customer_id}?limit=100
Response: {
  "customer_id": "C-00001",
  "total_transactions": 2847,
  "flagged_count": 12,
  "fraud_risk_avg": "245",
  "transactions": [
    {
      "transaction_id": "TXN-001",
      "amount": 500.00,
      "fraud_risk": "LOW",
      "fraud_score": 85,
      "timestamp": "2026-04-17T14:30:00",
      "location": "Bucharest",
      "category": "Groceries"
    },
    ...
  ]
}
```

#### Customers (List & Search)
```
GET /customers?search=John&limit=50
Response: {
  "total": 5,
  "customers": [
    {
      "customer_id": "C-00001",
      "customer_name": "John Doe",
      "account_tier": "GOLD",
      "annual_income": 65000,
      "last_transaction_date": "2026-04-17"
    },
    ...
  ]
}
```

#### Transactions
```
GET /transactions/{customer_id}?limit=100
Response: {
  "customer_id": "C-00001",
  "total": 2847,
  "transactions": [...]
}
```

---

## 🎨 Design System

The frontend uses a cohesive design system:

### Colors
```css
--color-primary: #1a2332        /* Deep indigo */
--color-accent: #00d4ff         /* Vibrant teal */
--color-success: #10b981        /* Emerald */
--color-danger: #ef4444         /* Rose */
--color-warning: #f59e0b        /* Amber */
```

### Typography
- **Display Font:** Syne (bold, geometric, modern)
- **Body Font:** Epilogue (humanist, refined)

### Components
- **Cards:** Default, interactive, minimal variants
- **Buttons:** Primary, secondary, tertiary, danger
- **Metrics:** KPI cards with color coding
- **Status:** Approval/decline visualization

### Animations
- Page transitions (fade + slide up)
- Card hovers (lift + border glow)
- Loading spinners
- Risk meter animations

---

## 🧪 Testing the System

### Manual Testing: Customer 360°

1. Navigate to **Customer 360°** page
2. Enter `C-00001` in search box
3. Click "Search"
4. View:
   - Customer name and avatar
   - Account balance
   - Transaction count
   - Risk score
   - Activity summary

### Manual Testing: Loan Assessment

1. Navigate to **Loan Assessment** page
2. Fill in form:
   - Customer ID: `C-00001`
   - Loan Amount: `15000`
   - Term: `36`
   - Purpose: "Personal Loan"
3. Click "Get Assessment"
4. View:
   - Credit score (300-850)
   - Approval status (APPROVED or DECLINED)
   - Interest rate
   - Maximum approved amount

### Manual Testing: Fraud Detection

1. Navigate to **Fraud Detection** page
2. Enter `C-00001` in search box
3. Click "Analyze Transactions"
4. View:
   - Total transactions analyzed
   - Number flagged
   - Average fraud risk score
   - Detailed transaction table with risk levels

### Manual Testing: Customer Management

1. Navigate to **Management** page
2. Search by name (e.g., "John")
3. Click customer to select
4. View customer details
5. Click "Edit" to modify fields

---

## 🔗 API Testing with Swagger

The FastAPI automatically generates interactive documentation:

1. Open **http://localhost:8000/docs**
2. You'll see all endpoints with:
   - Request/response schemas
   - Try-it-out buttons
   - Example payloads

Try making requests directly from the Swagger UI.

---

## 🛑 Troubleshooting

### Frontend won't connect to API

**Problem:** Error like "Cannot POST /api/customer-360"

**Solution:**
1. Ensure backend is running (`python3 main.py`)
2. Check backend is on port 8000
3. In `frontend/vite.config.ts`, verify proxy settings:
   ```typescript
   proxy: {
     '/api': {
       target: 'http://localhost:8000',
       changeOrigin: true,
       rewrite: (path) => path.replace(/^\/api/, '')
     }
   }
   ```

### 404 errors on API endpoints

**Problem:** `Cannot GET /customer-360`

**Solution:**
- Verify endpoint exists in `backend/main.py`
- Ensure Parquet files exist in `data/` directory
- Regenerate data: `python3 data/generate_synthetic.py`

### Port already in use

**Problem:** `Address already in use: ('0.0.0.0', 8000)`

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill it
kill -9 <PID>

# Or use different port:
python3 main.py  # Edit to specify different port
```

### Dependencies install error

**Problem:** `pip install -r requirements.txt` fails

**Solution:**
```bash
# Upgrade pip
pip install --upgrade pip

# Use Python 3.11 explicitly
python3.11 -m pip install -r requirements.txt

# Or specify versions manually
pip install fastapi==0.108.0 uvicorn==0.25.0
```

---

## 📊 Data Layer Integration

The backend automatically queries the existing data layer:

### Data Files Used

| File | Rows | Purpose |
|------|------|---------|
| `data/customers.parquet` | 100K | Customer profiles |
| `data/loans.parquet` | 500K | Loan history |
| `data/transactions/` | 10M | Transaction records (date-partitioned) |
| `data/fraud_labels.parquet` | 50K | Fraud ground truth |

### No Changes Required

- The backend **imports existing Python scripts unchanged**
- All analytics logic remains in `python/` directory
- DuckDB queries work the same way

---

## 📈 Production Deployment

### Frontend Deployment (Vercel, Netlify, etc.)

```bash
# Build for production
cd frontend
npm run build

# Output: frontend/dist/ (ready to deploy)
```

### Backend Deployment (Heroku, Railway, etc.)

```bash
# Using Gunicorn for production
pip install gunicorn

# Start with Gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

### Environment Variables

Create `.env` files:

**backend/.env**
```
DATABASE_PATH=/path/to/data
LOG_LEVEL=info
API_PORT=8000
```

**frontend/.env**
```
VITE_API_URL=https://api.yourdomain.com
```

---

## 🎯 Next Steps

1. **Frontend Customization:**
   - Modify colors in `src/styles/globals.css`
   - Add new pages in `src/pages/`
   - Create new components in `src/components/`

2. **Backend Enhancements:**
   - Add new endpoints in `backend/main.py`
   - Integrate authentication (JWT tokens)
   - Add request logging and monitoring

3. **Data Integration:**
   - Connect to real banking systems
   - Replace synthetic data with production data
   - Implement data validation and sanitization

---

## 📚 Documentation

- **Frontend Components:** See `src/components/*.tsx` for component library
- **API Docs:** http://localhost:8000/docs (Swagger UI)
- **Design System:** `frontend/src/styles/globals.css`
- **Architecture:** See main `docs/` directory

---

## ✨ Features

✅ **Customer 360°** — Comprehensive customer profiles  
✅ **Loan Assessment** — Real-time eligibility and rates  
✅ **Fraud Detection** — Real-time and batch analysis  
✅ **Customer Management** — Search, view, update profiles  
✅ **Modern UI** — Responsive, animated, production-grade  
✅ **Design System** — Consistent colors, typography, spacing  
✅ **REST API** — Clean, documented endpoints  
✅ **Real Data** — 100K+ customer records, 10M+ transactions  

---

## 💡 Architecture Highlights

### Separation of Concerns

| Layer | Technology | Responsibility |
|-------|-----------|-----------------|
| **Frontend** | React + Vite | UI, routing, state |
| **API** | FastAPI | REST endpoints, request validation |
| **Analytics** | Python | Business logic, analytics algorithms |
| **Data** | DuckDB + Parquet | Query execution, storage |

### Design Philosophy

✨ **Refined Minimalism** — Clean, professional fintech aesthetic  
⚡ **Performance** — Fast page loads, smooth animations  
🎨 **Accessibility** — Semantic HTML, keyboard navigation  
📱 **Responsive** — Works on mobile, tablet, desktop  

---

**Ready to launch?** Open http://localhost:3000 and explore the platform! 🚀
