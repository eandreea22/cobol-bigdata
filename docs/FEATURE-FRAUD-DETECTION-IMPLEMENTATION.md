# Fraud Detection Enhancement: Implementation Guide

**Date:** 2026-04-15  
**Phase:** Implementation (Ready to Code)  
**Estimated Effort:** 4-6 hours (Backend 2h + UI 3h + Testing 1h)

---

## Pre-Implementation Checklist

Before starting implementation, verify:

- [ ] Design document reviewed: `FEATURE-FRAUD-DETECTION-ENHANCEMENT.md`
- [ ] Data schema confirmed: Check `data/transactions.parquet` columns
- [ ] DuckDB + pyarrow installed and working
- [ ] Streamlit running without errors
- [ ] All existing tests passing

---

## Phase 1: Backend Implementation (2 hours)

### Step 1.1: Verify Data Schema

**Goal:** Confirm transactions.parquet structure before writing code

```bash
# Run in terminal
python3 << 'EOF'
import duckdb
import pandas as pd

# Connect to DuckDB
conn = duckdb.connect()

# Query transactions schema
result = conn.execute("""
    SELECT *
    FROM 'data/transactions/*.parquet'
    LIMIT 1
""").fetch_df()

print("Columns in transactions.parquet:")
print(result.columns.tolist())
print("\nFirst row:")
print(result.head())
print("\nData types:")
print(result.dtypes)
EOF
```

**Expected Output:**
```
Columns in transactions.parquet:
['customer_id', 'txn_id', 'date', 'amount', 'mcc', 'location', 'channel', ...]

Data types:
customer_id: object
date: datetime64[ns] or object
amount: float64
mcc: object
location: object
channel: object
```

**If schema differs:** Update implementation plan accordingly

---

### Step 1.2: Create python/customer_transactions.py

**File Path:** `C:\Users\Andreea\Desktop\cobol-bigdata\python\customer_transactions.py`

**Implementation:**

```python
#!/usr/bin/env python3
"""
Fetch transaction list for a customer.

Usage:
    python3 customer_transactions.py <customer_id> [limit] [offset]

Example:
    python3 customer_transactions.py C-00001 10 0

Output (pipe-delimited):
    <count>
    <txn_id>|<date>|<amount>|<mcc>|<location>|<channel>
    ...

Error Cases:
    - Customer not found: count=0
    - Query error: error message to stderr, exit code 99
"""

import sys
import duckdb
from pathlib import Path

def main():
    # Parse arguments
    if len(sys.argv) < 2:
        print("Error: customer_id required", file=sys.stderr)
        sys.exit(99)
    
    customer_id = sys.argv[1].strip()
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    offset = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    
    try:
        # Connect to DuckDB
        conn = duckdb.connect(':memory:')
        
        # Query transactions for this customer
        # Note: Adjust column names based on actual data schema
        result = conn.execute(f"""
            SELECT 
                txn_id,
                date,
                amount,
                mcc,
                location,
                channel
            FROM 'data/transactions/*.parquet'
            WHERE customer_id = '{customer_id}'
            ORDER BY date DESC
            LIMIT {limit} OFFSET {offset}
        """).fetchall()
        
        # Get total count for pagination
        count_result = conn.execute(f"""
            SELECT COUNT(*) as total
            FROM 'data/transactions/*.parquet'
            WHERE customer_id = '{customer_id}'
        """).fetchone()
        
        total_count = count_result[0]
        
        # Output format: count as first line
        print(total_count)
        
        # Then output each transaction as pipe-delimited
        for row in result:
            txn_id, date, amount, mcc, location, channel = row
            
            # Format date as YYYY-MM-DD if it's a date object
            if hasattr(date, 'strftime'):
                date_str = date.strftime('%Y-%m-%d')
            else:
                date_str = str(date)[:10]  # Take first 10 chars if string
            
            # Format amount as decimal
            amount_str = f"{amount:.2f}"
            
            # Clean strings (remove pipes to avoid parsing issues)
            location = str(location).replace('|', ' ')
            
            # Output pipe-delimited row
            print(f"{txn_id}|{date_str}|{amount_str}|{mcc}|{location}|{channel}")
        
        sys.exit(0)
    
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(99)

if __name__ == '__main__':
    main()
```

