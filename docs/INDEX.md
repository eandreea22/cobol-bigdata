# Documentation Index

All documentation has been consolidated in the `docs/` folder.

## Quick Navigation

### 🎯 For Claude Code Sessions
Start here when continuing work:
- **[CLAUDE.md](CLAUDE.md)** — Build commands, architecture, IPC contracts
- **[PROGRESS.md](PROGRESS.md)** — Current implementation status tracker
- **[README-IMPLEMENTATION.md](README-IMPLEMENTATION.md)** — Quick start guide

### 📚 Technical Reference
- **[project-data.md](project-data.md)** — Full technical specification (authoritative source, 140+ pages)
- **[data-architecture.md](data-architecture.md)** — Parquet + DuckDB design, data generation flow, relationships, queries

### 🎉 Completed Features

#### Customer Search & Management Feature — COMPLETE ✅

- **[FEATURE-COMPLETION-SUMMARY.md](FEATURE-COMPLETION-SUMMARY.md)** — Executive summary & sign-off (production-ready for demo)

#### Fraud Detection Enhancement — COMPLETE ✅

- **[FRAUD-DETECTION-QUICK-START.md](FRAUD-DETECTION-QUICK-START.md)** — User guide: How to use the new transaction list feature
- **[FEATURE-FRAUD-DETECTION-IMPLEMENTATION-COMPLETE.md](FEATURE-FRAUD-DETECTION-IMPLEMENTATION-COMPLETE.md)** — ✅ Implementation complete: transaction list, pagination, form pre-filling, all tests passing
- **[FEATURE-FRAUD-DETECTION-ENHANCEMENT.md](FEATURE-FRAUD-DETECTION-ENHANCEMENT.md)** — Design analysis: transaction-based analysis, UX/technical assessment
- **[FEATURE-FRAUD-DETECTION-IMPLEMENTATION.md](FEATURE-FRAUD-DETECTION-IMPLEMENTATION.md)** — Step-by-step implementation guide (reference)
- **[FEATURE-FRAUD-DETECTION-PROGRESS.md](FEATURE-FRAUD-DETECTION-PROGRESS.md)** — Task checklist and progress tracker (reference)

**Implementation Documentation (5 phases):**
- **[FEATURE-CUSTOMER-MANAGEMENT.md](FEATURE-CUSTOMER-MANAGEMENT.md)** — Implementation plan: customer search by last name + customer list page + COBOL update pipeline
- **[FEATURE-PROGRESS.md](FEATURE-PROGRESS.md)** — Checklist tracker for the customer management feature
- **[FEATURE-PHASE1-IMPLEMENTATION.md](FEATURE-PHASE1-IMPLEMENTATION.md)** — ✅ Phase 1: Backend Python scripts (`customer_search.py`, `customer_list.py`, `customer_update.py`)
- **[FEATURE-PHASE2-IMPLEMENTATION.md](FEATURE-PHASE2-IMPLEMENTATION.md)** — ✅ Phase 2: COBOL validation program (`CUSTOMER-UPDATE.cbl`)
- **[FEATURE-PHASE3-IMPLEMENTATION.md](FEATURE-PHASE3-IMPLEMENTATION.md)** — ✅ Phase 3: UI parse functions (3 new parsers in `ui/parse.py`)
- **[FEATURE-PHASE4-IMPLEMENTATION.md](FEATURE-PHASE4-IMPLEMENTATION.md)** — ✅ Phase 4: UI components (search widget, customer list page, sidebar integration)
- **[FEATURE-PHASE4-BUGFIX.md](FEATURE-PHASE4-BUGFIX.md)** — ✅ Bug fix: Customer List page auto-loads all customers by default
- **[FEATURE-SEARCH-FIX.md](FEATURE-SEARCH-FIX.md)** — Bug fix v1: Search by last name simplified
- **[FEATURE-SEARCH-FIX-V2.md](FEATURE-SEARCH-FIX-V2.md)** — Bug fix v2: Complete rewrite - simplified session state, arrow button
- **[CUSTOMER360-FINAL-FIX.md](CUSTOMER360-FINAL-FIX.md)** — ✅ Final fix: Dark text visibility, working select button, search-only workflow, auto-loading
- **[PAGES-CUSTOMER-SELECTION.md](PAGES-CUSTOMER-SELECTION.md)** — ✅ Loan Assessment & Fraud Detection: Read-only customer selection, form for details entry
- **[FEATURE-PHASE5-INTEGRATION-TESTING.md](FEATURE-PHASE5-INTEGRATION-TESTING.md)** — ✅ Phase 5: Integration testing & verification (33 test cases, all passing)

### 📋 Implementation Details — All Complete ✅

- ✅ Phase 1a: `python/utils/ipc_formatter.py` — IPC formatting utilities
- ✅ Phase 1b: `python/utils/parquet_reader.py` — DuckDB query helpers
- ✅ Phase 2: `data/generate_synthetic.py` — Synthetic data generation (100K customers, 10M transactions)
- ✅ Phase 3: COBOL copybooks (CUSTOMER-REC, LOAN-REC, FRAUD-REC) — Fixed-width record definitions
- ✅ Phase 4: Python analytics scripts (customer_360, loan_scoring, fraud_detect, report_aggregator) — Scoring & risk assessment
- ✅ Phase 5: COBOL programs (CUSTOMER-LOOKUP, LOAN-PROCESS, FRAUD-CHECK) — IPC orchestration
- ✅ Phase 6: Build system (Makefile) — Compilation & testing targets
- ✅ Phase 7: Benchmarks (VSAM vs Parquet, IPC overhead) — Performance validation
- ✅ Phase 8: Streamlit UI (customer_360, loan_scoring, fraud_detect) — Web interface for system testing

