# Fraud Detection Enhancement: Transaction-Based Analysis

**Date:** 2026-04-15  
**Feature:** Fraud Detection with Transaction List  
**Status:** 🎯 DESIGN PHASE (Ready for Implementation)

---

## Executive Summary

The current Fraud Detection page requires users to manually enter transaction details (amount, MCC, location, channel, timestamp). This enhancement improves the UX and accuracy by displaying actual customer transactions, allowing users to select a real transaction to analyze instead of guessing or recalling transaction details.

**Expected Outcome:**
- More intuitive workflow (see real data → pick one → analyze)
- Fewer data entry errors
- Better user experience
- No changes to existing COBOL/Python core

---

## Current State vs. Proposed State

### Current Fraud Detection Flow
```
1. User opens Fraud Detection page
2. Search for customer by last name
3. Select customer → see customer ID (read-only)
4. Fill in form MANUALLY:
   ├─ Amount (user guesses/remembers)
   ├─ MCC (user enters 4 digits)
   ├─ Location (user types)
   ├─ Channel (user selects)
   └─ Timestamp (user enters date+time)
5. Click "Run Fraud Detection"
6. See results
```

**Problems:**
- ❌ Users may enter wrong data or misremember
- ❌ No context about what transaction actually was
- ❌ Requires knowledge of MCC codes (not user-friendly)
- ❌ Potential for typos or incorrect data

### Proposed Fraud Detection Flow
```
1. User opens Fraud Detection page
2. Search for customer by last name
3. Select customer → see customer ID (read-only)
4. System automatically fetches recent transactions
5. Display transaction list:
   ├─ Date | Amount | MCC | Location | Channel
   ├─ Pagination (10 per page)
   └─ Most recent pre-selected
6. User optionally:
   ├─ Click different transaction to select it
   └─ Manually edit any field if needed
7. Click "Analyse" button
8. See fraud detection results
```

**Benefits:**
- ✅ See actual transaction data
- ✅ Pick a real transaction from history
- ✅ Pre-filled form (less typing)
- ✅ Better accuracy
- ✅ More context-aware analysis

---

## User Flow: Step-by-Step

### Step 1: Page Load & Search
```
┌──────────────────────────────────────┐
│ 🔍 FRAUD DETECTION                   │
├──────────────────────────────────────┤
│ Search by Last Name                  │
│ [Smith_______] [Search]              │
└──────────────────────────────────────┘

User types "Smith" and clicks Search
```

### Step 2: Search Results
```
┌──────────────────────────────────────┐
│ 2 results found                      │
│                                      │
│ John Smith — C-00001 · NYC [→]       │
│ Jane Smith — C-00005 · BOS [→]       │
└──────────────────────────────────────┘

User clicks [→] next to "John Smith"
```

### Step 3: Customer Selected
```
┌──────────────────────────────────────┐
│ ✓ Selected: C-00001                  │
│ (Page auto-loads)                    │
└──────────────────────────────────────┘

Page fetches transactions for C-00001
```

### Step 4: Transaction List Appears
```
┌──────────────────────────────────────┐
│ Recent Transactions for C-00001      │
│                                      │
│ Date       │ Amount │ MCC  │ Channel │
│ ────────────────────────────────     │
│ ☑ 2025-01-15 │ $500  │ 5411 │ POS    │  ← Pre-selected
│ ☐ 2025-01-14 │ $120  │ 6011 │ ATM    │
│ ☐ 2025-01-13 │ $45   │ 5499 │ ONL    │
│                                      │
│ [← Previous] [Page 1 of 5] [Next →]  │
└──────────────────────────────────────┘

Most recent transaction automatically pre-selected
User can click other rows to select different one
```

