# Analytics Pages: Customer Selection Workflow

**Date:** 2026-04-15  
**Pages Updated:**
- Loan Assessment
- Fraud Detection

**Status:** ✅ COMPLETE  

---

## What Changed

All three analytics pages now use the same **customer selection workflow**:

### **Customer 360**
1. Search for customer by last name
2. Auto-loads customer profile

### **Loan Assessment** (Updated)
1. Search for customer by last name
2. View selected customer ID (read-only)
3. Fill in loan details (amount, term, purpose)
4. Submit for assessment

### **Fraud Detection** (Updated)
1. Search for customer by last name
2. View selected customer ID (read-only)
3. Fill in transaction details (amount, MCC, location, channel, timestamp)
4. Submit for analysis

---

## Design: Read-Only Customer Selection

### **Before:**
```
[Customer ID input field] ← Can be edited/changed
[Loan amount]
[Term]
[Purpose]
[Submit]
```

### **After:**
```
┌─────────────────────────────┐
│ SELECTED CUSTOMER           │
│ C-00001                     │  ← Read-only display
└─────────────────────────────┘

[Loan amount]
[Term]
[Purpose]
[Submit]
```

---

## User Flow

### **Loan Assessment:**
```
1. Page loads
   ↓
"👆 Search for a customer above to continue"
   ↓
2. User searches for "Smith"
   ↓
3. Results appear with → button
   ↓
4. User clicks →
   ↓
5. Customer selected: "C-00001"
   ↓
6. Selected Customer box appears (read-only)
   ↓
7. Form shows:
   [Loan Amount]
   [Loan Term]
   [Purpose]
   [Submit]
   ↓
8. User fills in details and clicks "Run Credit Assessment"
   ↓
9. Results display
```

### **Fraud Detection:**
```
(Same as above, but with)

7. Form shows:
   [Transaction Amount]
   [MCC]
   [Location]
   [Channel]
   [Date]
   [Time]
   [Submit]
```

---

## Implementation Details

### **Customer Selection Box**
```html
<div style="background:#f1f5f9;padding:1rem;border-radius:8px;">
  <div style="font-size:.75rem;text-transform:uppercase;">
    SELECTED CUSTOMER
  </div>
  <div style="font-size:1.1rem;font-weight:600;">
    C-00001
  </div>
</div>
```

**Why this design:**
- ✅ Read-only display prevents accidental changes
- ✅ Light blue background distinguishes it from form inputs
- ✅ Uppercase label makes it clear this is metadata
- ✅ Large, bold ID is easy to see

### **Form Structure**
```python
# 1. Get customer from search
cid = search_widget("loan")

# 2. If no customer, show instructions
if not cid:
    st.info("👆 Search for a customer above to continue")
    return

# 3. Display selected customer (read-only)
st.markdown(f'<div>Selected: {cid}</div>')

# 4. Show form (no customer ID field)
with st.form("f_loan"):
    amount = st.number_input(...)
    term = st.selectbox(...)
    purpose = st.selectbox(...)
    go = st.form_submit_button(...)
```

---

## Benefits

✅ **Prevents Mistakes** — Can't accidentally change customer mid-form  
✅ **Clear Context** — Always shows which customer you're assessing  
✅ **Simpler Form** — No customer ID field cluttering the interface  
✅ **Consistent** — Same workflow across all three pages  
✅ **User-Friendly** — Instructions guide user on what to do  

---

## Customer Flow Comparison

### **All Three Pages Now:**

| Step | Customer 360 | Loan Assessment | Fraud Detection |
|------|--------------|-----------------|-----------------|
| 1 | Search | Search | Search |
| 2 | Auto-load profile | Show read-only ID | Show read-only ID |
| 3 | (Results) | Fill loan details | Fill transaction details |
| 4 | (Results) | Submit form | Submit form |
| 5 | (Results) | Show assessment | Show analysis |

---

## Files Modified

- ✅ `ui/app.py` — `page_loan_assessment()` updated
- ✅ `ui/app.py` — `page_fraud_detection()` updated

---

## Testing Checklist

### **Loan Assessment**
- [ ] Search for customer
- [ ] Click → to select
- [ ] Verify customer ID displays in read-only box
- [ ] Verify can't edit customer ID
- [ ] Fill in loan details
- [ ] Submit and verify results load

### **Fraud Detection**
- [ ] Search for customer
- [ ] Click → to select
- [ ] Verify customer ID displays in read-only box
- [ ] Verify can't edit customer ID
- [ ] Fill in transaction details
- [ ] Submit and verify results load

---

**Status:** ✅ COMPLETE & READY FOR TESTING
