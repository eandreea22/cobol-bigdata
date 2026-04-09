# UI User Guide

**Version:** 1.0  
**Date:** 2026-04-08  
**Status:** Ready to Use

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Running the UI](#running-the-ui)
4. [Using the Three Tabs](#using-the-three-tabs)
5. [Understanding Outputs](#understanding-outputs)
6. [Troubleshooting](#troubleshooting)
7. [FAQ](#faq)

---

## Prerequisites

### System Requirements

- **Python:** 3.11 or later
- **OS:** Windows, macOS, or Linux
- **Disk Space:** ~500 MB (for Streamlit + dependencies)
- **Network:** Localhost only (no internet required)

### Verify Python Installation

Open a terminal/command prompt and run:

```bash
python --version
```

If this fails, install Python from [python.org](https://python.org).

### Verify Data Files

Before running the UI, ensure synthetic data has been generated:

```bash
# On Windows (PowerShell)
Get-ChildItem data/*.parquet

# On Linux/macOS
ls data/*.parquet
```

You should see:
- `customers.parquet`
- `loans.parquet`
- `fraud_labels.parquet`

If these don't exist, generate them first:

```bash
python data/generate_synthetic.py
```

---

## Installation

### Step 1: Install Streamlit

```bash
pip install streamlit
```

Verify installation:

```bash
streamlit --version
```

Expected output: `Streamlit, version X.Y.Z`

### Step 2: Navigate to Project Root

```bash
cd C:\Users\[YourUsername]\Desktop\cobol-bigdata
```

(On macOS/Linux: `cd ~/Desktop/cobol-bigdata`)

### Step 3: Verify UI Files Exist

```bash
# On Windows (PowerShell)
Test-Path ui/app.py
Test-Path ui/runner.py
Test-Path ui/parse.py

# On Linux/macOS
ls ui/*.py
```

You should see all three files.

---

## Running the UI

### Start the Application

```bash
streamlit run ui/app.py
```

Expected output:
```
  You can now view your Streamlit app in your browser.

  URL: http://localhost:8501

  Press CTRL+C to quit
```

A browser window will open automatically at `http://localhost:8501`.

### Stop the Application

Press **Ctrl+C** in the terminal where you ran the command.

---

## Using the Three Tabs

### Tab 1: Customer 360 View

**Purpose:** View a customer's complete profile, balance, and transaction history.

#### Input Fields

| Field | Type | Example | Notes |
|-------|------|---------|-------|
| Customer ID | Text | `C-00001` | Format: `C-XXXXX` where XXXXX is 5 digits (00001–100000) |

#### What to Expect

Once you click "Lookup":

1. **Loading indicator** appears (usually 1–2 seconds)
2. **Green success message** appears: "Customer found!"
3. **Key metrics** displayed in boxes:
   - Account Balance (in USD, e.g., `$45,123.67`)
   - Transaction Count (number of transactions)
   - Avg Monthly Spend (average monthly spending, in USD)
4. **Risk Score** (0–999):
   - 🟢 LOW RISK (0–299)
   - 🟡 MEDIUM RISK (300–599)
   - 🔴 HIGH RISK (600–999)
5. **Last Transaction Date** (YYYY-MM-DD format)
6. **Customer Name** (first and last name)

#### Example Run

```
Customer ID: C-00001
[Click "Lookup"]

✅ Customer found!

Account Balance
$45,231.92

Transactions
1,247

Avg Monthly Spend
$3,456.78

Risk Score: 324/999 — 🟡 MEDIUM RISK

Last Transaction: 2025-01-15

Name: John Smith
```

#### Error Cases

**Customer not found:**
```
❌ Parse error: Customer not found — check customer ID
```
→ Try a different customer ID (C-00050, C-00100, etc.)

**Script execution failed:**
```
❌ Execution error: Script python/customer_360.py exited with code 1
stderr: [error details]
```
→ Check that `python/customer_360.py` exists and data files are present

---

### Tab 2: Loan Assessment

**Purpose:** Check if a customer is eligible for a loan and see the terms (interest rate, max amount).

#### Input Fields

| Field | Type | Example | Notes |
|-------|------|---------|-------|
| Customer ID | Text | `C-00001` | Same format as Tab 1 |
| Loan Amount ($) | Number | `25000` | Min: $1,000; Max: $500,000; Step: $1,000 |
| Term (Months) | Dropdown | `36` | Options: 12, 24, 36, 48, 60, 84, 120 months |
| Loan Purpose | Dropdown | `PERS` | Options: HOME, AUTO, PERS, EDUC |

#### What to Expect

Once you click "Assess Loan":

1. **Loading indicator** appears
2. **Credit Score** displayed in a metric box (300–850 scale)
3. **Eligibility badge:**
   - ✅ **APPROVED** (green)
   - ❌ **DECLINED** (red)

**If APPROVED, you'll also see:**
- Interest Rate (e.g., `4.50%`)
- Max Approved Amount (e.g., `$25,000.00`)

**If DECLINED, you'll see:**
- Rejection Reason (e.g., `"LOW_CREDIT_SCORE"`)

#### Example Run (Approved)

```
Customer ID: C-00001
Loan Amount: $25,000
Term: 36 months
Purpose: AUTO

[Click "Assess Loan"]

Credit Score
539 / 850

#### ✅ **APPROVED**

Interest Rate
4.50%

Max Amount
$25,000.00
```

#### Example Run (Declined)

```
Customer ID: C-00050
Loan Amount: $50,000
Term: 60 months
Purpose: HOME

[Click "Assess Loan"]

Credit Score
480 / 850

#### ❌ **DECLINED**

⚠️ Reason: LOW_CREDIT_SCORE
```

#### Loan Purpose Codes

| Code | Meaning |
|------|---------|
| HOME | Home purchase or refinance |
| AUTO | Car or vehicle purchase |
| PERS | Personal loan (debt consolidation, etc.) |
| EDUC | Education (student loan alternative) |

#### Error Cases

**Invalid loan amount:**
```
number_input enforces min/max → UI prevents entry outside 1000–500000
```

**System error from backend:**
```
❌ Execution error: Script python/loan_scoring.py exited with code 1
```

---

### Tab 3: Fraud Detection

**Purpose:** Analyze a transaction and get a risk assessment with recommended action (approve, review, or decline).

#### Input Fields

| Field | Type | Example | Notes |
|-------|------|---------|-------|
| Customer ID | Text | `C-00001` | Same format |
| Amount ($) | Number | `500.00` | Min: $0.01; Step: $0.01 |
| MCC (Merchant Category Code) | Text | `5411` | Must be exactly 4 digits |
| Location | Text | `Bucharest` | City or location name |
| Date | Date | `2026-04-08` | Date picker; default: today |
| Time | Time | `14:30` | Time picker; default: current time |
| Channel | Dropdown | `POS` | Options: POS, ATM, ONL, MOB |

#### What to Expect

Once you click "Analyze Transaction":

1. **Loading indicator** appears
2. **Risk Level** displayed as large colored header:
   - 🟢 LOW
   - 🟡 MEDIUM
   - 🔴 HIGH
3. **Fraud Score** (0–100):
   - Metric box showing number
   - Progress bar (fills as score increases)
4. **Recommendation:**
   - ✅ APPROVE (green)
   - ⚠️ REVIEW (orange)
   - ❌ DECLINE (red)
5. **Detected Flags** (if any):
   - List of red flags detected (e.g., `GEO_ANOMALY`, `UNUSUAL_AMOUNT`, etc.)

#### Example Run (Low Risk → Approve)

```
Customer ID: C-00001
Amount: $50.00
MCC: 5411
Location: Bucharest
Date: 2026-04-08
Time: 14:30
Channel: POS

[Click "Analyze Transaction"]

### Risk Level: LOW 🟢

Fraud Score
18/100
[=====>                              ] (progress bar)

Recommendation: APPROVE ✅

No fraud flags detected
```

#### Example Run (Medium Risk → Review)

```
Customer ID: C-00001
Amount: $10,000.00
MCC: 6211
Location: Singapore
Date: 2026-04-08
Time: 02:15
Channel: ONL

[Click "Analyze Transaction"]

### Risk Level: MEDIUM 🟡

Fraud Score
62/100
[=========================>          ] (progress bar)

Recommendation: REVIEW ⚠️

Detected Flags:
🚩 GEO_ANOMALY    🚩 AMOUNT_ANOMALY    🚩 UNUSUAL_TIME
```

#### Channel Codes

| Code | Meaning |
|------|---------|
| POS | Point of Sale (in-store card swipe/chip) |
| ATM | Automated Teller Machine (cash withdrawal) |
| ONL | Online (web or app purchase) |
| MOB | Mobile (mobile app transaction) |

#### Common Fraud Flags

| Flag | Meaning |
|------|---------|
| GEO_ANOMALY | Location different from customer's usual area |
| AMOUNT_ANOMALY | Amount much higher than customer's typical spend |
| VELOCITY | Too many transactions in short time |
| NEW_MERCHANT_CAT | Category never purchased before |
| UNUSUAL_TIME | Transaction at unusual time (2am, etc.) |
| AMOUNT_EXCEEDS_AVG | Amount exceeds average by 3+ standard deviations |

#### Error Cases

**Invalid MCC format:**
```
❌ MCC must be a 4-digit number
```
→ Enter exactly 4 digits, e.g., `5411`

**Script failure:**
```
❌ Execution error: Script python/fraud_detect.py exited with code 1
```

---

## Understanding Outputs

### Numeric Formatting

| Type | Example | Format |
|------|---------|--------|
| Currency (USD) | Account Balance | `$1,234.56` (comma-separated, 2 decimals) |
| Percentage | Interest Rate | `4.50%` |
| Integer | Transaction Count | `1247` (no decimals) |
| Score | Risk Score | `324/999` or `62/100` |

### Color Meanings

| Color | Meaning | Context |
|-------|---------|---------|
| 🟢 Green | Safe / Good | Low risk, approved, good credit |
| 🟡 Yellow/Orange | Caution / Neutral | Medium risk, manual review needed |
| 🔴 Red | Danger / Bad | High risk, declined, low credit |

### Return Codes (Behind the Scenes)

All backend scripts return a code in the last 2 bytes:

- `00` — Success (normal result)
- `01` — Not found (customer doesn't exist)
- `99` — System error (backend failure)

**You will see:** Error messages instead of raw codes. Example:
```
❌ Parse error: Customer not found — check customer ID
```

---

## Troubleshooting

### Issue: "command not found: streamlit"

**Problem:** Streamlit not installed.

**Solution:**
```bash
pip install streamlit
```

Then try again:
```bash
streamlit run ui/app.py
```

---

### Issue: "ModuleNotFoundError: No module named 'ui.runner'"

**Problem:** Running from wrong directory or ui/ doesn't exist.

**Solution:**

1. Navigate to project root:
   ```bash
   cd C:\Users\[YourUsername]\Desktop\cobol-bigdata
   ```

2. Verify ui/ exists:
   ```bash
   dir ui
   ```
   (On Linux: `ls ui`)

3. Try again:
   ```bash
   streamlit run ui/app.py
   ```

---

### Issue: "Script not found: python/customer_360.py"

**Problem:** Project root is incorrect or Python script missing.

**Solution:**

1. Verify you're in the project root:
   ```bash
   dir python
   ```
   Should show: `customer_360.py`, `loan_scoring.py`, `fraud_detect.py`, `utils/`

2. Verify script exists:
   ```bash
   dir python\customer_360.py
   ```

3. Try running the script directly:
   ```bash
   python python/customer_360.py C-00001
   ```
   Should return a 145-byte output.

---

### Issue: "Customer not found" when entering C-00001

**Problem:** Data files not generated or customer ID is invalid.

**Solution:**

1. Verify data files exist:
   ```bash
   dir data\*.parquet
   ```
   Should show: `customers.parquet`, `loans.parquet`, `fraud_labels.parquet`

2. If missing, generate data:
   ```bash
   python data/generate_synthetic.py
   ```
   (Takes 5–10 minutes)

3. Try a different customer ID (C-00001 through C-100000 exist)

---

### Issue: UI is very slow (>5 seconds to respond)

**Problem:** Streamlit is rerunning the entire script on every action (normal), but queries are slow.

**Solution:**

1. This is expected behavior on first query (DuckDB initializes)
2. Subsequent queries should be faster
3. If consistently slow (>10 seconds):
   - Ensure you have enough disk space
   - Check if antivirus is scanning the data directory
   - Try a simpler query first (e.g., Tab 1 lookup vs. Tab 3 fraud detection)

---

### Issue: "Port 8501 already in use"

**Problem:** Another Streamlit instance is running or port is occupied.

**Solution:**

```bash
# Stop the existing process
# Press Ctrl+C in the terminal where streamlit is running

# Or run on a different port
streamlit run ui/app.py --server.port 8502
```

Browser will open at `http://localhost:8502`

---

### Issue: "Invalid MCC" error when I enter a 4-digit code

**Problem:** MCC field contains non-numeric characters.

**Solution:**

- Clear the field
- Enter only digits (0–9)
- Must be exactly 4 characters

Example: `5411` ✅ | `541A` ❌ | `541` ❌

---

## FAQ

### Q: Can I modify the UI code?

**A:** Yes! The UI (`ui/app.py`, `ui/runner.py`, `ui/parse.py`) is yours to modify. However, the backend scripts (`python/customer_360.py`, etc.) should not be changed for thesis purposes.

### Q: Why does the UI run locally and not on the internet?

**A:** The UI is designed for demo and thesis presentation. For production deployment, you would need to deploy it to Streamlit Cloud, AWS, or another hosting provider. Instructions for that are outside the scope of this guide.

### Q: Can I run the UI on my phone or another computer?

**A:** Only if they're on the same network. You can bind Streamlit to your machine's IP:
```bash
streamlit run ui/app.py --server.address 0.0.0.0
```
Then access from another computer: `http://[your-ip]:8501`

**Warning:** This opens the UI to your entire network. Use only for testing.

### Q: What if I want to test with my own data?

**A:** Replace the Parquet files in `data/`:
- `customers.parquet` (must have columns: customer_id, name, credit_score, etc.)
- `loans.parquet`
- `fraud_labels.parquet`
- `transactions/*.parquet` (partitioned by date)

Consult `python/utils/parquet_reader.py` for required column names.

### Q: Can I export the results?

**A:** Not from the current UI. To export, you can:
1. Take a screenshot
2. Copy the displayed results to a document
3. Modify `ui/app.py` to add `st.download_button()` for CSV export

### Q: What if the backend scripts don't work?

**A:** Test them directly:
```bash
python python/customer_360.py C-00001
python python/loan_scoring.py C-00001 10000 36 PERS
python python/fraud_detect.py C-00001 500 5411 Bucharest "2026-04-08T14:30:00" POS
```

Each should return a fixed-width record (145, 51, 78 bytes respectively). If they fail, check:
- Python version (should be 3.11+)
- Installed packages: `pip install pyarrow duckdb faker numpy`
- Data files exist: `data/*.parquet`

### Q: Is the UI thread-safe for multiple users?

**A:** No. Streamlit is single-user by default. Each user gets their own session. For multiple concurrent users, deploy to Streamlit Cloud or use load balancing. This is beyond the thesis scope.

### Q: How do I stop the UI?

**A:** Press **Ctrl+C** in the terminal where you ran `streamlit run ui/app.py`.

---

## Support

If you encounter an issue not covered here:

1. Check the **Troubleshooting** section above
2. Review `docs/development_plan.md` for architecture details
3. Review `docs/ui_design.md` for design decisions
4. Inspect error messages in the terminal (they're usually descriptive)

---

## Next Steps

Once you're comfortable with the UI:

1. **Test with different data:**
   - Try all three tabs
   - Test error cases (invalid customer, declined loans, etc.)

2. **Use for thesis presentation:**
   - Run the UI during your defense
   - Show live results from the three analytics modules

3. **Optional enhancements:**
   - Add CSV export functionality
   - Add user authentication
   - Deploy to Streamlit Cloud for remote access

---

## Summary

The UI is a **three-tab Streamlit application** for testing the hybrid COBOL-Python banking system:

- **Tab 1:** Customer 360 — View customer profile
- **Tab 2:** Loan Assessment — Check loan eligibility
- **Tab 3:** Fraud Detection — Analyze transaction risk

**To run:**
```bash
pip install streamlit
streamlit run ui/app.py
```

**To stop:**
```
Ctrl+C in the terminal
```

Enjoy!