**Testing:**

```bash
# Test with a customer that should exist
python3 python/customer_transactions.py C-00001 5 0

# Expected output:
# 42                          (total count for this customer)
# TXN-001|2025-01-15|500.00|5411|Bucharest|POS
# TXN-002|2025-01-14|120.00|6011|Iasi|ATM
# ...

# Test with invalid customer
python3 python/customer_transactions.py C-99999 5 0
# Expected output:
# 0                           (count=0 for non-existent customer)
```

**Verification Checklist:**
- [ ] Script runs without errors
- [ ] Returns correct count
- [ ] Returns transactions in date DESC order (newest first)
- [ ] Format is correct (pipe-delimited, count on first line)
- [ ] Pagination works (offset parameter)
- [ ] Handles non-existent customer (returns 0)

---

### Step 1.3: Update ui/parse.py

**File Path:** `C:\Users\Andreea\Desktop\cobol-bigdata\ui\parse.py`

**Add this function:**

```python
def parse_customer_transactions(raw: str) -> dict:
    """
    Parse customer transactions response from customer_transactions.py
    
    Format:
        <count>
        <txn_id>|<date>|<amount>|<mcc>|<location>|<channel>
        ...
    
    Args:
        raw: Raw output from customer_transactions.py
    
    Returns:
        {
            'count': int,
            'transactions': [
                {
                    'txn_id': str,
                    'date': str,
                    'amount': float,
                    'mcc': str,
                    'location': str,
                    'channel': str
                },
                ...
            ]
        }
    
    Raises:
        ValueError: If format is invalid
    """
    lines = raw.strip().split('\n')
    
    if not lines:
        raise ValueError("Empty response")
    
    # First line is count
    try:
        count = int(lines[0])
    except ValueError:
        raise ValueError(f"Invalid count in first line: {lines[0]}")
    
    transactions = []
    
    # Parse remaining lines (one transaction per line)
    for i, line in enumerate(lines[1:], start=1):
        if not line.strip():
            continue
        
        parts = line.split('|')
        if len(parts) < 6:
            raise ValueError(f"Line {i}: Not enough fields (expected 6, got {len(parts)})")
        
        try:
            transaction = {
                'txn_id': parts[0].strip(),
                'date': parts[1].strip(),
                'amount': float(parts[2]),
                'mcc': parts[3].strip(),
                'location': parts[4].strip(),
                'channel': parts[5].strip()
            }
            transactions.append(transaction)
        except (ValueError, IndexError) as e:
            raise ValueError(f"Line {i}: Failed to parse transaction: {str(e)}")
    
    # Validate count matches number of transactions
    if len(transactions) != count and count > 0:
        # Note: count might be total (for pagination), transactions might be partial
        # So we don't strictly enforce this, just log it
        pass
    
    return {
        'count': count,
        'transactions': transactions
    }
```

**Testing:**

```python
# Test 1: Valid response
raw = """3
TXN-001|2025-01-15|500.00|5411|Bucharest|POS
TXN-002|2025-01-14|120.00|6011|Iasi|ATM
TXN-003|2025-01-13|45.99|5499|OnlineStore|ONL
"""

result = parse_customer_transactions(raw)
assert result['count'] == 3
assert len(result['transactions']) == 3
assert result['transactions'][0]['amount'] == 500.00

# Test 2: Empty list
raw = "0"
result = parse_customer_transactions(raw)
assert result['count'] == 0
assert result['transactions'] == []

# Test 3: Invalid format
try:
    parse_customer_transactions("invalid")
    assert False, "Should raise ValueError"
except ValueError:
    pass  # Expected
```

