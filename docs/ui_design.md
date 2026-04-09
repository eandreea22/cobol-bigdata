# UI Design Document

**Date:** 2026-04-08  
**Technology:** Streamlit (pure Python web framework)  
**Status:** COMPLETE

---

## 1. Technology Choice: Streamlit

### Why Streamlit?

| Criterion | Choice | Rationale |
|-----------|--------|-----------|
| Language | Python | Integrates seamlessly with existing analytics scripts; no JavaScript/CSS needed |
| Framework | Streamlit | Minimal setup, pure Python, built-in widgets for forms & metrics |
| Deployment | Local browser | Single command: `streamlit run ui/app.py` → auto-opens browser |
| Dependencies | Minimal | Just `pip install streamlit` — no Node.js, npm, or build tools |
| State Management | Automatic | Streamlit handles form state and reruns automatically |

### Advantages

✅ **Zero frontend complexity** — Metrics, forms, buttons, progress bars all built-in  
✅ **Subprocess-friendly** — Designed for Python workflows; perfect for calling our scripts  
✅ **Fast iteration** — File changes auto-reload (no manual restart)  
✅ **Production-ready** — Used by data science teams at scale  
✅ **Windows-compatible** — Works on Windows 11 with Python  

---

## 2. Architecture

### Data Flow Diagram

```
User Input (Web Form)
         ↓
Streamlit Widget State (st.text_input, st.selectbox, etc.)
         ↓
User Clicks Button (st.button)
         ↓
Python Handler Function (tab_*_*())
         ↓
runner.run_script(script_path, args)
         ↓
subprocess.run(["python", "python/script.py", args...])
         ↓
Python Script Executes (customer_360.py, loan_scoring.py, fraud_detect.py)
         ↓
Fixed-Width Output (145, 51, or 78 bytes)
         ↓
runner returns stdout.strip()
         ↓
parse_customer_360() / parse_loan_scoring() / parse_fraud_detect()
         ↓
Returns Parsed Dict (name, balance, risk_score, etc.)
         ↓
Streamlit Display (st.metric, st.write, st.markdown)
         ↓
Browser Renders Results
```

### Module Structure

| Module | Lines | Purpose |
|--------|-------|---------|
| `ui/app.py` | ~280 | Main Streamlit app with three tabs and widget definitions |
| `ui/runner.py` | ~70 | Subprocess wrapper; executes scripts and captures output |
| `ui/parse.py` | ~160 | Fixed-width record parsers; converts binary to Python dicts |

**Integration Points:**
- `app.py` imports `runner.py` and `parse.py`
- `runner.py` calls `subprocess.run()` with project root as cwd
- `parse.py` validates byte lengths and return codes; raises `ParseError` on invalid data

---

## 3. Tab-Based Interface

### Tab 1: Customer 360 View

**Purpose:** Display comprehensive customer profile — balance, transaction count, risk score, etc.

**Inputs:**
| Widget | Type | Default | Constraints |
|--------|------|---------|-------------|
| Customer ID | text_input | "C-00001" | Format: C-00001 through C-100000 |

**Actions:**
- Button: "Lookup" — Calls `customer_360.py`

**Output Display:**
| Component | Source | Format |
|-----------|--------|--------|
| Account Balance | `balance` | USD currency: `$X,XXX.XX` |
| Transaction Count | `txn_count` | Plain integer |
| Avg Monthly Spend | `avg_monthly` | USD currency |
| Risk Score | `risk_score` | Integer 0-999 with color badge (0-299=🟢 LOW, 300-599=🟡 MEDIUM, 600-999=🔴 HIGH) |
| Last Transaction | `last_txn_date` | Date string: YYYY-MM-DD |
| Customer Name | `name` | Plain text (stripped) |

**Error Handling:**
- Return code "01" (not found) → ParseError: "Customer not found"
- Return code "99" (system error) → ParseError: "Customer script error"
- Wrong byte length → ParseError: "Expected 145 bytes, got N"

---

### Tab 2: Loan Assessment

**Purpose:** Evaluate loan request; return eligibility and terms.

**Inputs:**
| Widget | Type | Default | Range | Options |
|--------|------|---------|-------|---------|
| Customer ID | text_input | "C-00001" | — | C-00001 to C-100000 |
| Loan Amount | number_input | 10000 | 1000–500000 | Step: 1000 |
| Term | selectbox | 36 | — | 12, 24, 36, 48, 60, 84, 120 months |
| Purpose | selectbox | PERS | — | HOME, AUTO, PERS, EDUC |

**Actions:**
- Button: "Assess Loan" — Calls `loan_scoring.py <id> <amount> <term> <purpose>`

**Output Display:**
| Component | Source | Format | Condition |
|-----------|--------|--------|-----------|
| Credit Score | `credit_score` | Metric card: X/850 | Always |
| Eligibility | `eligible` | Large badge: ✅ APPROVED or ❌ DECLINED | Always |
| Interest Rate | `int_rate` | Metric card: X.XX% | Only if eligible |
| Max Amount | `max_amount` | Metric card: $X,XXX.XX | Only if eligible |
| Rejection Reason | `reason` | Warning box text | Only if not eligible |

**Color Coding:**
- Approved → Green badge with checkmark
- Declined → Red badge with X
- Credit score displayed with metric card (standard Streamlit styling)

---

### Tab 3: Fraud Detection

