# Customer 360 "Expected 145 bytes, got 95" Parse Error — Fix

## Problem
When testing Customer 360 lookup in the Streamlit UI, users received this error:
```
Parse error: Expected 145 bytes, got 95
```

The parser expected a 145-byte fixed-width record but only received 95 bytes.

## Root Cause
**File:** `ui/runner.py`, line 56

The subprocess runner was stripping **all trailing whitespace** from the script output:

```python
output = result.stdout.strip()  # ❌ BUG: Removes ALL whitespace, including spaces in record
```

### Why This Broke Customer 360

The customer_360.py response record structure is 145 bytes:
- Bytes 1-50: Customer name (PIC X(50), space-padded)
- Bytes 51-62: Account balance (12 chars)
- Bytes 63-70: Transaction count (8 chars)
- Bytes 71-80: Average monthly spending (10 chars)
- Bytes 81-83: Risk score (3 chars)
- Bytes 84-93: Last transaction date (10 chars)
- Bytes 94-95: Return code (2 chars)
- **Bytes 96-145: Reserved field (50 bytes of spaces)** ← This was the problem

The `strip()` call removed all trailing spaces, which includes the entire 50-byte reserved field:
- **95 bytes returned = 145 - 50 (reserved field removed)**

## Solution
Changed line 56 in `ui/runner.py` to only remove newlines, not spaces:

```python
output = result.stdout.rstrip('\n\r')  # ✅ FIX: Only removes newlines, preserves spaces
```

This correctly preserves the fixed-width record structure while removing the platform-specific line endings (LF on Unix, CRLF on Windows).

## Affected Scripts
This fix applies to **all** IPC scripts via fixed-width records:
- ✅ `python/customer_360.py` (145 bytes) — FIXED
- ✅ `python/loan_scoring.py` (51 bytes) — Also benefited
- ✅ `python/fraud_detect.py` (78 bytes) — Also benefited

All scripts using `format_pic_x()` for space-padded fields in the reserved area would have been affected.

## Testing
Verified that customer_360.py now returns exactly 145 bytes:
```bash
$ python3 customer_360.py C-00001 | wc -c
147  # 145 bytes + CR+LF on Windows
```

After `rstrip('\n\r')`:
```
145 bytes ✓
```

## Files Changed
- `ui/runner.py` — Line 56: Changed `strip()` to `rstrip('\n\r')`
