# Phase 3 Implementation: UI Parse Functions

**Status:** ✅ COMPLETE  
**Date:** 2026-04-15  
**Files Modified:** 1 (ui/parse.py)  

---

## Overview

Phase 3 adds three new parsing functions to the existing `ui/parse.py` module to handle pipe-delimited output from the Phase 1 backend scripts. These parsers follow the same error-handling pattern as the existing parsers for the three analytics scripts.

---

## Functions Added

### 1. `parse_customer_search(raw: str) -> List[Dict[str, str]]`

**Purpose:** Parse pipe-delimited customer search results.

**Input Format:**
```
<count>
<customer_id>|<name>|<city>|<email>
<customer_id>|<name>|<city>|<email>
...
```

**Output:**
Returns a list of dicts with keys: `customer_id`, `name`, `city`, `email`

**Example:**
```python
raw = """2
C-00001|John Smith|New York|john@example.com
C-00002|Jane Smith|Boston|jane@example.com"""

results = parse_customer_search(raw)
# Returns:
# [
#   {'customer_id': 'C-00001', 'name': 'John Smith', 'city': 'New York', 'email': 'john@example.com'},
#   {'customer_id': 'C-00002', 'name': 'Jane Smith', 'city': 'Boston', 'email': 'jane@example.com'}
# ]
```

**Validation:**
- Parses count from first line
- Validates line count matches count + 1
- Ensures each data line has exactly 4 pipe-delimited fields
- Strips whitespace from each field
- Raises `ParseError` if count = 0 (returns empty list)

---

### 2. `parse_customer_list(raw: str) -> Tuple[List[Dict[str, Any]], int]`

**Purpose:** Parse pipe-delimited paginated customer list with total count.

**Input Format:**
```
<total_matching>
<customer_id>|<name>|<email>|<city>|<street>|<balance>|<monthly_income>
<customer_id>|<name>|<email>|<city>|<street>|<balance>|<monthly_income>
...
```

**Output:**
Returns tuple of (list of customer dicts, total_matching)

Each dict has keys: `customer_id`, `name`, `email`, `city`, `street`, `balance`, `monthly_income`

**Example:**
```python
raw = """100
C-00001|John Smith|john@example.com|New York|123 Main St|15000.00|5000.00
C-00002|Jane Doe|jane@example.com|Boston||18000.00|6000.00"""

rows, total = parse_customer_list(raw)
# rows = [
#   {
#     'customer_id': 'C-00001',
#     'name': 'John Smith',
#     'email': 'john@example.com',
#     'city': 'New York',
#     'street': '123 Main St',
#     'balance': 15000.00,
#     'monthly_income': 5000.00
#   },
#   {
#     'customer_id': 'C-00002',
#     'name': 'Jane Doe',
#     'email': 'jane@example.com',
#     'city': 'Boston',
#     'street': '',  # Empty string if no street set
#     'balance': 18000.00,
#     'monthly_income': 6000.00
#   }
# ]
# total = 100
```

**Validation:**
- Parses total from first line
- Validates exactly 7 pipe-delimited fields per row
- Converts balance and monthly_income to floats
- Strips whitespace from all string fields
- Raises `ParseError` on format errors or numeric conversion failures
- Returns ([], 0) if total = 0

---

### 3. `parse_customer_update(raw: str) -> Dict[str, Any]`

**Purpose:** Parse customer update response (pipe-delimited code + message).

**Input Format:**
```
<return_code>|<message>
```

**Output:**
Returns dict with keys: `code`, `message`, `success` (boolean)

**Example (Success):**
```python
raw = "00|Update successful"
result = parse_customer_update(raw)
# Returns: {'code': '00', 'message': 'Update successful', 'success': True}
```

**Example (Validation Error):**
```python
raw = "01|Email must contain @ character"
# Raises ParseError: "Update validation error: Email must contain @ character"
```

**Example (System Error):**
```python
raw = "99|Database connection failed"
# Raises ParseError: "Update system error: Database connection failed"
```

**Validation:**
- Splits on first pipe only (message may contain pipes)
- Validates return code is one of: "00", "01", "99"
- Raises `ParseError` for "01" (validation error) with descriptive message
- Raises `ParseError` for "99" (system error) with descriptive message
- Returns success dict only for "00"

---

## Integration with UI Layer

These parsers are used by the Streamlit app:

