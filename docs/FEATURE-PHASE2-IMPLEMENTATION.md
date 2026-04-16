# Phase 2 Implementation: COBOL Validation Program

**Status:** ✅ COMPLETE  
**Date:** 2026-04-15  
**Files Created:** 1 COBOL program  

---

## Overview

Phase 2 implements the COBOL validation program that provides business-rule checking for customer update operations. This is an optional but recommended validation layer that complements Python's field-level validation.

---

## File Created

### `cobol/CUSTOMER-UPDATE.cbl` (~180 lines)

**Purpose:** Validate customer record fields according to COBOL business rules before database update.

**Input:** Fixed-width 207-byte record from file passed as command-line argument:

| Bytes | Field | Format | Content |
|-------|-------|--------|---------|
| 1–7 | Customer ID | PIC X(7) | e.g., "C-00001" |
| 8–57 | Name | PIC X(50) | Left-justified, space-padded |
| 58–157 | Email | PIC X(100) | Left-justified, space-padded |
| 158–207 | City | PIC X(50) | Left-justified, space-padded |

**Output:** 52-byte record to stdout:

| Bytes | Field | Format | Content |
|-------|-------|--------|---------|
| 1–2 | Return Code | PIC XX | "00"=pass, "01"=fail |
| 3–52 | Message | PIC X(50) | Validation result message |

**Invocation:**
```bash
./customer-update /path/to/input.dat
```

---

## Validation Rules

The program performs four validation checks in order:

### 1. Customer ID Format
- **Rule:** Must start with `C-` (first two characters)
- **Failure message:** "Customer ID must start with C-"

### 2. Name Length
- **Rule:** Trimmed length must be ≥ 2 characters
- **Failure message:** "Name must be at least 2 characters"

### 3. Email Format
- **Rule:** Must contain exactly one `@` character
- **Check:** Loops through all 100 bytes searching for `@`
- **Failure message:** "Email must contain @ character"

### 4. City Not Blank
- **Rule:** Trimmed length must be ≥ 1 character
- **Failure message:** "City cannot be blank"

### Success Case
- **Return code:** "00"
- **Message:** "Validation passed"

---

## Implementation Details

### Program Structure

The program follows the standard COBOL pattern:

```
IDENTIFICATION DIVISION
  └─ PROGRAM-ID: CUSTOMER-UPDATE

ENVIRONMENT DIVISION
  └─ INPUT-OUTPUT SECTION
     └─ FILE-CONTROL: Defines INPUT-FILE

DATA DIVISION
  ├─ FILE SECTION: INPUT-RECORD (207 bytes)
  └─ WORKING-STORAGE SECTION
     ├─ Input parameters
     ├─ File operations
     ├─ Parsed fields (WS-CUSTOMER-ID, WS-NAME, WS-EMAIL, WS-CITY)
     ├─ Working variables (trimmed strings, counters, flags)
     └─ Response record (52 bytes)

PROCEDURE DIVISION
  ├─ MAIN-PROCEDURE: Orchestrates flow
  ├─ INITIALIZE-PROGRAM: Accepts command-line argument
  ├─ VALIDATE-ARGUMENTS: Checks argument provided
  ├─ OPEN-INPUT-FILE: Opens the input file
  ├─ READ-INPUT-RECORD: Reads 207-byte record
  ├─ PARSE-INPUT-RECORD: Extracts fields from raw bytes
  ├─ VALIDATE-FIELDS: Performs 4 validation checks
  ├─ FIND-AT-SIGN: Helper to search for @ in email
  └─ WRITE-RESPONSE: Formats and outputs 52-byte response
```

### Key Features

**File I/O:**
- Uses ACCEPT to get input filename from command-line argument
- Opens file with OPEN INPUT, reads one record
- Closes file after reading
- FILE STATUS captures I/O errors

**String Trimming:**
- Uses FUNCTION TRIM() to remove leading/trailing spaces
- Calculates trimmed length for validation

**String Search:**
- PERFORM VARYING loop searches email for `@` character
- Sets flag WS-FOUND-AT when found

**Response Formatting:**
- Builds 52-byte response record
- Code field (2 bytes): "00" or "01"
- Message field (50 bytes): Left-justified, space-padded
- DISPLAY ... NO ADVANCING writes to stdout without newline

---

## Compilation

### GnuCOBOL (Linux/WSL/macOS)

```bash
cd cobol
cobc -x -o customer-update CUSTOMER-UPDATE.cbl
```

**Result:** Executable `cobol/customer-update`

### Windows (Optional)

If GnuCOBOL is installed on Windows:
```bash
cobc -x -o customer-update.exe CUSTOMER-UPDATE.cbl
```