**Verification Checklist:**
- [ ] Function parses valid input correctly
- [ ] Returns dict with 'count' and 'transactions' keys
- [ ] Amount is converted to float
- [ ] Handles empty list (count=0)
- [ ] Raises ValueError on invalid format

---

## Phase 2: UI Implementation (3 hours)

### Step 2.1: Update ui/app.py - Add Helper Function

**Location:** In `ui/app.py`, add this function before `page_fraud_detection()`:

```python
def fetch_customer_transactions(customer_id: str, limit: int = 10, offset: int = 0) -> dict:
    """
    Fetch transactions for a customer.
    
    Args:
        customer_id: Customer ID (e.g., "C-00001")
        limit: Number of transactions to fetch per page
        offset: Number of transactions to skip (for pagination)
    
    Returns:
        {
            'count': int,
            'transactions': [...]
        }
    """
    try:
        raw = run_script("python/customer_transactions.py", [customer_id, str(limit), str(offset)])
        return parse_customer_transactions(raw)
    except Exception as e:
        st.error(f"Failed to fetch transactions: {str(e)}")
        return {'count': 0, 'transactions': []}
```

---

### Step 2.2: Update ui/app.py - Modify page_fraud_detection()

**Location:** Find the `page_fraud_detection()` function and update it.

**Current structure (before modification):**

```python
def page_fraud_detection():
    # 1. Search for customer
    cid = search_widget("fraud")
    
    if not cid:
        st.info("👆 Search for a customer above to continue")
        return
    
    # 2. Display selected customer (read-only)
    customer_info = st.session_state.get("selected_customer_info_fraud", {})
    customer_name = customer_info.get("name", "")
    display_text = f"{customer_name} — {cid}" if customer_name else cid
    
    st.markdown(...)
    
    # 3. Form for manual entry
    with st.form("f_fraud"):
        amount = st.number_input(...)
        mcc = st.text_input(...)
        location = st.text_input(...)
        channel = st.selectbox(...)
        # ... etc
```

**Modification: Add transaction list after customer selection**

