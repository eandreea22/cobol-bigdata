# Phase 1 Implementation: Backend Python Scripts

**Status:** ✅ COMPLETE  
**Date:** 2026-04-15  
**Files Created:** 3 Python scripts  

---

## Overview

Phase 1 implements the three backend Python scripts that power the customer search and management features:

1. **`python/customer_search.py`** — Search customers by last name
2. **`python/customer_list.py`** — Fetch paginated customer list with filtering
3. **`python/customer_update.py`** — Update customer records with COBOL validation

---

## Files Created

### 1. `python/customer_search.py` (~105 lines)

**Purpose:** Search `customers.parquet` by customer last name with case-insensitive matching.

**Input:**
```bash
python python/customer_search.py <last_name>
```

**Example:**
```bash
python python/customer_search.py Smith
```

**Output Format:**
```
<count>
<customer_id>|<name>|<city>|<email>
<customer_id>|<name>|<city>|<email>
...
```

**Features:**
- Case-insensitive substring matching on name field
- Returns up to 50 results, sorted by name
- Sanitizes pipe characters (`|`) in field values (replaces with space)
- Returns count of 0 on error or no results
- Logs errors to stderr, output to stdout only

**Key Functions:**
- `search_customers(last_name: str, max_results: int = 50) -> list[dict]`
- `sanitize(value: str) -> str` — replaces pipes with spaces
- `main()` — argument parsing and output formatting

---

### 2. `python/customer_list.py` (~165 lines)

**Purpose:** Return paginated list of customers with optional name filtering and optional street field from edits.

**Input:**
```bash
python python/customer_list.py <page> <page_size> [name_filter]
```

**Examples:**
```bash
python python/customer_list.py 1 100          # First 100 customers
python python/customer_list.py 2 50 Smith    # Page 2, 50 per page, filter by "Smith"
```

**Output Format:**
```
<total_matching>
<customer_id>|<name>|<email>|<city>|<street>|<balance>|<monthly_income>
<customer_id>|<name>|<email>|<city>|<street>|<balance>|<monthly_income>
...
```

**Features:**
- Pagination: offset/limit based on page number and size
- Optional name filter (substring match, case-insensitive)
- Left-join on `customer_edits.parquet` for street field (defaults to "" if no edit exists)
- Balance computed as `monthly_income × 3` (read-only, matches customer_360 formula)
- All numeric values formatted to 2 decimal places
- Sanitizes pipe characters in all field values
- Logs errors to stderr

**Key Functions:**
- `fetch_customer_list(page: int, page_size: int, name_filter: str = "") -> tuple[list[dict], int]`
- `format_currency(value: float) -> str` — formats to 2 decimal places
- `sanitize(value) -> str`
- `main()` — parses args, validates page >= 1, outputs results

**Data Flow:**
1. Query `customers.parquet` with optional name filter
2. Left-join with `customer_edits.parquet` on customer_id
3. Compute balance, format income
4. Offset and limit by page parameters
5. Output total count + paginated rows

---

### 3. `python/customer_update.py` (~205 lines)

**Purpose:** Update customer record with Python validation + optional COBOL business-rule validation, then persist changes to parquet files.

**Input:**
```bash
python python/customer_update.py <id> <name> <email> <city> <street> <monthly_income>
```

**Example:**
```bash
python python/customer_update.py C-00001 "John Smith" "john@example.com" "New York" "123 Main St" 5000
```

**Output Format:**
```
<return_code>|<message>
```

**Return Codes:**
- `00` = success
- `01` = validation error
- `99` = system error

**Example Outputs:**
```
00|Update successful
01|Name must be 2-100 characters
99|COBOL validation timeout
```

**Features:**
- **Python-level validation** (always runs):
  - Customer ID format: `C-\d{5}` regex
  - Name: 2-100 characters, not blank
  - Email: contains `@`, 5-200 characters
  - City: 1-100 characters, not blank
  - Street: 0-200 characters (optional)
  - Monthly income: numeric, 0 ≤ value ≤ 10,000,000

- **COBOL-level validation** (if compiled binary exists):
  - Checks customer ID prefix (`C-`)
  - Validates name length (≥ 2 chars after trim)
  - Verifies email contains `@`
  - Ensures city is not blank
  - Graceful fallback if COBOL binary not found (logs warning, continues)

- **Database update** (on all validations pass):
  - Rewrites entire `customers.parquet` with updated row
  - Upserts `customer_edits.parquet` with street field
  - Atomic via pandas/DuckDB (write to temp, then replace)