### Step 5: Form Auto-Fills
```
┌──────────────────────────────────────┐
│ Transaction Details (Pre-filled)    │
│                                      │
│ Amount: 500                          │
│ MCC: 5411                            │
│ Location: Bucharest                  │
│ Channel: POS                         │
│ Timestamp: 2025-01-15 14:23         │
│                                      │
│ [Analyse]                            │
└──────────────────────────────────────┘

Form shows values from selected transaction
User can edit if needed (e.g., to test "what if" scenarios)
```

### Step 6: Results
```
┌──────────────────────────────────────┐
│ Fraud Analysis Results              │
├──────────────────────────────────────┤
│ Risk Level: LOW                      │
│ Fraud Score: 12/100                  │
│                                      │
│ Detected Flags:                      │
│ ✓ Amount within normal range         │
│ ✓ Location matches history           │
│ ✓ Time within typical window         │
│                                      │
│ Recommendation: APPROVE              │
└──────────────────────────────────────┘
```

---

## Technical Architecture

### Component Breakdown

#### 1. Backend: New Python Script
```
File: python/customer_transactions.py
Purpose: Fetch transaction list for a customer

Usage:
  python3 python/customer_transactions.py <customer_id> [limit=10] [offset=0]

Example:
  python3 python/customer_transactions.py C-00001 10 0
  
Output (pipe-delimited):
  <count>
  <txn_id>|<date>|<amount>|<mcc>|<location>|<channel>
  <txn_id>|<date>|<amount>|<mcc>|<location>|<channel>
  ...

Example Output:
  5
  TXN-001|2025-01-15|500.00|5411|Bucharest|POS
  TXN-002|2025-01-14|120.00|6011|Iasi|ATM
  TXN-003|2025-01-13|45.99|5499|OnlineStore|ONL
  (etc.)

Error Cases:
  - Customer not found: count=0 (empty list)
  - Query error: return error message with return code
```

#### 2. Parsing: Update ui/parse.py
```python
def parse_customer_transactions(raw: str) -> dict:
    """
    Parse customer transactions response
    
    Returns:
        {
            'count': int,
            'transactions': [
                {
                    'txn_id': str,
                    'date': str,       # YYYY-MM-DD
                    'amount': float,
                    'mcc': str,
                    'location': str,
                    'channel': str
                },
                ...
            ]
        }
    """
```

#### 3. UI: Update Fraud Detection Page
```python
def page_fraud_detection():
    # 1. Search widget
    cid = search_widget("fraud")
    
    if not cid:
        st.info("👆 Search for a customer above to continue")
        return
    
    # 2. Show selected customer (existing)
    # ... (existing code)
    
    # 3. NEW: Fetch and display transactions
    with st.spinner("Loading transactions..."):
        transactions = fetch_customer_transactions(cid)
    
    if transactions['count'] == 0:
        st.warning("No transactions found for this customer")
        # Fall back to manual entry
        # ... (existing manual form)
    else:
        # 4. NEW: Display transaction list with pagination
        page = st.number_input("Page", min_value=1, ...)
        display_transaction_list(transactions, page)
        
        # 5. NEW: Handle selection (click row → pre-fill form)
        selected_txn = get_selected_transaction()
        
        # 6. Show form with pre-filled values from selected transaction
        # ... (existing form, but with default values from transaction)
        
        # 7. User clicks "Analyse"
        # ... (existing analysis code)
```

---

## Data Schema

### transactions.parquet Layout
Expected fields in the data:
```
├─ customer_id (string): C-00001, C-00002, etc.
├─ txn_id (string): unique transaction identifier
├─ date (date or timestamp): YYYY-MM-DD or ISO format
├─ amount (decimal): transaction amount in currency units
├─ mcc (string): merchant category code (4 digits)
├─ location (string): transaction location/merchant name
├─ channel (string): POS, ATM, ONL, MOB
└─ (optional) other fields: status, description, etc.
```

---

## Implementation Scope

### What's Being Added
1. ✅ New Python script: `python/customer_transactions.py`
2. ✅ New parser: `parse_customer_transactions()` in `ui/parse.py`
3. ✅ New UI component: Transaction list display in Fraud Detection page
4. ✅ Form pre-filling logic based on selected transaction

