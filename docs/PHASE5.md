# Phase 5: COBOL Programs - Implementation Guide

**Status:** ✅ COMPLETE | **Date:** 2026-04-08

## Overview

Phase 5 implements the COBOL orchestration layer that ties together the copybooks (Phase 3) with the Python analytics scripts (Phase 4). Three COBOL programs use the `CALL "SYSTEM"` pattern to invoke Python via subprocess, read responses from files, and display results.

---

## Architecture Pattern

All three COBOL programs follow the same orchestration pattern:

```
1. Accept input parameters (from COMMAND-LINE or hardcoded)
2. Build shell command to invoke Python script
3. CALL "SYSTEM" to execute Python subprocess
4. Wait for subprocess to complete and write response file
5. OPEN INPUT file containing response record
6. READ response into copybook structure (REDEFINES pattern)
7. FUNCTION NUMVAL() converts numeric string fields
8. PERFORM paragraphs to parse and display results
9. Error handling: check RETURN-CODE 99, show safe defaults
10. STOP RUN with appropriate exit code
```

---

## Program 1: CUSTOMER-LOOKUP.cbl

**Purpose:** Retrieve comprehensive customer profile with risk assessment

**Input:**
- Command-line argument: `<customer_id>` (required)

**Invocation:**
```bash
make run-customer-lookup CUSTOMER_ID=C-00001
# Or directly:
./customer-lookup C-00001
```

**Output:**
- Customer name, account balance, transaction count
- Average monthly spending, risk score (0-999)
- Last transaction date

**IPC Flow:**
```
COBOL                           Python
─────────────────────────────────────────────────────
Build command ──────────────→ timeout 5 python3 customer_360.py C-00001
CALL "SYSTEM"                 └─→ Query DuckDB → Output 145-byte record
Read /tmp/cust-response.dat   ←─────────────── Response to stdout
Parse response via REDEFINES     └─→ Write to file
Display results
```

**Key Sections:**
```cobol
PARSE-RESPONSE-RECORD.
    MOVE FUNCTION NUMVAL(CR-ACCT-BALANCE-STR)
        TO CR-ACCT-BALANCE.
    MOVE FUNCTION NUMVAL(CR-TXN-COUNT-STR)
        TO CR-TXN-COUNT.
    ...

DISPLAY-CUSTOMER-RESULTS.
    DISPLAY "Customer ID:    " WS-CUSTOMER-ID.
    DISPLAY "Name:           " CR-CUST-NAME.
    DISPLAY "Account Balance: $" CR-ACCT-BALANCE.
    ...
```

**Error Handling:**
- Return code 01: Customer not found
- Return code 99: Python script error
- Safe defaults: name="UNKNOWN", balance=0, risk_score=0

---

## Program 2: LOAN-PROCESS.cbl

**Purpose:** Assess loan eligibility and compute terms

**Input:**
- Command-line argument: `<customer_id>` (required)
- Hardcoded for now: amount=10000, term=36, purpose=PERS
- TODO: Parse all 4 parameters from COMMAND-LINE

**Invocation:**
```bash
make run-loan-process CUSTOMER_ID=C-00001
# Or directly:
./loan-process C-00001
```

**Output:**
- Credit score (300-850)
- Eligibility decision (Y/N)
- Interest rate (if eligible)
- Max approvable amount (if eligible)
- Rejection reason (if ineligible)

**IPC Flow:**
```
COBOL                              Python
──────────────────────────────────────────────────────────
Build command ────────────────→ timeout 5 python3 loan_scoring.py
CALL "SYSTEM"                    C-00001 10000 36 PERS
Read /tmp/loan-response.dat      └─→ Query DuckDB → Output 51-byte record
Parse via REDEFINES              ←─────────────── Response
Display eligibility result
```

**Key Logic:**
```cobol
IF LR-ELIGIBLE = "Y"
    DISPLAY "Interest Rate:   " LR-INT-RATE "%"
    DISPLAY "Max Loan Amount: $" LR-MAX-AMOUNT
ELSE
    DISPLAY "Rejection Reason:" LR-REJECT-REASON
END-IF.
```

**Error Handling:**
- Safe defaults: score=300, eligible=N, reason="SYSTEM_ERROR"

---

## Program 3: FRAUD-CHECK.cbl

**Purpose:** Assess fraud risk for transaction in real-time

**Input:**
- Command-line argument: `<customer_id>` (required)
- Hardcoded for now: amount=500, mcc=5411, location=Bucharest, timestamp=2025-01-15T14:30:00, channel=POS
- TODO: Parse all 6 parameters from COMMAND-LINE

**Invocation:**
```bash
make run-fraud-check CUSTOMER_ID=C-00001
# Or with parameters:
./fraud-check C-00001 500 5411 Bucharest "2025-01-15T14:30:00" POS
```

**Output:**
- Fraud risk level (LOW, MEDIUM, HIGH)
- Fraud score (0-100)
- Detected anomalies (comma-separated flags)
- Recommendation (APPROVE, REVIEW, DECLINE)