**COBOL IPC Contract:**

**Input file (207 bytes):**
| Bytes | Field | Format |
|-------|-------|--------|
| 1–7 | Customer ID | PIC X(7) |
| 8–57 | Name | PIC X(50) |
| 58–157 | Email | PIC X(100) |
| 158–207 | City | PIC X(50) |

**COBOL Response (52 bytes to stdout):**
| Bytes | Field | Format |
|-------|-------|--------|
| 1–2 | Return code | PIC XX ("00" or "01") |
| 3–52 | Message | PIC X(50) |

**Key Functions:**
- `validate_fields(...) -> tuple[bool, str]` — Python-level validation
- `call_cobol_validation(...) -> tuple[str, str]` — invokes COBOL binary (with graceful fallback)
- `update_parquet(...) -> tuple[bool, str]` — updates both parquet files
- `main()` — orchestrates all steps

**Update Flow:**
1. Parse and validate arguments
2. Python field validation (returns 01 on fail)
3. Call COBOL if available (returns 01/99 on fail)
4. Rewrite `customers.parquet` (name, email, city, monthly_income)
5. Upsert `customer_edits.parquet` (street)
6. Output `00|Update successful`

---

## Testing

### Manual Tests

**Test customer_search.py:**
```bash
# Search for "Smith"
python python/customer_search.py Smith

# Expected: count line + up to 50 matching rows with format id|name|city|email

# Test with no results
python python/customer_search.py ZZZZZZ

# Expected: 0
```

**Test customer_list.py:**
```bash
# First page, 100 rows per page
python python/customer_list.py 1 100

# Expected: total count + 100 rows (or fewer if < 100 customers total)

# With filter
python python/customer_list.py 1 50 Smith

# Expected: total matching + up to 50 Smith rows
```

**Test customer_update.py:**
```bash
# Valid update
python python/customer_update.py C-00001 "Jane Doe" "jane@example.com" "Boston" "456 Oak Ave" 4500

# Expected: 00|Update successful

# Invalid email (no @)
python python/customer_update.py C-00001 "Jane Doe" "janeatexample.com" "Boston" "456 Oak Ave" 4500

# Expected: 01|Email must be valid (contains @) and 5-200 characters

# Invalid ID format
python python/customer_update.py INVALID "Jane Doe" "jane@example.com" "Boston" "456 Oak Ave" 4500

# Expected: 01|Customer ID must match format C-XXXXX
```

---

## Integration Notes

### For UI Layer (`ui/app.py`)

The three scripts integrate with the UI via `runner.py` and parse functions:

```python
# Search widget
raw = runner.run_script("python/customer_search.py", [last_name])
results = parse_customer_search(raw)  # Returns list[dict]

# Customer list page
raw = runner.run_script("python/customer_list.py", [page, page_size, filter])
rows, total = parse_customer_list(raw)  # Returns (list[dict], int)

# Save changes
raw = runner.run_script("python/customer_update.py", [id, name, email, city, street, income])
result = parse_customer_update(raw)  # Returns dict with code/message
```

### Data Files

- **`data/customers.parquet`** — Source of truth for customer demographics
- **`data/customer_edits.parquet`** — Auto-created on first save, stores street field and future extensions

---

## Implementation Details

### Error Handling

- **Python validation fails:** Return `01|error message` immediately
- **COBOL binary not found:** Log warning, skip COBOL check, continue to parquet update
- **COBOL timeout (5s):** Return `99|COBOL validation timeout`
- **Parquet update fails:** Return `99|Database error message`

### Field Sanitization

All pipe characters (`|`) in output fields are replaced with spaces to preserve the pipe delimiter:
```python
def sanitize(value: str) -> str:
    return value.replace('|', ' ').strip() if value else ""
```

### Currency Formatting

Balance and income formatted to exactly 2 decimal places:
```python
def format_currency(value: float) -> str:
    return f"{float(value):.2f}"
```

---

## Next Steps

- **Phase 2:** Implement `cobol/CUSTOMER-UPDATE.cbl` — COBOL validation program
- **Phase 3:** Add parse functions to `ui/parse.py`
- **Phase 4:** Add UI components to `ui/app.py` (search_widget, page_customer_list)

---

## Summary

Phase 1 delivers the three core backend scripts that handle:
- ✅ Customer search by name
- ✅ Paginated customer listing with filtering
- ✅ Customer updates with multi-tier validation

All scripts are production-ready, follow the existing IPC patterns, and integrate cleanly with the Streamlit UI layer.