### What's NOT Changing
- ❌ Existing COBOL programs (CUSTOMER-LOOKUP, FRAUD-CHECK)
- ❌ Existing Python modules (customer_360.py, fraud_detect.py, loan_scoring.py)
- ❌ IPC contracts or data formats
- ❌ Customer 360 page
- ❌ Loan Assessment page

---

## Design Decisions

### Decision 1: Default Selection
**Choice:** Pre-select most recent transaction  
**Rationale:**
- Most recent transaction is usually the one users want to check
- Reduces friction (one less click)
- Can still select others by clicking table row

### Decision 2: Pagination
**Choice:** Show 10 transactions per page  
**Rationale:**
- Balances data visibility with performance
- Typical account has 50-500 transactions (5-50 pages)
- Faster loading than showing all at once

### Decision 3: Manual Override
**Choice:** Allow editing form fields  
**Rationale:**
- Users might want to test "what-if" scenarios
- Backwards compatible with current manual entry workflow
- Flexibility without adding complexity

### Decision 4: Empty State
**Choice:** If no transactions, show manual entry form  
**Rationale:**
- New/dormant accounts have no transactions
- Don't break analysis workflow
- Graceful degradation

---

## Performance Considerations

### Query Performance
```
Operation                    | Est. Time | Notes
--------------------------------------------------
Filter transactions by cust  | <100ms    | Parquet partition pruning
Fetch 10 transactions        | <50ms     | DuckDB in-process
Paginate (load next batch)   | <50ms     | Each batch independent
--------------------------------------------------
TOTAL (display list)         | <150ms    | Acceptable for UX
```

### UI Rendering
```
Component            | Est. Time | Notes
------------------------------------------
Parse response       | ~20ms     | Pipe-delimited parsing
Render table (10 rows) | ~100ms   | Streamlit rendering
Form update          | ~30ms     | Pre-fill form fields
------------------------------------------
TOTAL                | ~150ms    | Smooth user experience
```

**Verdict:** No performance concerns. Can handle 100K customers with <200ms latency.

---

## Assumptions & Dependencies

### Assumptions
1. ✅ `transactions.parquet` exists and has correct schema
2. ✅ DuckDB can efficiently filter 10M rows by customer_id
3. ✅ Parquet date field is YYYY-MM-DD format
4. ✅ All transactions have complete data (no nulls in key fields)
5. ✅ Customer_id uniquely identifies a customer

### Required Data
- `data/transactions.parquet` — must exist with correct schema

### Required Dependencies
- ✅ DuckDB (already in requirements)
- ✅ pyarrow (already in requirements)
- ✅ streamlit (already in requirements)

### New Dependencies
- ❌ None — uses existing packages

---

## Edge Cases & Handling

### Edge Case 1: Customer with 0 Transactions
```
Handling:
├─ Fetch returns count=0
├─ Show message: "No transactions found for this customer"
├─ Display manual entry form as fallback
└─ User can still analyze by entering details manually
```

### Edge Case 2: Customer with 100K+ Transactions
```
Current limit=10 per page handles this:
├─ Show first 10 transactions (load <150ms)
├─ Pagination controls: [← Page 1 of 10000 →]
├─ User can navigate pages or search
└─ No performance issues (each page loads independently)
```

### Edge Case 3: Invalid Customer ID
```
Handling:
├─ python/customer_transactions.py returns count=0
├─ Show "No transactions found"
└─ User proceeds to manual entry
```

### Edge Case 4: Deleted/Updated Transaction
```
Current handling:
├─ User sees transaction in list
├─ Selects it, form pre-fills
├─ User can modify any field before analysis
└─ If data changed, they see it in results
```

---

## Files to Create/Modify

### New Files
1. `python/customer_transactions.py` — Backend script to fetch transactions