**Purpose:** Assess transaction risk and recommend action.

**Inputs:**
| Widget | Type | Default | Constraints |
|--------|------|---------|-------------|
| Customer ID | text_input | "C-00001" | C-00001 to C-100000 |
| Amount | number_input | 500.00 | Min 0.01, step 0.01 |
| MCC | text_input | "5411" | Must be 4 digits (0-9) |
| Location | text_input | "Bucharest" | Free text; affects geo anomaly detection |
| Date | date_input | Today | — |
| Time | time_input | Current | — |
| Channel | selectbox | POS | POS, ATM, ONL, MOB |

**Actions:**
- Button: "Analyze Transaction" — Calls `fraud_detect.py <id> <amt> <mcc> <loc> <timestamp> <channel>`
- Timestamp combined from date + time → ISO 8601 format

**Output Display:**
| Component | Source | Format | Styling |
|-----------|--------|--------|---------|
| Risk Level | `risk_level` | Large header: LOW, MEDIUM, or HIGH | 🟢 GREEN, 🟡 ORANGE, 🔴 RED |
| Fraud Score | `fraud_score` | Metric + progress bar: X/100 | Bar fills 0–100 |
| Recommendation | `recommendation` | Inline text: APPROVE ✅, REVIEW ⚠️, or DECLINE ❌ | Colored by action |
| Detected Flags | `flags` | Pill tags, one per flag | Gray background, comma-separated from output |

**Validation:**
- MCC must be 4 digits → Error if not

---

## 4. Component Design Details

### Metrics & Badges

**Streamlit `st.metric()`** — Used for numerical displays:
```python
st.metric("Account Balance", "$12,345.67")
```
Displays label above, value in large font. Good for key figures.

**Colored Badges** — Using `st.markdown()` with emojis:
```python
if result['eligible']:
    st.markdown("#### ✅ **APPROVED**")
else:
    st.markdown("#### ❌ **DECLINED**")
```

**Progress Bars** — For fraud score 0–100:
```python
st.progress(fraud_score / 100.0)
```

**Alert Boxes** — Using `st.success()`, `st.warning()`, `st.error()`:
```python
st.success("Customer found!")
st.warning(f"Reason: {reason}")
st.error("Fraud score high!")
```

### Form Layout

**Two-column layout for cramped forms:**
```python
col1, col2 = st.columns(2)
with col1:
    st.text_input(...)
with col2:
    st.number_input(...)
```

**Three-column for metrics display:**
```python
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Balance", "$X")
with col2:
    st.metric("Count", "N")
with col3:
    st.metric("Risk", "X/999")
```

---

## 5. Error Handling & User Feedback

### Execution Errors

**RunnerError** → Subprocess failed (script not found, timeout, non-zero exit):
```
❌ Execution error: Script /python/customer_360.py exited with code 1
stderr: [actual error]
```
Displayed via `st.error()`.

### Parse Errors

**ParseError** → Output validation failed (wrong byte length, invalid return code):
```
❌ Parse error: Customer not found — check customer ID
```
Displayed via `st.error()`.

### Loading Feedback

`st.spinner("Looking up customer...")` wraps the entire subprocess + parse block.

---

## 6. Design Constraints & Trade-offs

### Assumptions

1. **Project root as cwd:** UI runs from project root; paths like `python/customer_360.py` resolve correctly
2. **Python availability:** `sys.executable` finds Python; script calls use absolute path via `project_root / script_path`
3. **Customer ID format:** User enters C-00001 through C-100000; no validation against actual data (wrong ID → error from script)
4. **No state across tabs:** Each tab is independent; no multi-step workflows
5. **Real-time queries:** No caching; every lookup hits Parquet files (acceptable for demo/thesis)

### Future Enhancements (Not Implemented)

- ⏭️ Batch uploads (CSV of customer IDs)
- ⏭️ Transaction history timeline (need new backend script)
- ⏭️ Loan calculator with amortization schedule
- ⏭️ Fraud rule explanation (why was it flagged?)
- ⏭️ Export results as PDF or CSV
- ⏭️ User authentication & audit logs

---

## 7. File Structure

```
ui/
  __init__.py          (empty, makes ui/ a package)
  app.py               (main Streamlit app)
  runner.py            (subprocess execution)
  parse.py             (fixed-width record parsing)
```

Run command:
```bash
streamlit run ui/app.py
```

Browser opens automatically to `http://localhost:8501`

---

## 8. Validation & Edge Cases

| Scenario | Handling |
|----------|----------|
| Customer ID blank | `st.error("Please enter a customer ID")` |
| Customer not found (return code 01) | ParseError raised, caught and displayed |
| System error (return code 99) | ParseError raised, caught and displayed |
| Subprocess timeout (>30s) | RunnerError: "Script timed out (>30s)" |
| MCC not 4 digits | `st.error("MCC must be a 4-digit number")` |
| Loan amount < 1000 | number_input enforces min_value=1000 |
| Negative fraud score | Clamped by progress bar (min 0) |
| Invalid timestamp | Python datetime validation (handled by date/time inputs) |

---

## Summary

The UI is a **pure Python Streamlit app** with three independent tabs, each calling a backend analytics script, parsing the fixed-width response, and displaying results with color-coded metrics and alerts. No modifications to core system logic; UI only orchestrates subprocess calls and presentation.

**Status:** ✅ Design complete, ready for implementation.

