# UI Development Plan

**Date:** 2026-04-08  
**Phase:** UI Layer (Phase 8 of 8)  
**Status:** COMPLETE  

---

## 1. Project Scope

### Objective

Add a **Streamlit-based web UI** to the hybrid COBOL-Python banking system. The UI provides an interactive interface for three core analytics functions without modifying any existing system logic.

### Constraints

- ✅ Do NOT modify `python/customer_360.py`, `python/loan_scoring.py`, `python/fraud_detect.py`
- ✅ Do NOT modify `cobol/` programs
- ✅ Do NOT modify `data/` generation or structure
- ✅ UI is read-only; all writes are by the backend scripts
- ✅ UI must work on Windows 11 (no Linux-specific features)
- ✅ Subprocess calls must use absolute paths (via `sys.executable` and `project_root`)

### Success Criteria

- [ ] Three tabs render correctly with proper input fields
- [ ] Each tab calls the appropriate Python script via subprocess
- [ ] Output parsing works for all three record types (145, 51, 78 bytes)
- [ ] Error handling catches RunnerError and ParseError
- [ ] Color-coded metrics display properly
- [ ] UI runs: `streamlit run ui/app.py` → browser opens automatically

---

## 2. Directory Structure

### Before (Phases 1–7)

```
cobol-bigdata/
├── python/
│   ├── customer_360.py          (analytics)
│   ├── loan_scoring.py
│   ├── fraud_detect.py
│   └── utils/
│       ├── ipc_formatter.py
│       └── parquet_reader.py
├── cobol/
│   ├── CUSTOMER-LOOKUP.cbl
│   ├── LOAN-PROCESS.cbl
│   ├── FRAUD-CHECK.cbl
│   └── Makefile
├── data/
│   ├── customers.parquet
│   ├── loans.parquet
│   ├── fraud_labels.parquet
│   └── transactions/
└── docs/
    ├── CLAUDE.md
    ├── INDEX.md
    └── ... (8 more documentation files)
```

### After (Phase 8: UI Layer)

```
cobol-bigdata/
├── ui/                          ← NEW DIRECTORY
│   ├── __init__.py              (empty)
│   ├── app.py                   (main Streamlit app)
│   ├── runner.py                (subprocess execution)
│   └── parse.py                 (fixed-width parsing)
├── python/
│   ├── ...                      (unchanged)
│   └── utils/
├── cobol/
│   ├── ...                      (unchanged)
└── docs/
    ├── ui_design.md             ← NEW
    ├── development_plan.md      ← NEW (this file)
    ├── progress_tracker.md      ← NEW
    ├── ui_guide.md              ← NEW
    └── ... (existing)
```

---

## 3. Component Breakdown

### Module 1: `ui/parse.py` (COMPLETE)

**Purpose:** Parse fixed-width COBOL records into Python dicts.

**Functions:**
- `parse_customer_360(raw: str) -> Dict`
  - Validates 145 bytes
  - Extracts: name, balance (÷100), txn_count, avg_monthly (÷100), risk_score, last_txn_date, return_code
  - Raises ParseError on invalid return_code or byte length

- `parse_loan_scoring(raw: str) -> Dict`
  - Validates 51 bytes
  - Extracts: credit_score, eligible (bool), int_rate (÷10000), max_amount (÷100), reason, return_code
  - Raises ParseError on return_code != "00" (except "99" with reason)

- `parse_fraud_detect(raw: str) -> Dict`
  - Validates 78 bytes
  - Extracts: risk_level, fraud_score, flags (comma-split list), recommendation, return_code
  - Raises ParseError on invalid return_code or out-of-range score

**Dependencies:** None (pure Python)

**Testing:** Manual tests with known outputs (51, 78, 145 byte records)

---

### Module 2: `ui/runner.py` (COMPLETE)

**Purpose:** Execute Python analytics scripts via subprocess; return stdout.

**Functions:**
- `run_script(script_path: str, args: list) -> str`
  - Builds command: `[sys.executable, project_root / script_path, *args]`
  - Runs with `cwd=project_root` (so relative paths resolve)
  - Sets 30-second timeout
  - Captures stdout, returns stripped (removes CRLF)
  - Raises RunnerError on non-zero exit, timeout, or missing file

**Dependencies:** subprocess, sys, pathlib

**Error Handling:**
- RunnerError class for all execution failures
- Descriptive messages with stderr output

**Windows Compatibility:**
- Uses `sys.executable` instead of hardcoded `python`
- Converts all paths to absolute (via `Path.resolve()`)
- Handles Windows path separators automatically

---

### Module 3: `ui/app.py` (COMPLETE)

**Purpose:** Main Streamlit app with three tabs.

**Structure:**
```python
def tab_customer_360()      # Tab 1: Lookup
def tab_loan_assessment()   # Tab 2: Assess
def tab_fraud_detection()   # Tab 3: Analyze
def main()                  # Entry point: three tabs
```

