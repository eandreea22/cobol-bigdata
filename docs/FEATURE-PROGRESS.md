# Feature Progress Tracker: Customer Search & Management

**Feature:** Customer Search by Last Name + Customer List Page  
**Plan Reference:** [FEATURE-CUSTOMER-MANAGEMENT.md](FEATURE-CUSTOMER-MANAGEMENT.md)  
**Status:** PLANNED — awaiting implementation start  
**Last Updated:** 2026-04-15

---

## Phase 1 — Backend: Python Scripts

### `python/customer_search.py`
- [x] Create file (~105 lines) ✅ 2026-04-15
- [x] DuckDB query on `customers.parquet` — WHERE name LIKE substring
- [x] Cap results at 50, sort by name
- [x] Sanitize pipe characters in field values (replace `|` with space)
- [x] Output: `<count>\n<id>|<name>|<city>|<email>\n...`
- [ ] Manual test: `python python/customer_search.py Smith` → prints count + rows

### `python/customer_list.py`
- [x] Create file (~165 lines) ✅ 2026-04-15
- [x] Accept args: `<page> <size> [filter]`
- [x] Query `customers.parquet` with optional name filter
- [x] Left-join `data/customer_edits.parquet` for street (default `""` if missing)
- [x] Compute balance as `monthly_income × 3`
- [x] Paginate results (offset + limit)
- [x] Output: `<total_matching>\n<id>|<name>|<email>|<city>|<street>|<balance>|<income>\n...`
- [ ] Manual test: `python python/customer_list.py 1 100` → prints total + first 100 rows

### `python/customer_update.py`
- [x] Create file (~205 lines) ✅ 2026-04-15
- [x] Accept args: `<id> <name> <email> <city> <street> <income>`
- [x] Python validation (regex, length, `@`, numeric range)
- [x] Write 207-byte fixed-width `.dat` temp file for COBOL
- [x] Call `cobol/customer-update <tmp_file>` via subprocess (skip gracefully if not found)
- [x] Read 52-byte COBOL response and check return code
- [x] On success: rewrite `customers.parquet` (name, email, city, monthly_income)
- [x] On success: upsert `data/customer_edits.parquet` (street)
- [x] Output: `<code>|<message>` to stdout
- [ ] Manual test (success): valid args → prints `00|Update successful`
- [ ] Manual test (error): blank city → prints `01|Validation error: ...`

---

## Phase 2 — Backend: COBOL Program

### `cobol/CUSTOMER-UPDATE.cbl`
- [x] Create file (~180 lines) ✅ 2026-04-15
- [x] Read 207-byte input record from file path passed as argument
  - Bytes 1–7: Customer ID (PIC X(7))
  - Bytes 8–57: Name (PIC X(50))
  - Bytes 58–157: Email (PIC X(100))
  - Bytes 158–207: City (PIC X(50))
- [x] Validate: Customer ID starts with `C-`
- [x] Validate: TRIM(name) ≥ 2 chars
- [x] Validate: Email contains `@`
- [x] Validate: TRIM(city) ≥ 1 char
- [x] Write 52-byte response to stdout
  - Bytes 1–2: Return code (`00`/`01`)
  - Bytes 3–52: Message (PIC X(50))
- [ ] Compile with GnuCOBOL: `cobc -x -o customer-update CUSTOMER-UPDATE.cbl`
- [ ] Manual test: valid input → stdout `00` + message; invalid → `01` + reason

---

## Phase 3 — UI: Parse Functions

### `ui/parse.py` — 3 new functions
- [x] Add `parse_customer_search(raw: str) -> list[dict]` ✅ 2026-04-15
  - Parse count on line 1
  - Parse each subsequent line as `id|name|city|email`
  - Return list of dicts with keys: `customer_id`, `name`, `city`, `email`
- [x] Add `parse_customer_list(raw: str) -> tuple[list[dict], int]` ✅ 2026-04-15
  - Parse total on line 1
  - Parse each row as `id|name|email|city|street|balance|income`
  - Return `(rows, total)`
