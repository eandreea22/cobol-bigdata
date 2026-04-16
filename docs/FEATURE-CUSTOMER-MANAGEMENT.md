# Feature Plan: Customer Search & Management

**Status:** PLANNED — not yet implemented  
**Date:** 2026-04-15  
**Scope:** Search by last name (3 pages) + Customer List page (view + edit)

---

## 1. Overview

Two capabilities are being added to the existing Streamlit UI:

| Feature | Description |
|---------|-------------|
| **Search by Last Name** | Available on Customer 360, Loan Assessment, Fraud Detection — find a customer by surname, select from results, continue normal flow |
| **Customer List page** | New dedicated page — tabular view of all customers, inline editing, save via COBOL + Python pipeline |

Neither feature modifies the existing analytics scripts (`customer_360.py`, `loan_scoring.py`, `fraud_detect.py`).

---

## 2. Architecture

### 2.1 New Python Scripts (backend)

| Script | Args | Output | Purpose |
|--------|------|--------|---------|
| `python/customer_search.py` | `<last_name>` | Pipe-delimited lines | Search customers.parquet by surname |
| `python/customer_list.py` | `<page> <size> [filter]` | Pipe-delimited lines | Paginated customer list, merged with edits |
| `python/customer_update.py` | `<id> <name> <email> <city> <street> <income>` | `<code>\|<message>` | Validate via COBOL → update parquet |

### 2.2 New COBOL Program

| File | Purpose |
|------|---------|
| `cobol/CUSTOMER-UPDATE.cbl` | Business-rule validation (ID format, name length, email @, city not empty) |

Follows the exact same IPC pattern as existing COBOL programs: reads a `.dat` input file, writes a fixed-width response record to stdout.

### 2.3 UI Changes (`ui/app.py`)

- Add `search_widget(page_key)` — reusable expander used in 3 existing pages
- Add `page_customer_list()` — new full page
- Add **"👥 Customer List"** entry to the sidebar navigation radio

### 2.4 Parser Changes (`ui/parse.py`)

Three new functions:

| Function | Input | Returns |
|----------|-------|---------|
| `parse_customer_search(raw)` | Pipe-delimited string | `list[dict]` |
| `parse_customer_list(raw)` | Pipe-delimited string | `(list[dict], total: int)` |
| `parse_customer_update(raw)` | `"<code>\|<message>"` | `dict` |

---

## 3. Data Design

### 3.1 Existing data (unchanged)

`data/customers.parquet` — columns: `customer_id`, `name`, `dob`, `city`, `account_open_date`, `credit_tier`, `email`, `monthly_income`

### 3.2 New supplemental file

`data/customer_edits.parquet` — created on first save, stores fields not present in `customers.parquet`:

| Column | Type | Notes |
|--------|------|-------|
| `customer_id` | string | Primary key |
| `street` | string | Street address (new field) |

When `customer_list.py` loads data, it left-joins `customer_edits.parquet` onto `customers.parquet` on `customer_id`. Missing streets default to `""`.

### 3.3 Balance field

Balance is not stored. It is computed as `monthly_income × 3` (same formula as `customer_360.py`). It is displayed read-only in the Customer List. Editing `monthly_income` implicitly affects the displayed balance.

### 3.4 Editable fields in Customer List

| Field | Source | Editable |
|-------|--------|----------|
| Customer ID | `customers.parquet` | No (read-only) |
| Full Name | `customers.parquet` | Yes |
| Email | `customers.parquet` | Yes |
| City | `customers.parquet` | Yes |
| Street | `customer_edits.parquet` | Yes |
| Balance | Computed (`monthly_income × 3`) | No (display only) |
| Monthly Income | `customers.parquet` | Yes |

---

## 4. IPC Contracts

### 4.1 `customer_search.py` output

```
<count>
<customer_id>|<name>|<city>|<email>
<customer_id>|<name>|<city>|<email>
...
```

- Max 50 results
- Pipe (`|`) is the delimiter; pipes within field values are replaced with spaces
- Count = 0 means no results

### 4.2 `customer_list.py` output

```
<total_matching>
<customer_id>|<name>|<email>|<city>|<street>|<balance>|<monthly_income>
...
```

- `total_matching` = total rows across all pages (for pagination display)
- `balance` and `monthly_income` are formatted to 2 decimal places

### 4.3 `customer_update.py` output

```
<return_code>|<message>
```

- `return_code`: `00` = success, `01` = validation error, `99` = system error
- `message`: human-readable (max 100 chars)

### 4.4 COBOL input/output (`CUSTOMER-UPDATE.cbl`)

**Input file** (207-byte fixed-width record, written by `customer_update.py`):

| Bytes | Field | PIC |
|-------|-------|-----|
| 1–7 | Customer ID | X(7) |
| 8–57 | Name | X(50) |
| 58–157 | Email | X(100) |
| 158–207 | City | X(50) |

**Output** (52-byte record, written to stdout):

| Bytes | Field | PIC |
|-------|-------|-----|
| 1–2 | Return code (`00`/`01`) | XX |
| 3–52 | Message | X(50) |

---

## 5. Update Flow (Step by Step)

```
User edits row in Customer List
           ↓
Clicks "Save Changes" button
           ↓
UI calls runner.run_script("python/customer_update.py", [...args])
           ↓
customer_update.py:
  1. Python field validation (format, lengths, types)
  2. Write 207-byte input record to temp .dat file
  3. Call cobol/customer-update <tmp_file> via subprocess
     ├─ COBOL not found → skip, continue with Python validation only
     └─ COBOL found → read 52-byte response, check return code
  4. If all validations pass:
     a. Rewrite customers.parquet (name, email, city, monthly_income)
     b. Upsert customer_edits.parquet (street)
  5. Print return_code|message to stdout
           ↓
UI reads return code → shows success / error per row
```

