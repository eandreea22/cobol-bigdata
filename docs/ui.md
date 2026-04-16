# UI Documentation: Design, System, Guides

**Consolidated from:** ui_design.md, development_plan.md, ui_guide.md, UI-REDESIGN.md, DESIGN-SYSTEM.md, UI-DESIGN-ENHANCEMENT.md, UI-BEFORE-AFTER.md, UI-DEVELOPER-GUIDE.md, UI-IMPLEMENTATION-SUMMARY.md, UI-DOCUMENTATION-INDEX.md

---

## Table of Contents

1. [UI Architecture](#ui-architecture)
2. [Design System](#design-system)
3. [Implementation Structure](#implementation-structure)
4. [User Guide](#user-guide)
5. [Developer Guide](#developer-guide)

---

## UI Architecture

### Why Streamlit?

**Advantages:**
- ✅ No frontend/backend separation (pure Python)
- ✅ Rapid prototyping (minimal boilerplate)
- ✅ Built-in session state management
- ✅ No JavaScript/CSS required for functionality
- ✅ Perfect for data-heavy analytics apps

**Disadvantages:**
- App reloads on every button click (fine for demo)
- Limited customization without CSS
- Not suitable for high-concurrency (fine for single-user thesis)

### Overall Architecture

```
┌──────────────────────────────────────┐
│ Streamlit Web Interface (ui/app.py)  │
├──────────────────────────────────────┤
│ 1. Sidebar: Navigation + Search      │
│ 2. Tab 1: Customer 360 view          │
│ 3. Tab 2: Loan Assessment            │
│ 4. Tab 3: Fraud Detection            │
│ 5. Tab 4: Customer Management        │
└─────────────┬──────────────────────────┘
              │ Session State Management
┌─────────────▼──────────────────────────┐
│ ui/parse.py: Output Parsing Functions  │
│ - parse_customer_360()                 │
│ - parse_loan_scoring()                 │
│ - parse_fraud_detect()                 │
│ - parse_customer_search()              │
│ - parse_customer_list()                │
│ - parse_customer_update()              │
│ - parse_customer_transactions()        │
│ - parse_fraud_batch_analysis()         │
└─────────────┬──────────────────────────┘
              │ Subprocess Invocation
┌─────────────▼──────────────────────────┐
│ ui/runner.py: Script Execution         │
│ run_script(script_name, args) → str    │
└─────────────┬──────────────────────────┘
              │
              ▼
    ┌─────────────────────┐
    │ Python Analytics    │
    │ (python/*.py)       │
    │                     │
    │ Query Parquet Data  │
    │ (DuckDB)            │
    └─────────────────────┘
```

---

## Design System

### Color Palette

| Role | Color | Usage |
|------|-------|-------|
| **Primary** | #0066CC (Blue) | Buttons, links, interactive elements |
| **Success** | #28A745 (Green) | Positive status, LOW risk |
| **Warning** | #FFC107 (Yellow) | Caution, MEDIUM risk |
| **Danger** | #DC3545 (Red) | Negative status, HIGH risk |
| **Background** | #F5F5F5 (Light Gray) | Page background |
| **Text** | #333333 (Dark Gray) | Body text |

### Typography

| Element | Font | Size | Weight |
|---------|------|------|--------|
| **Heading 1** | System | 24px | Bold |
| **Heading 2** | System | 20px | Bold |
| **Body** | System | 14px | Regular |
| **Code** | Monospace | 12px | Regular |

### Components

**Metric Cards:**
- Large display of key numbers (balance, score, count)
- Color-coded background based on status
- Icon + value + label layout

**Status Badges:**
- Pill-shaped labels (LOW, MEDIUM, HIGH, Y, N)
- Color matches status role
- Small font, subtle appearance

**Buttons:**
- Primary: Full-width, blue background, white text
- Secondary: Outlined, blue border, blue text
- Disabled: Gray, no interaction

**Input Fields:**
- Text inputs for customer ID, amounts, etc.
- Number inputs for numeric values
- Date/time inputs for transactions
- Selectboxes for categorical fields

---

## Implementation Structure

### Files & Modules

```
ui/
├── __init__.py            (empty, makes ui/ a Python package)
├── runner.py              (70 lines: subprocess execution)
├── parse.py               (540+ lines: output parsing)
└── app.py                 (1000+ lines: Streamlit interface)

cobol/
├── CUSTOMER-LOOKUP.cbl    (142 lines)
├── LOAN-PROCESS.cbl       (146 lines)
├── FRAUD-CHECK.cbl        (156 lines)
├── copybooks/
│   ├── CUSTOMER-REC.cpy   (145 bytes)
│   ├── LOAN-REC.cpy       (51 bytes)
│   └── FRAUD-REC.cpy      (78 bytes)
└── Makefile               (compilation & testing)

python/
├── customer_360.py        (analytics: customer 360°)
├── loan_scoring.py        (analytics: loan eligibility)
├── fraud_detect.py        (analytics: fraud detection)
├── customer_search.py     (search by last name)
├── customer_list.py       (paginated customer list)
├── customer_update.py     (validate & update customer)
├── customer_transactions.py (fetch all transactions)
├── fraud_batch_analysis.py (batch fraud scoring)
└── utils/
    ├── ipc_formatter.py   (PIC X/9 formatting)
    └── parquet_reader.py  (DuckDB query wrapper)

data/
├── generate_synthetic.py  (create test data)
├── customers.parquet      (100K records)
├── loans.parquet          (500K records)
├── transactions/          (10M records, date-partitioned)
└── fraud_labels.parquet   (50K records)
```

### Session State Variables

**Customer-level state:**
```python
st.session_state.selected_customer_id       # Currently selected customer
st.session_state.selected_customer_name     # Display name
st.session_state.search_query               # Last search query
```

**Fraud Detection state:**
```python
st.session_state.fraud_all_transactions     # Cached all txns for customer
st.session_state.fraud_txns_loaded_cid      # Which customer's txns are cached
st.session_state.fraud_search_text          # Filter: search merchant/city
st.session_state.fraud_channel_filter       # Filter: selected channels
st.session_state.fraud_min_amount           # Filter: min amount
st.session_state.fraud_max_amount           # Filter: max amount
```

---

## User Guide

### Getting Started

**Prerequisites:**
- Python 3.11+
- Streamlit: `pip install streamlit`
- Dependencies: `pip install duckdb pyarrow pandas numpy faker`
- COBOL compiler (optional, for running COBOL programs directly)

**Launch the App:**
```bash
# From project root directory
streamlit run ui/app.py

# Opens browser at http://localhost:8501
```

### Page 1: Customer 360 View

**Purpose:** Get comprehensive customer profile (balance, risk score, transaction history)

**Steps:**
1. Enter customer ID (e.g., C-00001) in sidebar search
2. Click the search button (→)
3. Selected customer name appears below search box
4. View details: Account balance, transaction count, average monthly spending, risk score, last transaction date

**What It Does:**
- Queries `customers.parquet` and `transactions.parquet`
- Computes risk score based on transaction patterns
- Displays results in formatted cards with color-coding

### Page 2: Loan Assessment

**Purpose:** Determine loan eligibility and interest rate

**Steps:**
1. Select a customer (using sidebar search)
2. Enter loan details:
   - Requested amount (dollars)
   - Term (months: 12, 24, 36, 48, 60, etc.)
   - Purpose (HOME, AUTO, PERS, EDUC)
3. Click "Assess Loan →"
4. View results: Credit score, eligibility (Y/N), interest rate or rejection reason

**What It Does:**
- Analyzes payment history (on-time ratio, defaults)
- Computes debt-to-income ratio
- Calculates credit score (300–850 scale)
- Determines eligibility: score ≥ 650 AND DTI < 0.43 AND no recent defaults
- Assigns interest rate based on risk tier

### Page 3: Fraud Detection

**Purpose:** Assess transaction risk and analyze all customer transactions

**Steps:**
1. Select a customer
2. All transactions load automatically (may take a few seconds)
3. Use filters to explore:
   - **Search:** Type merchant name or city (live filtering)
   - **Channel:** Select ATM, ONL (Online), POS, MOB (Mobile)
   - **Amount Range:** Set min/max limits
4. Click "Analyse All Transactions →"
5. View batch results:
   - Summary cards (Total, High Risk, Medium Risk, Low Risk)
   - Risk distribution chart
   - Full transaction table with fraud scores
   - Flagged HIGH-risk transactions section

**What It Does:**
- Loads all transactions for the customer
- Applies client-side filters (search, channel, amount)
- Scores all transactions simultaneously
- Classifies risk: LOW (0–40), MEDIUM (41–75), HIGH (76–100)
- Provides recommendation: APPROVE, REVIEW, DECLINE

### Page 4: Customer Management

**Purpose:** Search, view, and update customer records

**Steps:**
1. **Search:** Enter last name prefix (e.g., "Smith")
2. **View:** Browse search results with customer ID, full name, city, email
3. **Select:** Click a customer to view full details
4. **Update:** Edit name, email, city, or street
5. **Submit:** System validates changes and confirms update

**What It Does:**
- Queries `customers.parquet` for matching names
- Displays paginated results
- Validates update fields against constraints
- Calls COBOL validation program if needed
- Shows success/error messages

### Error Handling

**What If I Get an Error?**

| Error Message | Cause | Fix |
|---|---|---|
| "Customer not found" | Invalid customer ID | Check the ID format (C-XXXXX) |
| "Python script failed" | Backend script crashed | Check data directory exists |
| "Record format error" | Byte-length mismatch | Verify Python scripts are current |
| "Timeout waiting for response" | Script took >5 seconds | Try again; might be system load |

---

## Developer Guide

### Adding a New Page

**Step 1:** Create a new function in `app.py`:
```python
def page_new_feature():
    st.header("🆕 New Feature")
    
    # Page content here
    customer_id = st.text_input("Customer ID")
    if st.button("Analyze"):
        try:
            result = run_script("python/new_script.py", [customer_id])
            data = parse_new_script(result)
            st.success(f"Success: {data}")
        except (RunnerError, ParseError) as e:
            st.error(str(e))
```

**Step 2:** Add to sidebar navigation:
```python
with st.sidebar:
    page = st.radio("Choose page", [
        "Customer 360",
        "Loan Assessment",
        "Fraud Detection",
        "Customer Management",
        "🆕 New Feature"  # Add here
    ])

if page == "🆕 New Feature":
    page_new_feature()
```

**Step 3:** Create backend script `python/new_script.py` and parser function in `ui/parse.py`.

### Adding a New Parser

**Step 1:** Create parser function in `ui/parse.py`:
```python
def parse_new_script(raw: str) -> Dict[str, Any]:
    """
    Parse output from new_script.py
    
    Expected format: <field1>|<field2>|...
    """
    try:
        parts = raw.strip().split('|')
        if len(parts) != 3:
            raise ParseError(f"Expected 3 fields, got {len(parts)}")
        
        return {
            'field1': parts[0].strip(),
            'field2': int(parts[1]),
            'field3': parts[2].strip(),
        }
    except ParseError:
        raise
    except Exception as e:
        raise ParseError(f"Failed to parse: {e}")
```

**Step 2:** Use in page:
```python
result = run_script("python/new_script.py", [arg1, arg2])
data = parse_new_script(result)
st.write(data)
```

### Debugging

**Enable Debug Output:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now see detailed logs in terminal
```

**Test Parser Function Directly:**
```python
from ui.parse import parse_customer_360

test_output = "Smith         " + "0" * 100 + "00"  # Mock 145-byte record
try:
    result = parse_customer_360(test_output)
    print(f"Success: {result}")
except ParseError as e:
    print(f"Error: {e}")
```

**Test Backend Script Directly:**
```bash
python3 python/customer_360.py C-00001
# Should output exactly 145 bytes + newline
```

### Performance Tips

| Optimization | Benefit |
|---|---|
| Cache transaction data in session state | Avoid re-fetching same customer |
| Use client-side filtering (pandas) | No round-trip to backend |
| Pre-compute fraud scores in batch | Faster than per-transaction |
| Load data only when page opens | Lazy loading reduces startup time |

---

## Accessibility & Design Decisions

### Accessibility
- ✅ High color contrast (WCAG AA compliant)
- ✅ Large touch targets for buttons (48px minimum)
- ✅ Clear, descriptive labels for all inputs
- ✅ Error messages are specific and actionable
- ✅ No audio or video required

### Design Decisions
- **Color Coding:** Risk levels (GREEN=LOW, YELLOW=MEDIUM, RED=HIGH) are immediately recognizable
- **Cards Over Tables:** Metric cards are scannable for quick decisions
- **Real-Time Filters:** Search/filter updates instantly without button clicks
- **Batch Analysis:** Single button click analyzes all transactions rather than per-transaction form
- **Sidebar Navigation:** Persistent, always-accessible page switcher

---

## Quick Reference

### Module Imports
```python
import streamlit as st
from ui.runner import run_script
from ui.parse import parse_customer_360, parse_loan_scoring, ...
from datetime import datetime
import pandas as pd
```

### Common Patterns
```python
# Run a backend script
result = run_script("python/customer_360.py", [customer_id])

# Parse the result
data = parse_customer_360(result)

# Handle errors
try:
    result = run_script(...)
    data = parse_customer_360(result)
except RunnerError as e:
    st.error(f"Backend error: {e}")
except ParseError as e:
    st.error(f"Parse error: {e}")

# Display formatted results
st.metric("Account Balance", f"${data['balance']:,.2f}")
st.write(f"Risk Score: {data['risk_score']} / 999")
```

---

## References

- **architecture.md** — System design & data layer
- **implementation.md** — Backend implementation details
- **progress.md** — Project status & metrics
- **CLAUDE.md** — Claude Code session guidance