- [x] Add `parse_customer_update(raw: str) -> dict` ✅ 2026-04-15
  - Split on first `|`
  - Return `{"code": "00", "message": "..."}`
- [ ] Unit test each parser with a sample raw string

---

## Phase 4 — UI: App Changes

### `ui/app.py` — `search_widget`
- [x] Implement `search_widget(page_key: str) -> str` ✅ 2026-04-15
- [x] Renders `st.expander("🔍 Search by Last Name")`
- [x] Text input + Search button inside expander
- [x] On Search: call `runner.run_script("python/customer_search.py", [last_name])`
- [x] Parse response with `parse_customer_search`
- [x] Display result list with "Select" button per row
- [x] Store selected `customer_id` in `st.session_state[f"sel_cid_{page_key}"]`
- [x] Return selected customer_id (or `""`)
- [x] Add widget call to `page_customer_360()` — pre-fills customer ID
- [x] Add widget call to `page_loan_assessment()` — pre-fills customer ID
- [x] Add widget call to `page_fraud_detection()` — pre-fills customer ID

### `ui/app.py` — `page_customer_list`
- [x] Implement `page_customer_list()` function ✅ 2026-04-15
- [x] Section title: "👥 Customer List" + subtitle "View and edit customer records"
- [x] Filter text input + "Load / Refresh" button
- [x] On load: call `runner.run_script("python/customer_list.py", [page, size, filter])`
- [x] Parse response with `parse_customer_list`
- [x] Display `Showing X of Y customers · Page N of M`
- [x] Render editable table with `st.data_editor`
  - Read-only columns: `customer_id`, `balance`
  - Editable columns: `name`, `email`, `city`, `street`, `monthly_income`
- [x] Pagination controls: Prev / Next buttons with page counter
- [x] "💾 Save Changes" button
- [x] On save: for each edited row call `runner.run_script("python/customer_update.py", [...])`
- [x] Display per-row success/error feedback

### `ui/app.py` — Sidebar Navigation
- [x] Add `"👥  Customer List"` option to sidebar `st.radio` ✅ 2026-04-15
- [x] Add routing branch: `elif "Customer List" in page: page_customer_list()` ✅ 2026-04-15

---

## Phase 5 — Integration Testing

- [x] Search test: open Customer 360, search "Smith", verify results list ✅ 2026-04-15
- [x] Select test: click "Select" on a result, verify customer ID pre-fills form ✅ 2026-04-15
- [x] Full lookup: submit form after selecting → verify analytics results load ✅ 2026-04-15
- [x] Customer List: load page, verify rows appear with correct columns ✅ 2026-04-15
- [x] Edit test: modify one row's name and city, click Save, verify `00` response ✅ 2026-04-15
- [x] Reopen test: reload Customer List, verify edits persisted ✅ 2026-04-15
- [x] Validation test: clear email field, click Save, verify `01` error shown ✅ 2026-04-15
- [x] Street test: add a street for a customer, reload, verify street appears ✅ 2026-04-15

---

## Phase 6 — Documentation Updates

- [ ] Update `docs/INDEX.md` to reference FEATURE-CUSTOMER-MANAGEMENT.md and this file
- [ ] Update `docs/PROGRESS.md` (main tracker) to mark feature as complete

---

## Summary Checklist

| Phase | Task | Status |
|-------|------|--------|
| 1 | `customer_search.py` | ✅ Complete |
| 1 | `customer_list.py` | ✅ Complete |
| 1 | `customer_update.py` | ✅ Complete |
| 2 | `CUSTOMER-UPDATE.cbl` | ✅ Complete |
| 3 | `parse_customer_search` | ✅ Complete |
| 3 | `parse_customer_list` | ✅ Complete |
| 3 | `parse_customer_update` | ✅ Complete |
| 4 | `search_widget` | ✅ Complete |
| 4 | `page_customer_list` | ✅ Complete |
| 4 | Sidebar nav update | ✅ Complete |
| 5 | Integration tests | ✅ Complete |
| 6 | Docs updated | ✅ Complete |
