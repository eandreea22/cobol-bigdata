# Phase 4 Implementation: UI Components

**Status:** ✅ COMPLETE  
**Date:** 2026-04-15  
**Files Modified:** 1 (ui/app.py)  

---

## Overview

Phase 4 adds three UI components to the Streamlit application:

1. **`search_widget(page_key: str)`** — Reusable customer search widget for all three existing pages
2. **`page_customer_list()`** — New full page for viewing and editing customer records
3. **Sidebar navigation update** — Added "👥 Customer List" to the navigation options
4. **Integration** — Added search widget to Customer 360, Loan Assessment, and Fraud Detection pages

---

## Components Implemented

### 1. `search_widget(page_key: str) -> str`

**Purpose:** Reusable expander widget for searching customers by last name.

**Location in app:** Rendered at the top of each page via `search_widget(page_key)` call

**Features:**
- Collapsible expander: "🔍 Search by Last Name"
- Text input for last name (case-insensitive matching)
- Search button triggers `python/customer_search.py`
- Results displayed in a compact list with:
  - Customer name, ID, and city
  - "Select" button per result
- Selected customer_id stored in `st.session_state[f"sel_cid_{page_key}"]`
- Returns selected customer_id (or empty string if none selected)

**Integration Points:**
- Called in `page_customer_360()` with `page_key="c360"`
- Called in `page_loan_assessment()` with `page_key="loan"`
- Called in `page_fraud_detection()` with `page_key="fraud"`
- Pre-fills the customer ID field in each page's form when a customer is selected

**Code Example:**
```python
# In page_customer_360():
search_cid = search_widget("c360")
default_cid = search_cid if search_cid else "C-00001"

with st.form("f_cust"):
    cid = st.text_input("Customer ID", value=default_cid, ...)
```

**Session State Keys:**
- `sel_cid_c360` — Selected customer ID on Customer 360 page
- `sel_cid_loan` — Selected customer ID on Loan Assessment page
- `sel_cid_fraud` — Selected customer ID on Fraud Detection page

---

### 2. `page_customer_list()`

**Purpose:** Full-page customer management interface with pagination, filtering, inline editing, and save functionality.

**Layout:**
```
┌─────────────────────────────────────────────────┐
│ 👥 Customer List                                 │
│ View and edit customer records                   │
├─────────────────────────────────────────────────┤
│ [Filter by name___________] [Load / Refresh]    │
│                                                  │
│ Showing 100 of 100,000 customers · Page 1 of 1000│
│                                                  │
│ ┌─────────────────────────────────────────────┐│
│ │ Customer ID │ Name │ Email │ City │ ...    ││
│ │ C-00001     │ John │ ...   │ ...  │ ...    ││
│ │ [read-only] │ [edit] [edit] [edit] [edit]  ││
│ └─────────────────────────────────────────────┘│
│                                                  │
│ [← Prev]  Page 1 / 1000  [Next →]              │
│ [💾 Save Changes]                               │
└─────────────────────────────────────────────────┘
```

**Features:**

**Filter & Load:**
- Text input: "Filter by name" (optional substring filter)
- Button: "Load / Refresh" (fetches from backend with pagination)
- Calls `python/customer_list.py` with page, page_size, filter

**Pagination:**
- Shows: "Showing X of Y customers · Page N of M"
- [← Prev] button (disabled if on page 1)
- [Next →] button (disabled if on last page)
- Page counter: "Page N / M"
- Clicking prev/next updates page number and reloads data

**Data Editor Table:**
- Uses `st.data_editor` for inline editing
- Columns: Customer ID, Full Name, Email, City, Street, Balance, Monthly Income
- Read-only columns: Customer ID, Balance
- Editable columns: Full Name, Email, City, Street, Monthly Income
- All cells show current values and accept edits
- Balance auto-updates based on Monthly Income (computed)

**Save Changes:**
- Button: "💾 Save Changes"
- For each edited row:
  - Compares original vs. edited values
  - Skips unchanged rows (optimization)
  - Calls `python/customer_update.py` with new values
  - Shows toast notification per row (✓ success or ✗ error)
- Summary message at end: "X updated successfully", "Y updates failed"
- Auto-reloads data after successful updates

**Session State Keys:**
- `cust_page` — Current page number (defaults to 1)
- `cust_page_size` — Rows per page (defaults to 100)
- `cust_data` — Cached customer rows (None triggers reload)
- `cust_total` — Total matching customer count

---

### 3. Sidebar Navigation Update

**Before:**
```
Options: ["💳  Customer 360", "📊  Loan Assessment", "⚠️  Fraud Detection"]
```

**After:**
```
Options: ["💳  Customer 360", "📊  Loan Assessment", "⚠️  Fraud Detection", "👥  Customer List"]
```

**Routing in `main()`:**
```python
if "Customer 360" in page:
    page_customer_360()
elif "Loan" in page:
    page_loan_assessment()
elif "Fraud" in page:
    page_fraud_detection()
else:
    page_customer_list()
```

---

## Code Changes Summary

### Modified `ui/app.py`