**Streamlit Widgets Used:**
- `st.set_page_config()` — Page title, icon, layout
- `st.title()`, `st.header()` — Headings
- `st.tabs()` — Three tabs
- `st.text_input()` — Customer ID, location, MCC
- `st.number_input()` — Amount, term, loan amount
- `st.selectbox()` — Purpose, channel, term
- `st.date_input()`, `st.time_input()` — Timestamp
- `st.button()` — Lookup/Assess/Analyze
- `st.spinner()` — Loading indicator
- `st.metric()` — Key-value display
- `st.columns()` — Layout grid
- `st.markdown()` — Rich text (badges, emoji)
- `st.progress()` — Progress bar
- `st.success()`, `st.error()`, `st.warning()` — Alert boxes

**Error Handling:**
- Try-except for RunnerError (execution failure)
- Try-except for ParseError (invalid output)
- Input validation (blank fields, MCC format)

---

## 4. Implementation Steps (Execution Order)

### Step 1: Create UI Directory

```bash
mkdir -p ui
touch ui/__init__.py
```

**Dependencies:** None  
**Time:** < 1 min  
**Success Criteria:** Directory exists, `__init__.py` is empty

### Step 2: Create `ui/parse.py`

**Code:**
- ParseError exception class
- parse_customer_360() function (145 bytes)
- parse_loan_scoring() function (51 bytes)
- parse_fraud_detect() function (78 bytes)

**Testing:**
```python
# Test with known output
raw = "John              " + "0" * 127  # 145 bytes
result = parse_customer_360(raw)
assert result["name"] == "John"
```

**Dependencies:** typing  
**Time:** ~30 min (30 min code, ~10 min testing with manual byte strings)  
**Success Criteria:** All three parsers work; ParseError raised on invalid input

---

### Step 3: Create `ui/runner.py`

**Code:**
- RunnerError exception class
- run_script(script_path, args) function

**Testing:**
```bash
python -c "from ui.runner import run_script; \
    out = run_script('python/loan_scoring.py', ['C-00001', '10000', '36', 'PERS']); \
    print(f'Output length: {len(out)}')"
# Expected: Output length: 51
```

**Dependencies:** subprocess, sys, pathlib  
**Time:** ~20 min (15 min code, 5 min testing with real script)  
**Success Criteria:** Subprocess execution works; stdout captured and returned

---

### Step 4: Create `ui/app.py`

**Code:**
- Imports: streamlit, runner, parse, datetime
- Helper functions: format_currency, format_percentage, risk_color, score_color
- tab_customer_360(), tab_loan_assessment(), tab_fraud_detection()
- main() with st.tabs()

**Testing:**
```bash
pip install streamlit
streamlit run ui/app.py
# Test: Enter C-00001, click buttons, verify output
```

**Dependencies:** streamlit, ui.runner, ui.parse  
**Time:** ~60 min (45 min code, 15 min testing & UI polish)  
**Success Criteria:** All three tabs load; buttons trigger scripts; results display correctly

---

### Step 5: Create `docs/ui_design.md`

**Content:**
- Technology choice rationale
- Data flow diagram
- Tab specifications (inputs, outputs, color coding)
- Component design (metrics, badges, alerts)
- Error handling & edge cases
- Validation table

**Dependencies:** None  
**Time:** ~30 min  
**Success Criteria:** Document is complete and covers all three tabs

---

### Step 6: Create `docs/development_plan.md`

**Content:**
- Scope & constraints
- Directory structure (before/after)
- Component breakdown (3 modules)
- 8-step implementation sequence
- Integration points with existing system
- Verification checklist

**Dependencies:** None  
**Time:** ~20 min  
**Success Criteria:** This document is complete

---

### Step 7: Create `docs/progress_tracker.md`

**Content:**
- Task checklist (all 8 steps)
- Blockers section (none expected)
- Notes on each module
- Status updates (TODO → IN_PROGRESS → DONE)

**Dependencies:** None  
**Time:** ~10 min  
**Success Criteria:** All tasks listed with status

---

### Step 8: Create `docs/ui_guide.md`

**Content:**
- Prerequisites (pip install streamlit)
- How to run (streamlit run ui/app.py)
- Field-by-field usage instructions
- Expected outputs and meanings
- Troubleshooting section (common errors)

**Dependencies:** None  
**Time:** ~20 min  
**Success Criteria:** User can run UI from guide alone

---

### Step 9: Update `docs/INDEX.md`

**Changes:**
- Add "Phase 8: UI Layer" section
- Link to ui_design.md, development_plan.md, progress_tracker.md, ui_guide.md
- Update overall status to "ALL 8 PHASES COMPLETE"

**Dependencies:** docs/INDEX.md exists  
**Time:** ~10 min  
**Success Criteria:** INDEX.md references all UI docs

---

## 5. Integration Points with Existing System

### 1. Data Access

**What UI reads:**
- `data/customers.parquet` — via customer_360.py
- `data/loans.parquet` — via loan_scoring.py
- `data/transactions/*.parquet` — via customer_360.py
- `data/fraud_labels.parquet` — via fraud_detect.py

**What UI does NOT modify:** Nothing

---

### 2. Script Execution

**Scripts called by UI (unchanged):**
- `python/customer_360.py <customer_id>`
- `python/loan_scoring.py <customer_id> <amount> <term> <purpose>`
- `python/fraud_detect.py <customer_id> <amount> <mcc> <location> <timestamp> <channel>`

