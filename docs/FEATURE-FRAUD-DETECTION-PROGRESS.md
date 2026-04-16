# Fraud Detection Enhancement: Progress Tracker

**Feature:** Fraud Detection with Transaction-Based Analysis  
**Start Date:** 2026-04-15  
**Target Completion:** 2026-04-17  
**Status:** 🎯 DESIGN PHASE COMPLETE → Ready for Implementation

---

## Phase Overview

```
Design Phase (COMPLETE)
    ↓
Phase 1: Backend (python script + parser)
    ↓
Phase 2: UI Implementation (Streamlit updates)
    ↓
Phase 3: Testing & Verification
    ↓
DONE ✅
```

---

## Phase 1: Backend Implementation

### 1.1 Verify Data Schema ⬜
- [ ] Run schema verification script
- [ ] Confirm transactions.parquet has all required columns
- [ ] Document actual column names and data types
- [ ] Note any differences from expected schema

**Blockers:** None  
**Assigned to:** —  
**Timeline:** 15 minutes  

---

### 1.2 Create python/customer_transactions.py ⬜
- [ ] Create new file: `python/customer_transactions.py`
- [ ] Implement query logic (filter by customer_id, sort DESC)
- [ ] Implement pagination (limit/offset parameters)
- [ ] Add error handling (non-existent customer, query errors)
- [ ] Test with sample customer (C-00001)
- [ ] Verify output format (pipe-delimited)
- [ ] Test pagination (offset parameter)
- [ ] Test empty results (non-existent customer)

**Blockers:** Schema verification  
**Assigned to:** —  
**Timeline:** 1 hour  

**Testing Notes:**
```bash
# Should return transaction data
python3 python/customer_transactions.py C-00001 10 0

# Should return count=0
python3 python/customer_transactions.py C-99999 10 0

# Should handle pagination
python3 python/customer_transactions.py C-00001 5 10
```

---

### 1.3 Add parse_customer_transactions() to ui/parse.py ⬜
- [ ] Add new function: `parse_customer_transactions(raw)`
- [ ] Parse pipe-delimited format
- [ ] Convert amount to float
- [ ] Return dict with 'count' and 'transactions' keys
- [ ] Handle edge cases (empty list, invalid format)
- [ ] Add error handling with clear messages
- [ ] Add unit tests for parser

**Blockers:** python/customer_transactions.py working  
**Assigned to:** —  
**Timeline:** 30 minutes  

**Unit Tests to Add:**
```python
test_parse_customer_transactions_valid()       # Happy path
test_parse_customer_transactions_empty()       # count=0
test_parse_customer_transactions_invalid()     # Malformed input
test_parse_customer_transactions_single()      # One transaction
```

---

### Phase 1 Verification Checklist
- [ ] `python/customer_transactions.py` returns correct data format
- [ ] Script handles edge cases (0 transactions, non-existent customer)
- [ ] Parser function works with all test cases
- [ ] All unit tests pass (`pytest ui/parse.py`)
- [ ] Code is clean and documented

**Phase 1 Status:** ⬜ TODO  
**Phase 1 Completion:** —

---

## Phase 2: UI Implementation

### 2.1 Add Helper Function to ui/app.py ⬜
- [ ] Add `fetch_customer_transactions()` function
- [ ] Call python/customer_transactions.py via run_script()
- [ ] Parse response with parse_customer_transactions()
- [ ] Handle errors gracefully
- [ ] Return dict or empty dict on error

**Blockers:** Phase 1 complete  
**Assigned to:** —  
**Timeline:** 15 minutes  

---

### 2.2 Update page_fraud_detection() Function ⬜
- [ ] Add session state management for pagination (`fraud_txn_page`)
- [ ] Add session state for selected transaction index
- [ ] Fetch transactions after customer selection
- [ ] Display "Loading transactions..." spinner
- [ ] Handle zero transactions case (show warning)
- [ ] Create transaction list display (table-like)
- [ ] Implement pagination (Previous/Next buttons)
- [ ] Make transaction rows clickable (select one)
- [ ] Store selected transaction in session state
- [ ] Pre-fill form from selected transaction
- [ ] Allow manual form field editing
- [ ] Run fraud analysis with form data

**Blockers:** 2.1 complete  
**Assigned to:** —  
**Timeline:** 2+ hours  