```python
def page_fraud_detection():
    # 1. Search for customer
    cid = search_widget("fraud")
    
    if not cid:
        st.info("👆 Search for a customer above to continue")
        return
    
    # 2. Display selected customer (read-only)
    customer_info = st.session_state.get("selected_customer_info_fraud", {})
    customer_name = customer_info.get("name", "")
    display_text = f"{customer_name} — {cid}" if customer_name else cid
    
    st.markdown(
        f'<div style="background:#f1f5f9;padding:1rem;border-radius:8px;margin-bottom:1.5rem">'
        f'<div style="font-size:.75rem;text-transform:uppercase;color:#64748b;font-weight:600;margin-bottom:.3rem">Selected Customer</div>'
        f'<div style="font-size:1.1rem;font-weight:600;color:#0f172a">{display_text}</div>'
        f'</div>',
        unsafe_allow_html=True
    )
    
    # ══════════════════════════════════════════════════════════
    # NEW: Fetch and display transaction list
    # ══════════════════════════════════════════════════════════
    
    # Initialize session state for pagination
    if "fraud_txn_page" not in st.session_state:
        st.session_state.fraud_txn_page = 1
    if "fraud_selected_txn_idx" not in st.session_state:
        st.session_state.fraud_selected_txn_idx = 0
    
    # Pagination
    page_num = st.session_state.fraud_txn_page
    offset = (page_num - 1) * 10
    
    # Fetch transactions
    with st.spinner("Loading transactions..."):
        txn_result = fetch_customer_transactions(cid, limit=10, offset=offset)
    
    transactions = txn_result['transactions']
    total_txns = txn_result['count']
    
    if total_txns == 0:
        st.warning("No transactions found for this customer. Enter details manually below.")
        # Fall through to manual form
    else:
        # Display transaction list
        st.subheader("Recent Transactions")
        
        # Create table for display
        table_data = []
        for idx, txn in enumerate(transactions):
            table_data.append({
                "Date": txn['date'],
                "Amount": f"${txn['amount']:.2f}",
                "MCC": txn['mcc'],
                "Location": txn['location'],
                "Channel": txn['channel']
            })
        
        # Show table (use columns for clickable rows)
        cols = st.columns([2, 2, 1, 2, 2])
        with cols[0]:
            st.write("**Date**")
        with cols[1]:
            st.write("**Amount**")
        with cols[2]:
            st.write("**MCC**")
        with cols[3]:
            st.write("**Location**")
        with cols[4]:
            st.write("**Channel**")
        
        st.divider()
        
        # Display each transaction as clickable row
        for idx, txn in enumerate(transactions):
            is_selected = (st.session_state.fraud_selected_txn_idx == idx)
            
            # Highlight selected row
            row_bg = "#f0f0f0" if is_selected else "transparent"
            
            cols = st.columns([2, 2, 1, 2, 2])
            with cols[0]:
                if st.button(
                    txn['date'],
                    key=f"fraud_txn_{page_num}_{idx}_date",
                    use_container_width=True
                ):
                    st.session_state.fraud_selected_txn_idx = idx
                    st.rerun()
            
            with cols[1]:
                if st.button(
                    f"${txn['amount']:.2f}",
                    key=f"fraud_txn_{page_num}_{idx}_amount",
                    use_container_width=True
                ):
                    st.session_state.fraud_selected_txn_idx = idx
                    st.rerun()
            
            with cols[2]:
                st.write(txn['mcc'])
            
            with cols[3]:
                st.write(txn['location'][:20])  # Truncate long names
            
            with cols[4]:
                st.write(txn['channel'])
        
        # Pagination controls
        st.divider()
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if st.button("← Previous", disabled=(page_num <= 1)):
                st.session_state.fraud_txn_page -= 1
                st.rerun()
        
        with col2:
            max_pages = (total_txns + 9) // 10  # Ceiling division
            st.write(f"Page {page_num} of {max_pages}")
        
        with col3:
            if st.button("Next →", disabled=(page_num * 10 >= total_txns)):
                st.session_state.fraud_txn_page += 1
                st.rerun()
        
        # Store selected transaction in session state
        if transactions:
            selected_txn = transactions[st.session_state.fraud_selected_txn_idx]
            st.session_state.fraud_selected_transaction = selected_txn
    
    # ══════════════════════════════════════════════════════════
    # Form for fraud analysis (pre-filled from selected transaction)
    # ══════════════════════════════════════════════════════════
    
    st.subheader("Transaction Analysis")
    
    # Get selected transaction (if any)
    selected_txn = st.session_state.get("fraud_selected_transaction", {})
    
    # Pre-fill form with transaction data
    default_amount = selected_txn.get('amount', 0)
    default_mcc = selected_txn.get('mcc', '')
    default_location = selected_txn.get('location', '')
    default_channel = selected_txn.get('channel', 'POS')
    default_date = selected_txn.get('date', '')
    
    with st.form("f_fraud"):
        amount = st.number_input(
            "Amount",
            min_value=0.01,
            value=float(default_amount) if default_amount else 0.01,
            step=0.01
        )
        mcc = st.text_input(
            "MCC (4-digit code)",
            value=default_mcc,
            placeholder="e.g. 5411"
        )
        location = st.text_input(
            "Location",
            value=default_location,
            placeholder="e.g. Bucharest"
        )
        channel = st.selectbox(
            "Channel",
            ("POS", "ATM", "ONL", "MOB"),
            index=("POS", "ATM", "ONL", "MOB").index(default_channel) if default_channel else 0
        )
        
        # Parse default date for datetime input
        if default_date:
            import datetime
            try:
                date_obj = datetime.datetime.strptime(default_date, "%Y-%m-%d")
                default_dt = datetime.datetime.combine(date_obj.date(), datetime.time(12, 0))
            except:
                default_dt = datetime.datetime.now()
        else:
            default_dt = datetime.datetime.now()
        
        dt = st.date_input("Date", value=default_dt.date())
        tm = st.time_input("Time", value=default_dt.time())
        timestamp = f"{dt.isoformat()}T{tm.isoformat()}"
        
        go = st.form_submit_button("🔍 Analyse for Fraud")
    
    if go:
        # Validate inputs
        if not mcc or len(mcc) != 4 or not mcc.isdigit():
            st.error("MCC must be exactly 4 digits")
            return
        if not location.strip():
            st.error("Location is required")
            return
        
        # Run fraud detection
        with st.spinner("Analyzing transaction…"):
            try:
                raw = run_script(
                    "python/fraud_detect.py",
                    [cid, str(amount), mcc, location, timestamp, channel]
                )
                result = parse_fraud_detect(raw)
                
                # Display results
                st.success("Analysis complete")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    risk_color = {
                        "LOW": "#28a745",
                        "MEDIUM": "#ffc107",
                        "HIGH": "#dc3545"
                    }.get(result['risk_level'], "#999")
                    
                    st.markdown(
                        f'<div style="background:{risk_color};color:white;padding:1rem;'
                        f'border-radius:8px;text-align:center">'
                        f'<div style="font-size:.75rem;text-transform:uppercase;font-weight:600">'
                        f'Risk Level</div>'
                        f'<div style="font-size:2rem;font-weight:bold">'
                        f'{result["risk_level"]}</div></div>',
                        unsafe_allow_html=True
                    )
                
                with col2:
                    st.metric("Fraud Score", f"{result['fraud_score']}/100")
                
                with col3:
                    rec_color = {
                        "APPROVE": "#28a745",
                        "REVIEW": "#ffc107",
                        "DECLINE": "#dc3545"
                    }.get(result['recommendation'], "#999")
                    
                    st.markdown(
                        f'<div style="background:{rec_color};color:white;padding:1rem;'
                        f'border-radius:8px;text-align:center">'
                        f'<div style="font-size:.75rem;text-transform:uppercase;font-weight:600">'
                        f'Recommendation</div>'
                        f'<div style="font-size:1.5rem;font-weight:bold">'
                        f'{result["recommendation"]}</div></div>',
                        unsafe_allow_html=True
                    )
                
                st.divider()
                st.subheader("Detected Flags")
                for flag in result['flags']:
                    st.write(f"✓ {flag}")
            
            except Exception as e:
                st.error(f"Error: {str(e)}")
```