**IPC Contract (read-only reference):**
- Output format is fixed-width (145, 51, 78 bytes respectively)
- Return codes embedded: "00"=success, "01"=not found, "99"=error
- Numeric fields use PIC 9(n)V9(m) format (divide by 10^m)

---

### 3. Error Handling Chain

```
User Input (UI)
    ↓
runner.run_script()
    ├─ subprocess.run() fails
    └─→ RunnerError (caught by app.py)
         └→ st.error() displayed to user
    
    ├─ subprocess.run() succeeds
    └→ stdout returned
         ↓
         parse_customer_360() / parse_loan_scoring() / parse_fraud_detect()
         ├─ Byte length validation fails
         │  └→ ParseError (caught by app.py)
         │     └→ st.error() displayed
         ├─ Return code "01" or "99"
         │  └→ ParseError (caught by app.py)
         │     └→ st.error() displayed
         └─ Parse succeeds
            └→ Dict returned
               └→ app.py displays via st.metric(), st.write()
```

---

## 6. Verification Checklist

### Code Quality

- [ ] All Python files follow PEP 8 (4-space indent, snake_case)
- [ ] No imports from core system (customer_360.py, etc.)
- [ ] runner.py uses sys.executable for Windows compatibility
- [ ] parse.py validates byte lengths and return codes
- [ ] app.py has comprehensive try-except blocks

### Functionality

- [ ] Tab 1 (Customer 360): Input → Lookup → Display name, balance, risk, date
- [ ] Tab 2 (Loan Assessment): Input → Assess → Display score, eligibility, rate/reason
- [ ] Tab 3 (Fraud Detection): Input → Analyze → Display risk, score, flags, recommendation
- [ ] All tabs handle errors gracefully with st.error()
- [ ] All numeric outputs formatted correctly ($, %)

### Testing

- [ ] Tested with C-00001 (exists in data)
- [ ] Tested with C-99999 (doesn't exist → return code "01")
- [ ] Tested edge cases: amount=0, term=12, etc.
- [ ] Tested error conditions: wrong byte length, timeout, missing script

### Documentation

- [ ] ui_design.md covers all three tabs and components
- [ ] development_plan.md lists all 8 implementation steps
- [ ] progress_tracker.md tracks status of all tasks
- [ ] ui_guide.md provides step-by-step usage instructions
- [ ] INDEX.md updated with links to all UI docs

### Deployment

- [ ] `pip install streamlit` succeeds
- [ ] `streamlit run ui/app.py` launches without errors
- [ ] Browser opens automatically to http://localhost:8501
- [ ] UI runs on Windows 11 without path issues

---

## 7. Known Limitations & Future Work

### Current Limitations

1. **No caching** — Every lookup hits Parquet files (acceptable for demo)
2. **No batch operations** — Single transaction at a time
3. **No audit logging** — No record of who looked up what
4. **No customer validation** — Wrong ID → error from backend (not caught by UI)
5. **Single timezone** — Timestamp input doesn't specify timezone

### Future Enhancements (Post-Thesis)

- [ ] CSV upload for batch fraud scanning
- [ ] Transaction history timeline (needs new script)
- [ ] Loan amortization calculator
- [ ] Rule explanation engine ("why was it flagged?")
- [ ] Export results as PDF/Excel
- [ ] User authentication & audit logs
- [ ] Dark mode toggle
- [ ] Mobile-responsive design

---

## 8. Timeline

| Phase | Component | Time | Status |
|-------|-----------|------|--------|
| 1 | Create ui/ directory | < 1 min | ✅ |
| 2 | ui/parse.py | 30 min | ✅ |
| 3 | ui/runner.py | 20 min | ✅ |
| 4 | ui/app.py | 60 min | ✅ |
| 5 | docs/ui_design.md | 30 min | ✅ |
| 6 | docs/development_plan.md | 20 min | ✅ |
| 7 | docs/progress_tracker.md | 10 min | ⏳ |
| 8 | docs/ui_guide.md | 20 min | ⏳ |
| 9 | Update docs/INDEX.md | 10 min | ⏳ |
| **TOTAL** | | **~3 hours** | **50% DONE** |

---

## 9. Success Criteria (Final)

By end of Phase 8:

✅ **All code complete:**
- [ ] ui/parse.py (160 lines)
- [ ] ui/runner.py (70 lines)
- [ ] ui/app.py (280 lines)

✅ **All docs complete:**
- [ ] ui_design.md
- [ ] development_plan.md
- [ ] progress_tracker.md
- [ ] ui_guide.md
- [ ] INDEX.md updated

✅ **System working:**
- [ ] Run: `streamlit run ui/app.py`
- [ ] All three tabs functional
- [ ] All three scripts callable
- [ ] All three parsers working
- [ ] Error messages clear and helpful

---

## Summary

The UI layer is a **three-module Streamlit app** with **four supporting documentation files**. All components are self-contained; no modifications to core system logic. Implementation follows a linear 9-step sequence; each step is independent and testable.

**Status:** ✅ Plan complete, ready to execute.