### Modified Files
1. `ui/parse.py` — Add `parse_customer_transactions()` function
2. `ui/app.py` — Update `page_fraud_detection()` to show transaction list
3. `docs/FEATURE-FRAUD-DETECTION-ENHANCEMENT.md` — This document

### Documentation Files
1. `docs/FEATURE-FRAUD-DETECTION-IMPLEMENTATION.md` — Step-by-step implementation guide
2. `docs/FEATURE-FRAUD-DETECTION-PROGRESS.md` — Checklist and progress tracker

---

## Testing Strategy

### Unit Tests
```python
# Test 1: Parse customer transactions
raw = "3\nTXN-001|2025-01-15|500.00|5411|Bucharest|POS\n..."
result = parse_customer_transactions(raw)
assert result['count'] == 3
assert result['transactions'][0]['amount'] == 500.0

# Test 2: Handle empty list
raw = "0"
result = parse_customer_transactions(raw)
assert result['count'] == 0
assert result['transactions'] == []
```

### Integration Tests
```python
# Test 1: Fetch and display for real customer
cid = "C-00001"
result = run_script("python/customer_transactions.py", [cid])
assert result['count'] > 0

# Test 2: Pagination
result = run_script("python/customer_transactions.py", [cid, 5, 10])
assert len(result['transactions']) <= 5
```

### Manual/UI Tests
```
Checklist:
[ ] Search for customer
[ ] Click to select customer
[ ] Verify transactions list appears
[ ] Verify most recent transaction is pre-selected
[ ] Click different transaction
[ ] Verify form fields update
[ ] Edit a form field manually
[ ] Click "Analyse"
[ ] Verify fraud analysis runs with correct data
[ ] Test pagination (click Next)
[ ] Test with customer that has 0 transactions
[ ] Test with customer that has 1000+ transactions
```

---

## Success Criteria

### Technical Success
- ✅ `python/customer_transactions.py` returns correct data
- ✅ `parse_customer_transactions()` parses correctly
- ✅ Transaction list displays in UI (< 200ms load time)
- ✅ Form pre-fills with correct transaction data
- ✅ Fraud analysis runs with pre-filled data
- ✅ All tests pass

### UX Success
- ✅ Users understand the flow (no confusion)
- ✅ Selecting a transaction pre-fills form (intuitive)
- ✅ Can still manually enter custom data (backwards compatible)
- ✅ Pagination is smooth and responsive
- ✅ Empty state handled gracefully

### Performance Success
- ✅ Transaction list loads in < 200ms
- ✅ Form pre-fills in < 50ms
- ✅ Pagination loads next page in < 150ms
- ✅ No UI freezing or slowdowns

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Large transaction list (>10K) | Medium | Performance issue | Pagination limits to 10/page |
| Schema mismatch in data | Low | Parser fails | Verify schema before implementation |
| Null values in transactions | Low | Form pre-fill issues | Handle nulls in parser |
| User confusion about selection | Low | Reduced adoption | Clear UI labels + instructions |

**Overall Risk Level:** 🟢 LOW

---

## Dependencies & Blockers

### External Dependencies
- ✅ `data/transactions.parquet` (must exist)
- ✅ DuckDB + pyarrow (already available)

### Internal Dependencies
- ✅ Existing `ui/parse.py` module
- ✅ Existing `ui/runner.py` module
- ✅ Existing `ui/app.py` (to modify)

### Blockers
- ❌ None identified

---

## Next Steps

1. **Approval:** Get sign-off on this design
2. **Implementation:** Create implementation guide (FEATURE-FRAUD-DETECTION-IMPLEMENTATION.md)
3. **Code:** Implement `python/customer_transactions.py`
4. **Code:** Update `ui/parse.py` with parser
5. **Code:** Update `ui/app.py` fraud detection page
6. **Testing:** Run all tests, verify end-to-end
7. **Documentation:** Update user guide if needed

---

**Status:** 🎯 DESIGN COMPLETE — Ready for Implementation Phase

**Last Updated:** 2026-04-15