The Python `customer_update.py` script automatically detects if the binary exists and gracefully skips COBOL validation if not found (continuing with Python validation only).

---

## Testing

### Manual Test: Valid Input

```bash
# Create a test input file (207 bytes)
python3 << 'EOF'
import struct
record = b"C-00001" + b" " * 0  # ID
record += b"Jane Doe" + b" " * 42  # Name (50 bytes)
record += b"jane@example.com" + b" " * 84  # Email (100 bytes)
record += b"New York" + b" " * 42  # City (50 bytes)
assert len(record) == 207
with open("/tmp/test-valid.dat", "wb") as f:
    f.write(record)
EOF

# Run validation
./customer-update /tmp/test-valid.dat | od -c

# Expected: "00Validation passed" + 30 spaces (52 bytes total)
```

### Manual Test: Invalid Customer ID

```bash
# Create test file with invalid ID
python3 << 'EOF'
import struct
record = b"INVALID" + b" " * 0  # Invalid ID
record += b"Jane Doe" + b" " * 42
record += b"jane@example.com" + b" " * 84
record += b"New York" + b" " * 42
assert len(record) == 207
with open("/tmp/test-invalid-id.dat", "wb") as f:
    f.write(record)
EOF

# Run validation
./customer-update /tmp/test-invalid-id.dat | od -c

# Expected: "01Customer ID must start with C-" + padding (52 bytes)
```

### Manual Test: Missing Email @

```bash
# Create test file with invalid email
python3 << 'EOF'
record = b"C-00001" + b" " * 0
record += b"Jane Doe" + b" " * 42
record += b"janeatexample.com" + b" " * 83  # No @ sign
record += b"New York" + b" " * 42
with open("/tmp/test-invalid-email.dat", "wb") as f:
    f.write(record)
EOF

./customer-update /tmp/test-invalid-email.dat | od -c

# Expected: "01Email must contain @ character..." (52 bytes)
```

---

## Integration with Python (`python/customer_update.py`)

The COBOL program is invoked by `customer_update.py`:

```python
def call_cobol_validation(customer_id: str, name: str, email: str, city: str):
    # Build 207-byte input record
    record = format_pic_x(customer_id, 7) + \
             format_pic_x(name, 50) + \
             format_pic_x(email, 100) + \
             format_pic_x(city, 50)
    
    # Write to temp .dat file
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.dat') as f:
        f.write(record)
        temp_file = f.name
    
    # Call COBOL
    result = subprocess.run(
        [str(cobol_binary), temp_file],
        capture_output=True,
        timeout=5
    )
    
    # Parse 52-byte response
    response = result.stdout
    return_code = response[0:2].decode('ascii')  # "00" or "01"
    message = response[2:52].decode('ascii').strip()
    
    return return_code, message
```

**Behavior:**
- If COBOL binary not found: logs warning, continues with Python validation only
- If COBOL times out (5s): returns ("99", "COBOL validation timeout")
- If COBOL returns 01: validation fails, returns error to UI
- If COBOL returns 00: proceeds to parquet update

---

## Graceful Degradation

The system is designed to work even if COBOL is not compiled:

1. **Windows without GnuCOBOL:** Binary doesn't exist → Python validation only
2. **Unix without GnuCOBOL:** Same behavior
3. **Linux with GnuCOBOL:** Both Python + COBOL validation layers active

This allows the system to run on any platform with just Python + DuckDB, and optionally add stricter COBOL validation if the binary is available.

---

## Validation Order

The `customer_update.py` script validates in two stages:

**Stage 1 (Python, always):**
```
Customer ID format → Name length → Email @ present → City not blank → Income range
```

**Stage 2 (COBOL, if available):**
```
Customer ID prefix → Name trim length → Email @ search → City trim length
```

This two-tier approach provides defense-in-depth:
- Python catches obvious mistakes early and quickly
- COBOL applies stricter business rules on trimmed values
- System degrades gracefully if COBOL unavailable

---

## Next Steps

- **Phase 3:** Add parse functions to `ui/parse.py` (3 new functions for search, list, update)
- **Phase 4:** Add UI components to `ui/app.py` (search_widget, page_customer_list, sidebar nav update)
- **Phase 5:** Integration testing

---

## Summary

Phase 2 delivers the COBOL validation program that:
- ✅ Reads 207-byte fixed-width input records
- ✅ Validates 4 business rules with descriptive error messages
- ✅ Outputs 52-byte response record (code + message)
- ✅ Gracefully degrades if not compiled
- ✅ Integrates seamlessly with Python validation pipeline

The program follows established COBOL patterns and IPC conventions from the rest of the system.