## Data Contracts

### Customer 360 (145 bytes)
```
Bytes 1-50:    Name (PIC X(50))
Bytes 51-62:   Balance (PIC 9(10)V99)
Bytes 63-70:   Transaction count (PIC 9(8))
Bytes 71-80:   Avg monthly (PIC 9(8)V99)
Bytes 81-83:   Risk score (PIC 9(3))
Bytes 84-93:   Last transaction date (YYYY-MM-DD)
Bytes 94-95:   Return code (00/01/99)
Bytes 96-145:  Reserved (50 bytes)
```

### Loan (51 bytes)
```
Bytes 1-3:     Credit score (PIC 9(3))
Byte 4:        Eligible (PIC X(1))
Bytes 5-9:     Interest rate (PIC 9V9(4))
Bytes 10-19:   Max amount (PIC 9(8)V99)
Bytes 20-49:   Rejection reason (PIC X(30))
Bytes 50-51:   Return code (PIC 99)
```

### Fraud (78 bytes)
```
Bytes 1-6:     Fraud risk (PIC X(6))
Bytes 7-9:     Fraud score (PIC 9(3))
Bytes 10-69:   Fraud flags (PIC X(60))
Bytes 70-76:   Recommendation (PIC X(7))
Bytes 77-78:   Return code (PIC 99)
```

### 🎨 Phase 8: UI Layer — Web Interface Documentation ✅

- **[UI-REDESIGN.md](UI-REDESIGN.md)** — Full v2 redesign spec: design tokens, component library, sidebar nav, layout diagrams, CSS override map



Interactive Streamlit UI for testing the hybrid COBOL-Python system. Three tabs expose core analytics:

- **[ui_design.md](ui_design.md)** — Technology choice, architecture, tab specifications, component design
- **[development_plan.md](development_plan.md)** — Implementation strategy, 9-step roadmap, integration points, verification checklist
- **[progress_tracker.md](progress_tracker.md)** — Task status, blockers, detailed notes, timeline
- **[ui_guide.md](ui_guide.md)** — User guide (setup, running, using three tabs, troubleshooting, FAQ)

**To run the UI:**
```bash
pip install streamlit
streamlit run ui/app.py
```

## Key Files

| File | Purpose |
|------|---------|
| docs/CLAUDE.md | Claude Code session guidance |
| docs/PROGRESS.md | Task status & verification checklist |
| docs/README-IMPLEMENTATION.md | Implementation guide & quick start |
| docs/project-data.md | Full technical spec (source of truth) |
| docs/INDEX.md | This file (navigation) |
| ~/.claude/plans/peaceful-puzzling-scott.md | Implementation plan (internal) |

## Phase Dependencies

```
Phase 1 (Utilities)
    ↓
Phase 2 (Data Generation) ← Must run before testing Python scripts
    ↓
Phase 3 (COBOL Copybooks) ← Needed by Phase 5
    ↓
Phase 4 (Python Scripts)
    ↓
Phase 5 (COBOL Programs) ← Depends on Phase 3 copybooks
    ↓
Phase 6 (Build System)
    ↓
Phase 7 (Benchmarks)
    ↓
Phase 8 (UI Layer) ← Streamlit web interface (optional, for testing)
```

## Running the System

```bash
# 1. Generate synthetic data (one-time setup, required before running analytics)
python3 data/generate_synthetic.py

# 2. Verify Python output byte lengths
python3 python/customer_360.py C-00001 | wc -c    # Should be 146 (145+\n)
python3 python/loan_scoring.py C-00001 10000 36 PERS | wc -c  # Should be 52
python3 python/fraud_detect.py C-00001 500 5411 Bucharest "2025-01-15T14:30:00" POS | wc -c  # Should be 79

# 3. Compile and test COBOL programs
cd cobol && make all
./customer-lookup C-00001
./loan-process C-00001 10000 36 PERS
./fraud-check C-00001 500 5411 Bucharest "2025-01-15T14:30:00" POS

# 4. Run benchmarks (Linux/WSL required for named pipes)
python3 benchmarks/bench_ipc_overhead.py
python3 benchmarks/bench_vsam_vs_parquet.py
```

## Key Design Principles

1. **Byte-Perfect IPC** — Python output must match COBOL expectations exactly
2. **Stateless Python** — Each script invocation is independent
3. **3-Tier Error Handling** — Exit codes → timeouts → safe defaults
4. **DuckDB In-Memory** — No database server needed
5. **REDEFINES Pattern** — Raw bytes + named field overlay for COBOL

---

**Last Updated:** 2026-04-08  
**Status:** ✅ ALL 8 PHASES COMPLETE — System fully implemented, tested on Windows, and ready for thesis presentation with interactive UI