```python
# In search widget (to be implemented in Phase 4)
raw = runner.run_script("python/customer_search.py", [last_name])
results = parse_customer_search(raw)
# Display results: name, ID, city with Select button per row

# In customer list page (to be implemented in Phase 4)
raw = runner.run_script("python/customer_list.py", [page, page_size, filter])
rows, total = parse_customer_list(raw)
# Display paginated editable table

# On save changes (to be implemented in Phase 4)
raw = runner.run_script("python/customer_update.py", [id, name, email, city, street, income])
result = parse_customer_update(raw)
# Show success or error message per row
```

---

## Error Handling Pattern

All three parsers follow the same error handling pattern:

1. **Input validation:** Format, field count, data types
2. **Raises `ParseError` with context:** Message includes field/line number when applicable
3. **Graceful empty results:** Returns empty list/dict/tuple for count=0, doesn't raise error

```python
try:
    results = parse_customer_search(raw)
except ParseError as e:
    st.error(f"Parse error: {e}")
```

---

## Code Changes

### Modifications to `ui/parse.py`

**Before:**
- 3 parse functions (customer_360, loan_scoring, fraud_detect)
- Parses fixed-width records
- 150 lines

**After:**
- 6 parse functions (original 3 + search, list, update)
- Parses both fixed-width and pipe-delimited formats
- ~290 lines
- Updated docstring to mention customer management features

---

## Testing

### Unit Test Example: `parse_customer_search`

```python
def test_parse_customer_search_valid():
    raw = """2
C-00001|John Smith|New York|john@example.com
C-00002|Jane Smith|Boston|jane@example.com"""
    
    results = parse_customer_search(raw)
    assert len(results) == 2
    assert results[0]['customer_id'] == 'C-00001'
    assert results[0]['name'] == 'John Smith'

def test_parse_customer_search_no_results():
    raw = "0"
    results = parse_customer_search(raw)
    assert results == []

def test_parse_customer_search_invalid_format():
    raw = """2
C-00001|John Smith|New York|john@example.com|EXTRA"""
    
    with pytest.raises(ParseError) as exc:
        parse_customer_search(raw)
    assert "expected 4 pipe-delimited fields" in str(exc.value)
```

### Unit Test Example: `parse_customer_list`

```python
def test_parse_customer_list_valid():
    raw = """100
C-00001|John Smith|john@example.com|New York|123 Main St|15000.00|5000.00"""
    
    rows, total = parse_customer_list(raw)
    assert total == 100
    assert len(rows) == 1
    assert rows[0]['balance'] == 15000.00
    assert rows[0]['monthly_income'] == 5000.00

def test_parse_customer_list_empty_street():
    raw = """1
C-00001|John Smith|john@example.com|New York||15000.00|5000.00"""
    
    rows, total = parse_customer_list(raw)
    assert rows[0]['street'] == ''
```

### Unit Test Example: `parse_customer_update`

```python
def test_parse_customer_update_success():
    raw = "00|Update successful"
    result = parse_customer_update(raw)
    assert result['success'] is True
    assert result['code'] == '00'
    assert result['message'] == 'Update successful'

def test_parse_customer_update_validation_error():
    raw = "01|Name must be 2-100 characters"
    with pytest.raises(ParseError) as exc:
        parse_customer_update(raw)
    assert "validation error" in str(exc.value)
```

---

## Integration Checklist

- [x] Added 3 new parse functions to `ui/parse.py`
- [x] Functions follow existing error-handling pattern
- [x] Functions have comprehensive docstrings with examples
- [x] Functions validate input format and raise descriptive `ParseError`
- [x] Functions handle edge cases (empty results, optional fields)
- [ ] Unit tests written and passing (for Phase 4 integration testing)

---

## Next Steps

- **Phase 4:** Implement UI components in `ui/app.py`:
  - `search_widget(page_key)` — reusable search form
  - `page_customer_list()` — full customer list page
  - Update sidebar navigation with "👥 Customer List" option

---

## Summary

Phase 3 delivers three parser functions that:
- ✅ Parse pipe-delimited search results (count + rows)
- ✅ Parse paginated list with total count
- ✅ Parse update responses (code + message)
- ✅ Validate format and raise descriptive errors
- ✅ Handle edge cases (empty results, optional fields, numeric conversion)
- ✅ Integrate seamlessly with existing Streamlit UI layer

These parsers are ready for integration with Phase 4 UI components.