**Imports:**
- Added: `parse_customer_search, parse_customer_list, parse_customer_update` to parse imports
- Added: `Tuple` from typing (for return type hints)

**New Functions:**
- `search_widget(page_key: str) -> str` — ~60 lines
- `page_customer_list()` — ~170 lines

**Existing Functions Modified:**
- `build_sidebar()` — Updated radio options (added "👥  Customer List")
- `page_customer_360()` — Added search_widget call at top
- `page_loan_assessment()` — Added search_widget call at top
- `page_fraud_detection()` — Added search_widget call at top
- `main()` — Updated routing logic (3-way if → 4-way if/elif)

**Total Changes:**
- ~40 lines of imports and updates
- ~230 lines of new code
- Total file size: ~1,100 lines

---

## User Flows

### Flow 1: Search & Navigate

1. User opens Customer 360, Loan Assessment, or Fraud Detection page
2. Expander "🔍 Search by Last Name" appears at top
3. User types last name → clicks "Search"
4. Results displayed (up to 50 customers)
5. User clicks "Select" on a result
6. Customer ID field in the form pre-fills automatically
7. User continues normal flow (submit form, see results)

### Flow 2: Browse & Edit

1. User navigates to "👥 Customer List" from sidebar
2. Page loads first 100 customers (or based on filter)
3. User can:
   - Filter by name and reload
   - Scroll through paginated results
   - Edit any cell (except Customer ID and Balance)
   - Click "Save Changes" to persist edits
4. System shows per-row success/error toasts
5. Data automatically reloads after successful updates

### Flow 3: Pagination

1. On Customer List page with 100,000 customers
2. Default shows first 100 (page 1 of 1,000)
3. User clicks "Next →"
4. Data reloads with page 2 of 1,000
5. [← Prev] becomes enabled
6. User can navigate forward/backward through pages

---

## Error Handling

**Search Widget:**
- RunnerError: Display error message (e.g., "customer_search.py not found")
- ParseError: Display error message (e.g., "Invalid count in results")
- Empty results: Display "No customers found." info message

**Customer List:**
- RunnerError on load: Display error, return early
- ParseError on load: Display error, return early
- RunnerError on save: Toast "✗ ID: error message" per row
- ParseError on save: Toast "✗ ID: error message" per row
- Summary: "X updated, Y failed" messages

---

## Design System Integration

Both new components use existing design tokens and patterns:

- **Colors:** Navy (#0f172a), Cyan (#06b6d4), Slate grays
- **Typography:** Inter font, 12px labels, 1.875rem values
- **Spacing:** 1.25rem sections, 1rem gaps
- **Shadows:** Subtle card shadows (var(--shadow-sm))
- **Border radius:** 12px cards, 8px inputs/buttons
- **Icons:** Emoji-based (🔍, 👥, ✓, ✗)
- **Buttons:** Cyan background, hover lift effect, form_submit_button styling

---

## Performance Considerations

1. **Pagination reduces load:** 100 rows per page instead of all customers
2. **Lazy search:** Results only fetched when user clicks "Search"
3. **Lazy load:** Initial page loads only when user clicks "Load / Refresh"
4. **Session state caching:** Prevents unnecessary reloads on navigation
5. **Incremental updates:** Only changed rows are sent to backend
6. **Spinner feedback:** User sees "Loading…" / "Saving…" during operations

---

## Testing Checklist

- [ ] Search widget:
  - [ ] Expander opens/closes
  - [ ] Search for existing last name (e.g., "Smith")
  - [ ] Search for non-existent last name (shows "No customers found")
  - [ ] Click "Select" on a result → customer ID field pre-fills in form
  - [ ] Test on all three pages (Customer 360, Loan, Fraud)

- [ ] Customer List page:
  - [ ] Page loads with first 100 customers
  - [ ] Filter by name works
  - [ ] Edit a cell (e.g., change email)
  - [ ] Click "Save Changes" → see success toast
  - [ ] Page reloads after successful save
  - [ ] Pagination: click "Next →", see page 2 data
  - [ ] Click "← Prev", see page 1 data again
  - [ ] Disabled states on pagination buttons (first/last pages)
  - [ ] Try invalid edit (e.g., email without @) → see error toast
  - [ ] Multiple edits: edit 3 rows, save, verify all updated

- [ ] Sidebar:
  - [ ] "👥  Customer List" appears in nav
  - [ ] Click it → page_customer_list() renders
  - [ ] Switching between all 4 pages works

---

## Next Steps

- **Phase 5:** Integration testing
  - Test full workflows end-to-end
  - Verify UI handles all error cases gracefully
  - Performance test with full 100K customer dataset
  - Browser compatibility check

---

## Summary

Phase 4 delivers complete UI components for customer search and management:

- ✅ Reusable search widget (integrated into 3 existing pages)
- ✅ Full-featured customer list page (pagination, filtering, editing, saving)
- ✅ Navigation integration (sidebar + routing)
- ✅ Error handling and user feedback (toasts, info/error messages)
- ✅ Session state management (pagination, filters, selection)
- ✅ Design system consistency (colors, typography, spacing, icons)

The implementation is complete and ready for Phase 5 integration testing.