**Key Implementation Details:**
```python
# Pagination state
st.session_state.fraud_txn_page     # Current page (1-indexed)
st.session_state.fraud_selected_txn_idx  # Index of selected transaction (0-indexed)
st.session_state.fraud_selected_transaction  # Dict with transaction data

# Form pre-filling
default_amount = selected_txn.get('amount', 0)
default_mcc = selected_txn.get('mcc', '')
# ... etc for other fields
```

---

### 2.3 Verify UI Rendering ⬜
- [ ] No syntax errors in modified page_fraud_detection()
- [ ] Streamlit doesn't crash when page loads
- [ ] Search widget still works
- [ ] Customer selection still works
- [ ] Transaction list displays (if customer has transactions)
- [ ] Pagination controls visible and functional
- [ ] Form fields show pre-filled values
- [ ] "Analyse for Fraud" button runs analysis

**Blockers:** 2.2 complete  
**Assigned to:** —  
**Timeline:** 30 minutes  

---

### Phase 2 Verification Checklist
- [ ] No import errors
- [ ] No undefined variables
- [ ] All st.session_state variables initialized
- [ ] Helper function integrated correctly
- [ ] Transaction list displays for test customer
- [ ] Pagination works
- [ ] Form pre-filling works
- [ ] Fraud analysis runs successfully

**Phase 2 Status:** ⬜ TODO  
**Phase 2 Completion:** —

---

## Phase 3: Testing & Verification

### 3.1 Unit Tests ⬜
- [ ] Run `pytest ui/parse.py` for parser tests
- [ ] All parser tests pass (parse_customer_transactions)
- [ ] Add integration test for fetch_customer_transactions()
- [ ] Run all tests: `pytest python/ tests/`
- [ ] Zero test failures

**Blockers:** Phase 1 & 2 complete  
**Assigned to:** —  
**Timeline:** 30 minutes  

**Test Commands:**
```bash
pytest ui/parse.py::test_parse_customer_transactions_valid -v
pytest ui/parse.py::test_parse_customer_transactions_empty -v
pytest ui/parse.py::test_parse_customer_transactions_invalid -v
pytest python/ -v
pytest tests/ -v
```

---

### 3.2 Manual UI Testing ⬜
- [ ] Open Fraud Detection page in browser
- [ ] Search for customer "Smith"
- [ ] Select "John Smith — C-00001"
- [ ] Verify customer name displays
- [ ] Verify "Recent Transactions" section appears
- [ ] Verify table shows 10 transactions
- [ ] Verify columns: Date, Amount, MCC, Location, Channel
- [ ] Verify most recent transaction is pre-selected
- [ ] Click different transaction
- [ ] Verify form fields update with new transaction data
- [ ] Verify all 5 fields pre-fill correctly:
  - [ ] Amount matches
  - [ ] MCC matches
  - [ ] Location matches
  - [ ] Channel matches
  - [ ] Date/time matches
- [ ] Manually edit a form field (e.g., change amount)
- [ ] Click "Analyse for Fraud"
- [ ] Verify fraud analysis runs
- [ ] Verify results display (risk level, score, recommendation)

**Blockers:** Phase 2 complete  
**Assigned to:** —  
**Timeline:** 1 hour  

**Test Cases:**
```
Test 1: Search and select
Test 2: Transaction list appears
Test 3: Pagination next page
Test 4: Pagination previous page
Test 5: Transaction selection
Test 6: Form pre-filling
Test 7: Manual editing
Test 8: Fraud analysis
Test 9: Empty transactions (edge case)
Test 10: Large transaction list (1000+)
```

---

### 3.3 Edge Case Testing ⬜
- [ ] Customer with 0 transactions
  - [ ] Warning message appears
  - [ ] Manual form still appears
  - [ ] Can analyze manually
- [ ] Customer with 100 transactions
  - [ ] Pagination shows correct count
  - [ ] All pages load correctly
- [ ] Customer with 1000+ transactions
  - [ ] Performance acceptable (< 200ms per page)
  - [ ] Pagination works smoothly
- [ ] Transaction with special characters in location
  - [ ] Doesn't break form or display
- [ ] Very long location name
  - [ ] Truncates properly in table
  - [ ] Shows full name in form
- [ ] Missing transaction fields
  - [ ] Gracefully handles null/missing data

**Blockers:** 3.2 complete  
**Assigned to:** —  
**Timeline:** 45 minutes  

---

### 3.4 Performance Testing ⬜
- [ ] Transaction list loads in < 200ms
- [ ] Pagination loads in < 150ms
- [ ] Form pre-filling in < 50ms
- [ ] No UI freezing or lag
- [ ] Browser console has no errors
- [ ] No memory leaks (test multiple interactions)