**Verification Checklist:**
- [ ] Transaction list displays correctly
- [ ] Pagination works (Previous/Next buttons)
- [ ] Clicking a transaction pre-fills the form
- [ ] Form fields update when transaction is selected
- [ ] Fraud analysis runs with pre-filled data
- [ ] Results display correctly

---

## Phase 3: Testing (1 hour)

### Step 3.1: Unit Tests

**File:** `tests/test_fraud_transactions.py` (create if needed)

```python
import pytest
from ui.parse import parse_customer_transactions

def test_parse_customer_transactions_valid():
    raw = """3
TXN-001|2025-01-15|500.00|5411|Bucharest|POS
TXN-002|2025-01-14|120.00|6011|Iasi|ATM
TXN-003|2025-01-13|45.99|5499|OnlineStore|ONL
"""
    result = parse_customer_transactions(raw)
    assert result['count'] == 3
    assert len(result['transactions']) == 3
    assert result['transactions'][0]['amount'] == 500.0
    assert result['transactions'][0]['date'] == '2025-01-15'

def test_parse_customer_transactions_empty():
    raw = "0"
    result = parse_customer_transactions(raw)
    assert result['count'] == 0
    assert result['transactions'] == []

def test_parse_customer_transactions_invalid():
    with pytest.raises(ValueError):
        parse_customer_transactions("invalid")
```

---

### Step 3.2: Integration Tests

**Run manually in browser:**