---

## 6. Search Flow (Step by Step)

```
User opens "Search by Last Name" expander (on any of 3 pages)
           ↓
Types last name → clicks "Search"
           ↓
UI calls runner.run_script("python/customer_search.py", [last_name])
           ↓
customer_search.py:
  DuckDB query on customers.parquet:
    WHERE lower(name) LIKE lower('% ' || ?)   -- "First LastName"
       OR lower(name) = lower(?)               -- exact match
  Returns up to 50 results
           ↓
UI shows result list (name, ID, city) with a "Select" button per row
           ↓
User clicks "Select" → customer_id stored in st.session_state
           ↓
Customer ID field pre-filled → user submits form → normal analytics flow
```

---

## 7. UI Components

### 7.1 `search_widget(page_key: str) -> str`

Reusable function. Renders a collapsible `st.expander("🔍 Search by Last Name")`.

Inside:
- `st.text_input` for last name
- `st.button("Search")`
- If results: list with `st.button("Select")` per row
- Selected customer_id stored in `st.session_state[f"sel_cid_{page_key}"]`
- Returns the stored customer_id (or `""` if nothing selected)

Used by:
- `page_customer_360()` — pre-fills customer ID in form
- `page_loan_assessment()` — pre-fills customer ID in form
- `page_fraud_detection()` — pre-fills customer ID in form

### 7.2 `page_customer_list()`

Layout:

```
[icon] Customer List
       View and edit customer records

┌─── Filter & Controls ───────────────────────────────┐
│  [Filter by name___________]  [Load / Refresh]      │
└──────────────────────────────────────────────────────┘

Showing 100 of 100,000 customers  ·  Page 1 of 1000

┌── Editable Table (st.data_editor) ──────────────────┐
│ Customer ID │ Full Name │ Email │ City │ Street │ Balance │ Income │
│ C-00001     │ ...       │ ...   │ ...  │ ...    │  ...    │  ...   │
│ [read-only] │ [edit]    │ [edit]│ [ed] │ [edit] │ [RO]    │ [edit] │
└──────────────────────────────────────────────────────┘

         [💾 Save Changes]
```

Pagination controls: `[← Prev]  Page 1 / 1000  [Next →]`

---

## 8. Validation Rules

### Python-level (always run)

| Field | Rule |
|-------|------|
| customer_id | Matches `C-\d{5}` regex |
| name | 2–100 characters, not blank |
| email | Contains `@`, 5–200 characters |
| city | 1–100 characters, not blank |
| street | 0–200 characters (optional) |
| monthly_income | Number, 0 ≤ value ≤ 10,000,000 |

### COBOL-level (if binary compiled)

| Check | COBOL rule |
|-------|-----------|
| Customer ID prefix | Must start with `C-` |
| Name length | TRIM(name) ≥ 2 chars |
| Email `@` present | Loop through email bytes, find `@` |
| City not blank | TRIM(city) ≥ 1 char |

---

## 9. Files to Create / Modify

| File | Action | Notes |
|------|--------|-------|
| `python/customer_search.py` | **Create** | ~60 lines |
| `python/customer_list.py` | **Create** | ~90 lines |
| `python/customer_update.py` | **Create** | ~130 lines |
| `cobol/CUSTOMER-UPDATE.cbl` | **Create** | ~100 lines |
| `ui/parse.py` | **Modify** | Add 3 new parse functions |
| `ui/app.py` | **Modify** | Add search_widget, page_customer_list, update sidebar nav |
| `data/customer_edits.parquet` | **Auto-created** | First time a street is saved |
| `docs/FEATURE-CUSTOMER-MANAGEMENT.md` | **Create** | This document |
| `docs/FEATURE-PROGRESS.md` | **Create** | Checklist tracker |

**Files NOT modified:**
- `python/customer_360.py`
- `python/loan_scoring.py`
- `python/fraud_detect.py`
- `python/utils/parquet_reader.py`
- `python/utils/ipc_formatter.py`
- `ui/runner.py`
- `data/customers.parquet` *(structure unchanged; rows updated in place)*
- Any COBOL file other than the new one

---

## 10. Assumptions & Constraints

1. **Balance is computed, not stored.** `monthly_income × 3` is the formula used by `customer_360.py`. Editing `monthly_income` in the Customer List changes the displayed balance accordingly. No separate balance field is added to `customers.parquet`.

2. **COBOL binary may not exist on Windows.** `customer_update.py` checks for the compiled binary. If not found, it skips COBOL validation and proceeds with Python validation only. No error is raised — a warning is logged to stderr.

3. **Parquet rewrite on update.** Updating `customers.parquet` requires reading the full 100K-row file, changing one row, and writing it back. This takes ~1–2 seconds. Acceptable for a single-user demo.

4. **Max 50 search results.** Large last names (e.g. "Smith") may match thousands. The script caps at 50 and returns them sorted by name.

5. **Pagination defaults.** Customer List defaults to 100 rows per page. Users can filter by name to narrow results.

6. **Session state for search selection.** Streamlit session state stores the selected customer ID. Refreshing the page clears the selection.

7. **Street is optional.** Customers without a saved street show an empty cell in the list.

---

## 11. Risk & Mitigations

| Risk | Mitigation |
|------|-----------|
| Parquet rewrite corrupts data | Write to temp file first, then atomic rename (or use pandas which handles this) |
| COBOL not compiled on Windows | Graceful fallback to Python-only validation |
| 100K customers too slow to load | Pagination (100/page), plus server-side filter |
| Concurrent edits overwrite each other | Single-user demo — not applicable |
| Pipes in customer names break delimiter | `sanitize()` replaces `\|` with space before output |