**Blockers:** 3.2 complete  
**Assigned to:** —  
**Timeline:** 30 minutes  

**Performance Benchmarks:**
```
Acceptable: < 200ms for transaction list load
Good:       < 100ms
Excellent:  < 50ms

Acceptable: < 150ms for pagination
Good:       < 100ms
Excellent:  < 75ms
```

---

### 3.5 Cross-Browser Testing ⬜
- [ ] Chrome/Edge: Works correctly
- [ ] Firefox: Works correctly
- [ ] Safari (if available): Works correctly
- [ ] Mobile browser (if applicable): Works correctly

**Blockers:** 3.2 complete  
**Assigned to:** —  
**Timeline:** 15 minutes  

---

### Phase 3 Verification Checklist
- [ ] All unit tests pass
- [ ] All manual UI tests pass
- [ ] All edge cases handled
- [ ] Performance acceptable
- [ ] Cross-browser compatibility verified
- [ ] No console errors
- [ ] No broken links or missing features

**Phase 3 Status:** ⬜ TODO  
**Phase 3 Completion:** —

---

## Known Issues & Blockers

### Current Blockers
| Blocker | Status | Resolution | ETA |
|---------|--------|-----------|-----|
| (None identified) | ✅ Clear | — | — |

### Known Issues
| Issue | Severity | Status | Notes |
|-------|----------|--------|-------|
| (None identified) | — | ✅ Resolved | — |

### Potential Issues to Watch
1. **Large transaction lists** — Pagination should handle efficiently
2. **Null/missing data** — Parser should handle gracefully
3. **Special characters** — Pipe-delimited parsing might fail on `|` in location names

---

## Timeline & Milestones

```
2026-04-15  Design Phase Complete ✅
2026-04-16  Phase 1: Backend (4-6 hours)
2026-04-16  Phase 2: UI (3-4 hours)
2026-04-17  Phase 3: Testing (1-2 hours)
2026-04-17  COMPLETE ✅
```

---

## Dependencies

### External Dependencies
- ✅ data/transactions.parquet (exists)
- ✅ DuckDB (already installed)
- ✅ pyarrow (already installed)
- ✅ Streamlit (already installed)

### Internal Dependencies
- ✅ ui/runner.py (already exists)
- ✅ ui/parse.py (exists, will be updated)
- ✅ ui/app.py (exists, will be updated)
- ✅ python/fraud_detect.py (no changes needed)

### No Breaking Changes
- ❌ No changes to COBOL programs
- ❌ No changes to IPC contracts
- ❌ No changes to existing Python modules
- ❌ No changes to Customer 360 page
- ❌ No changes to Loan Assessment page

---

## Success Criteria

### Feature is successful when:
1. ✅ Users can see actual transactions for a customer
2. ✅ Users can select a transaction by clicking it
3. ✅ Form automatically pre-fills with selected transaction data
4. ✅ Users can still manually edit form fields
5. ✅ Fraud analysis runs with correct transaction data
6. ✅ UI is responsive (no lag or freezing)
7. ✅ Handles edge cases (0 transactions, 1000+ transactions)
8. ✅ All tests pass

---

## Team Notes

### For Implementation Phase
1. Start with schema verification (might uncover surprises)
2. Test python/customer_transactions.py independently before UI
3. Add detailed comments in page_fraud_detection() (complex function)
4. Use Streamlit columns() for table-like display (more flexible than st.dataframe)
5. Test pagination carefully (common source of bugs)

### Common Pitfalls to Avoid
- ❌ Using st.dataframe (slow and not clickable)
- ❌ Storing transaction list in st.session_state (large data)
- ❌ Not initializing session state variables (causes bugs on first run)
- ❌ Converting strings to floats incorrectly (might lose precision)
- ❌ Not handling empty transactions list (crashes UI)

### Testing Tips
- Use customer "C-00001" (should have many transactions)
- Test pagination thoroughly (often has off-by-one errors)
- Check browser console for JS/render errors
- Watch for memory leaks (rapid selections)
- Test on real data, not synthetic data (might have unexpected patterns)

---

## Sign-Off

- [ ] Design approved by stakeholder
- [ ] Architecture approved by stakeholder
- [ ] Ready to begin Phase 1 implementation

**Design Reviewed By:** —  
**Date:** —  

---

## Change Log

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2026-04-15 | 1.0 | Design Phase | Initial design document created |
| — | — | — | — |

---

**Last Updated:** 2026-04-15  
**Next Review:** 2026-04-16