```
Test 1: Search and select customer
[ ] Open Fraud Detection page
[ ] Search for "Smith"
[ ] Click to select "John Smith — C-00001"
[ ] Verify customer displays

Test 2: Transaction list appears
[ ] Verify "Recent Transactions" section appears
[ ] Verify table shows date, amount, MCC, location, channel
[ ] Verify most recent transaction is pre-selected (first row)

Test 3: Transaction selection
[ ] Click second transaction in list
[ ] Verify form fields update with second transaction's data
[ ] Verify amount, MCC, location, channel all match

Test 4: Form pre-filling
[ ] Select transaction with amount $500
[ ] Verify "Amount" field shows 500.00
[ ] Verify "MCC" field matches transaction
[ ] Verify "Location" field matches transaction

Test 5: Pagination
[ ] Click "Next →" button
[ ] Verify next 10 transactions load
[ ] Verify page counter updates
[ ] Click transaction on page 2
[ ] Verify it pre-fills form correctly

Test 6: Fraud analysis
[ ] Select a transaction
[ ] Click "Analyse for Fraud"
[ ] Verify fraud detection runs
[ ] Verify results display (risk level, score, recommendation)

Test 7: Manual override
[ ] Select transaction from list
[ ] Manually edit "Amount" field (change value)
[ ] Click "Analyse for Fraud"
[ ] Verify analysis uses edited value (not transaction value)

Test 8: Empty transactions
[ ] Find customer with 0 transactions (or create synthetic test)
[ ] Verify message "No transactions found for this customer"
[ ] Verify manual form still appears
[ ] User can enter custom details

Test 9: Edge cases
[ ] Very long location name (truncates correctly)
[ ] Special characters in location
[ ] Customer with 1000+ transactions (pagination works)
```

---

### Step 3.3: Performance Testing

```bash
# Test query speed
time python3 python/customer_transactions.py C-00001 10 0

# Expected: < 100ms
# Acceptable: < 200ms
```

---

## Integration Checklist

Before marking complete:

- [ ] `python/customer_transactions.py` working and tested
- [ ] `parse_customer_transactions()` added to `ui/parse.py`
- [ ] `page_fraud_detection()` updated in `ui/app.py`
- [ ] All helper functions added (`fetch_customer_transactions()`)
- [ ] UI renders without errors
- [ ] Transaction list displays for real customer
- [ ] Pagination works
- [ ] Form pre-filling works
- [ ] Fraud analysis runs with correct data
- [ ] All manual tests pass
- [ ] Unit tests pass
- [ ] Performance acceptable (< 200ms)

---

## Rollback Plan

If issues arise, can quickly rollback:

1. Revert `ui/app.py` to previous version (move transaction list + form update to comments)
2. Keep `python/customer_transactions.py` as optional script
3. Keep `parse_customer_transactions()` in `ui/parse.py` (unused)
4. UI reverts to manual form only (no transaction list)

---

## Known Limitations & Future Improvements

### Current Limitations
1. Transaction list limited to 10 per page (by design for performance)
2. No search/filter within customer's transactions
3. No "batch analyze" option (one transaction at a time)
4. No transaction details modal

### Future Improvements (Not in scope)
1. Add search by amount range within transactions list
2. Add date range filter
3. Add "analyze all transactions" option
4. Add transaction details modal with full data
5. Add transaction history chart (showing fraud scores over time)

---

## Success Metrics

After implementation, measure:

1. **Usability:** Can new users select a transaction without instructions?
2. **Accuracy:** Do pre-filled forms match transaction data correctly?
3. **Performance:** Does transaction list load in < 200ms?
4. **Reliability:** Does it work for customers with 0, 10, 100, 1000+ transactions?
5. **Compatibility:** Does it work with all browsers?

---

## Support & Documentation

After implementation:

- [ ] Update user guide with screenshots
- [ ] Add FAQ about transaction selection
- [ ] Update troubleshooting guide
- [ ] Document any known issues or limitations

---

**Status:** Ready for implementation  
**Last Updated:** 2026-04-15