**IPC Flow:**
```
COBOL                           Python
─────────────────────────────────────────────────────────
Build command ──────────────→ timeout 5 python3 fraud_detect.py
CALL "SYSTEM"                 C-00001 500 5411 ...
Read /tmp/fraud-response.dat ←─────────────── 78-byte record
Parse via REDEFINES
Display assessment result
```

**Key Logic:**
```cobol
DISPLAY "Risk Level:      " FR-FRAUD-RISK.
DISPLAY "Fraud Score:     " FR-FRAUD-SCORE " (0-100)".
IF FR-FRAUD-FLAGS NOT = SPACES
    DISPLAY "Detected Flags:  " FR-FRAUD-FLAGS
END-IF.
DISPLAY "Recommendation:  " FR-RECOMMEND.
```

**Recommendation Mapping:**
- LOW (score < 40) → APPROVE
- MEDIUM (score 40-69) → REVIEW
- HIGH (score ≥ 70) → DECLINE

**Error Handling:**
- Safe defaults: risk="UNKNOW", score=50, recommend="REVIEW "

---

## COBOL Patterns Used

### 1. CALL "SYSTEM" Pattern

```cobol
STRING
    "timeout 5 python3 python/customer_360.py "
    DELIMITED BY SIZE
    WS-CUSTOMER-ID DELIMITED BY SPACE
    " > /tmp/cust-response.dat 2>/dev/null"
    DELIMITED BY SIZE
    INTO WS-CMD
END-STRING.

CALL "SYSTEM" USING WS-CMD.
MOVE RETURN-CODE TO WS-CMD-RESULT.
```

**Key Points:**
- `DELIMITED BY SIZE` includes trailing spaces (system() ignores them)
- `timeout 5` enforces 5-second limit (return code 124 on timeout)
- `> /tmp/response.dat` redirects stdout to file
- `2>/dev/null` suppresses stderr (no debug output interferes with IPC)

### 2. REDEFINES + NUMVAL Pattern

```cobol
COPY "CUSTOMER-REC.cpy".

01  WS-RAW-CUST-RESPONSE        PIC X(145).
01  WS-CUST-RESPONSE REDEFINES WS-RAW-CUST-RESPONSE.
    05  CR-CUST-NAME            PIC X(50).
    05  CR-ACCT-BALANCE-STR     PIC X(12).
    ...

MOVE FUNCTION NUMVAL(CR-ACCT-BALANCE-STR)
    TO CR-ACCT-BALANCE.
```

**Why This Works:**
- Read entire 145-byte response as raw string
- REDEFINES overlays named fields on top
- Numeric string fields (PIC X) preserved exactly as Python output
- FUNCTION NUMVAL() converts without loss of precision

### 3. FILE I/O Pattern

```cobol
ENVIRONMENT DIVISION.
INPUT-OUTPUT SECTION.
FILE-CONTROL.
    SELECT RESPONSE-FILE ASSIGN TO "/tmp/cust-response.dat"
        ORGANIZATION IS LINE SEQUENTIAL.

DATA DIVISION.
FILE SECTION.
FD  RESPONSE-FILE.
01  RESPONSE-RECORD PIC X(146).  *> +1 for newline

PROCEDURE DIVISION.
    OPEN INPUT RESPONSE-FILE.
    READ RESPONSE-FILE INTO WS-RAW-CUST-RESPONSE
        AT END
            DISPLAY "ERROR: No response"
            CLOSE RESPONSE-FILE
            STOP RUN
    END-READ.
    CLOSE RESPONSE-FILE.
```

**Key Points:**
- `LINE SEQUENTIAL` organization for text files
- FD record size = Python output + 1 (newline)
- Python: `sys.stdout.write(record + "\n")`
- COBOL read gets exactly one line per READ

### 4. Error Handling Pattern

```cobol
IF FUNCTION NUMVAL(CR-RETURN-CODE-STR) = 1
    DISPLAY "Customer not found"
    MOVE 1 TO RETURN-CODE
    STOP RUN
END-IF.

IF FUNCTION NUMVAL(CR-RETURN-CODE-STR) = 99
    DISPLAY "System error (safe defaults shown)"
    PERFORM SHOW-SAFE-DEFAULTS
    MOVE 1 TO RETURN-CODE
    STOP RUN
END-IF.
```

**Three-Tier Error Handling:**
1. **Python exit code** (checked via RETURN-CODE after CALL)
   - 0 = success (continue)
   - 124 = timeout (show error)
   - other = failure (show error)

2. **Response record return code** (checked in copybook field)
   - 00 = success (display results)
   - 01 = not found (customer_360 only)
   - 99 = error in Python (show safe defaults)

3. **File I/O failure** (checked in AT END clause)
   - Response file missing or empty (show safe defaults)

---

## Compilation

**Using Makefile:**
```bash
cd cobol
make all              # Compile all 3 programs
make clean            # Remove executables
```

**Manual compilation:**
```bash
cobc -x -free -I copybooks -o customer-lookup CUSTOMER-LOOKUP.cbl
cobc -x -free -I copybooks -o loan-process LOAN-PROCESS.cbl
cobc -x -free -I copybooks -o fraud-check FRAUD-CHECK.cbl
```

**Flags:**
- `-x` = produce executable (links with libcob)
- `-free` = free-format COBOL (columns not enforced)
- `-I copybooks` = include path for COPY statements

---

## Testing

### Unit Tests (Per Program)

```bash
# Customer lookup
cd cobol && make all
./customer-lookup C-00001

# Loan assessment
./loan-process C-00001 10000 36 PERS

# Fraud detection
./fraud-check C-00001 500 5411 Bucharest "2025-01-15T14:30:00" POS
```

### Integration Test

```bash
# Prerequisites: Phase 1-4 complete
python3 data/generate_synthetic.py    # Generate data

# Compile
cd cobol && make all

# Run all programs
./customer-lookup C-00001
./loan-process C-00001
./fraud-check C-00001
```

### Expected Output

**Customer Lookup:**
```
========================================
CUSTOMER 360° LOOKUP
========================================
Calling: timeout 5 python3 python/customer_360.py C-00001 > ...

CUSTOMER PROFILE
========================================
Customer ID:     C-00001
Name:            [Customer Name]
Account Balance: $[Amount]
Transactions:    [Count] total
Avg Monthly:     $[Amount]
Risk Score:      [0-999] / 999
Last Transaction:[YYYY-MM-DD]
========================================
```

**Loan Assessment:**
```
========================================
LOAN ELIGIBILITY ASSESSMENT
========================================
...
ASSESSMENT RESULTS
----------------------------------------
Credit Score:    [300-850] (300-850)
Eligible:        Y
Interest Rate:   [X.XX]%
Max Loan Amount: $[Amount]
========================================
```

**Fraud Assessment:**
```
========================================
FRAUD DETECTION ASSESSMENT
========================================
...
FRAUD ASSESSMENT
----------------------------------------
Risk Level:      [LOW/MEDIUM/HIGH]
Fraud Score:     [0-100] (0-100)
Detected Flags:  [FLAG1, FLAG2, ...]
Recommendation:  [APPROVE/REVIEW/DECLINE]
========================================
```

---

## Known Limitations

1. **Parameter Parsing**
   - CUSTOMER-LOOKUP: handles 1 param ✓
   - LOAN-PROCESS: hardcoded params (TODO: parse 4 from COMMAND-LINE)
   - FRAUD-CHECK: hardcoded params (TODO: parse 6 from COMMAND-LINE)

2. **Timeout Implementation**
   - Uses shell `timeout` command (Linux-specific)
   - Works on Ubuntu/Debian (preinstalled)
   - Windows: requires WSL or different approach

3. **File Paths**
   - Hardcoded to `/tmp/` directory (Linux/macOS)
   - Windows: would need `%TEMP%` or environment variable handling

4. **No Connection Pooling**
   - Python creates fresh DuckDB connection per request
   - Acceptable for low-frequency batch operations
   - Not suitable for high-volume transaction processing (>100/sec)

---

## Gotchas & Constraints

1. **Numeric field parsing**
   - Never parse directly without FUNCTION NUMVAL()
   - String "000123456" → numeric 123456 (leading zeros stripped)
   - Don't mix PIC 9 and PIC X without explicit conversion

2. **File I/O line endings**
   - Python: `sys.stdout.write(record + "\n")` adds LF
   - COBOL: `LINE SEQUENTIAL` preserves LF in read
   - FD record size = output bytes + 1

3. **Command-line argument spaces**
   - COBOL pads arguments to field width: "C-00001   "
   - Python must `.strip()` before use
   - This is already handled in Phase 4 scripts

4. **Return codes**
   - `RETURN-CODE` special register updated after `CALL "SYSTEM"`
   - Value = shell exit code (0-255)
   - Check immediately after CALL (before other operations)

---

## Files Created

- ✅ `cobol/CUSTOMER-LOOKUP.cbl` (142 lines)
- ✅ `cobol/LOAN-PROCESS.cbl` (146 lines)
- ✅ `cobol/FRAUD-CHECK.cbl` (156 lines)
- ✅ `cobol/Makefile` (74 lines)

**Total Phase 5:** 518 lines of COBOL + Makefile

---

## Next Phase: Phase 6 (Already Complete)

The Makefile was created in Phase 5 to support Phase 6 (Build System). All compilation targets are now functional.

---

## Next Phase: Phase 7 - Benchmarks

With Phases 1-6 complete, the system is fully functional. Phase 7 implements:
- `benchmarks/bench_vsam_vs_parquet.py` — COBOL-only vs Hybrid comparison
- `benchmarks/bench_ipc_overhead.py` — IPC latency analysis (3 mechanisms)
