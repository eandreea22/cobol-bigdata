# Implementation Guide

This document points to key files for understanding and continuing the implementation.

## 📋 Key Documents

### For Claude Code (AI Assistant)
- **`CLAUDE.md`** — Comprehensive guidance for Claude Code sessions
  - Build & run commands
  - Architecture overview
  - IPC contract details (byte-precise)
  - Technology stack
  - Error handling strategy

### For Understanding the Project
- **`docs/project-data.md`** — Full technical specification (authoritative source)
  - Executive summary
  - Business context
  - Complete module specifications
  - Data layer design
  - Benchmarking methodology
  - 11 major sections with implementation details

### For Progress Tracking
- **`PROGRESS.md`** — Current implementation status
  - Phase-by-phase breakdown
  - Task completion checklist
  - Data format contracts (byte-by-byte)
  - Critical implementation notes
  - Verification steps

### For Implementation Planning
- **Implementation Plan** (internal to Claude Code)
  - Located at: `~/.claude/plans/peaceful-puzzling-scott.md`
  - 7-phase sequence with detailed specs
  - Per-file function signatures
  - GnuCOBOL syntax notes
  - Gotchas and constraints

---

## 🚀 Quick Start

### Current Status
- ✅ Phase 1: Foundation utilities (ipc_formatter, parquet_reader)
- ✅ Phase 2: Synthetic data generation
- ✅ Phase 3: COBOL copybooks
- ✅ Phase 4: Python analytics scripts (customer_360, loan_scoring, fraud_detect, report_aggregator)
- ✅ Phase 5: COBOL programs (CUSTOMER-LOOKUP, LOAN-PROCESS, FRAUD-CHECK)
- ✅ Phase 6: Build system (Makefile)
- ✅ Phase 7: Benchmarks (VSAM vs Parquet, IPC overhead)
- 🔄 Phase 8: Thesis writeup (benchmark execution, chapter writing)

### Generate Data First
```bash
cd /c/Users/Andreea/Desktop/cobol-bigdata
python3 data/generate_synthetic.py
# Produces: customers.parquet, loans.parquet, transactions/, fraud_labels.parquet
```

### Verify Python Utilities
```bash
python3 -c "from python.utils.ipc_formatter import format_pic_x, format_pic_9; \
            assert format_pic_9(1234.56, 10, 2) == '000000123456'; \
            print('✓ IPC formatter working')"
```

---

## 📊 Data Contracts (Critical)

All Python output must be byte-perfect fixed-width records. Use `ipc_formatter.py` functions:

| Module | Output Size | Key Fields |
|--------|-------------|-----------|
| customer_360.py | 145 bytes | name(50) + balance(12) + txn_count(8) + avg(10) + risk(3) + date(10) + rc(2) |
| loan_scoring.py | 51 bytes | score(3) + eligible(1) + rate(5) + max_amount(10) + reason(30) + rc(2) |
| fraud_detect.py | 78 bytes | risk(6) + score(3) + flags(60) + recommend(7) + rc(2) |

---

## 🔧 Build Commands

Once COBOL programs are written:
```bash
cd cobol
make all                                    # Compile all 3 programs
make run-customer-lookup CUSTOMER_ID=C-00001
make run-loan-process CUSTOMER_ID=C-00001 AMOUNT=10000 TERM=36 PURPOSE=PERS
make run-fraud-check CUSTOMER_ID=C-00001 AMOUNT=500 MCC=5411 LOCATION=Bucharest TIMESTAMP="2025-01-15T14:30:00" CHANNEL=POS
make benchmark                              # Run performance benchmarks
make clean                                  # Remove executables & temp files
```

---

## 📁 Directory Structure

```
cobol-bigdata/
├── CLAUDE.md                    ← Claude Code guidance
├── PROGRESS.md                  ← Current task status
├── README-IMPLEMENTATION.md     ← This file
├── docs/
│   ├── README.md               ← Original thesis prompt
│   ├── project-data.md         ← Full technical spec (authoritative)
│   ├── architecture.mermaid    ← Diagram stub
│   └── thesis_outline.md       ← Outline stub
├── cobol/
│   ├── CUSTOMER-LOOKUP.cbl     ✅ DONE (142 lines)
│   ├── LOAN-PROCESS.cbl        ✅ DONE (146 lines)
│   ├── FRAUD-CHECK.cbl         ✅ DONE (156 lines)
│   ├── Makefile                ✅ DONE (74 lines)
│   └── copybooks/
│       ├── CUSTOMER-REC.cpy    ✅ DONE (36 lines, 145 bytes)
│       ├── LOAN-REC.cpy        ✅ DONE (32 lines, 51 bytes)
│       └── FRAUD-REC.cpy       ✅ DONE (28 lines, 78 bytes)
├── python/
│   ├── customer_360.py         ✅ DONE (163 lines)
│   ├── loan_scoring.py         ✅ DONE (201 lines)
│   ├── fraud_detect.py         ✅ DONE (163 lines)
│   ├── report_aggregator.py    ✅ DONE (225 lines)
│   └── utils/
│       ├── ipc_formatter.py    ✅ DONE (67 lines)
│       └── parquet_reader.py   ✅ DONE (227 lines)
├── data/
│   ├── generate_synthetic.py   ✅ DONE (225 lines)
│   ├── customers.parquet       (generated: 100K records)
│   ├── loans.parquet           (generated: 500K records)
│   ├── transactions/           (generated: 10M records, 365 date partitions)
│   └── fraud_labels.parquet    (generated: 50K records)
└── benchmarks/
    ├── bench_vsam_vs_parquet.py   ✅ DONE (196 lines)
    └── bench_ipc_overhead.py      ✅ DONE (263 lines)
```

---

## 🎯 Next Steps: Phase 8 — Thesis Completion

All implementation phases are complete. The next steps are:

1. **Execute Benchmarks** (Linux/WSL required)
   - Run `python3 benchmarks/bench_vsam_vs_parquet.py` to validate crossover point
   - Run `python3 benchmarks/bench_ipc_overhead.py` to measure IPC latency
   - Capture output for thesis results tables

2. **Fill Thesis Outline** (`docs/thesis_outline.md`)
   - Chapter structure: Introduction, Background, Design, Implementation, Results, Discussion, Conclusion
   - Appendices: Data contracts, code listings, setup guide

3. **Write NEXT-STEPS.md**
   - Benchmark execution guide
   - Results interpretation
   - Thesis writing roadmap linking implementation to chapters

4. **Validate End-to-End**
   - Run `python3 data/generate_synthetic.py` to create data
   - Compile COBOL: `cd cobol && make all`
   - Test each program: `./customer-lookup`, `./loan-process`, `./fraud-check`
   - Verify byte-length outputs with `wc -c`

See `docs/NEXT-STEPS.md` for detailed post-implementation roadmap.

---

## 💡 Implementation Philosophy

- **Byte-perfect IPC**: Python output must match COBOL expectations exactly (use `ipc_formatter.py`)
- **Stateless Python**: Each script invocation is independent (no shared state)
- **3-tier error handling**: Python exit code → COBOL timeout → safe defaults
- **DuckDB in-memory**: No database server needed, fast columnar queries
- **Hive partitioning**: Transaction table partitioned by date for efficient pruning

---

## 📞 Support

If working with Claude Code:
- Reference `CLAUDE.md` for context
- Check `PROGRESS.md` for current status
- Refer to implementation plan: `~/.claude/plans/peaceful-puzzling-scott.md`
- Consult `docs/project-data.md` for detailed specs

For local development:
- Install: `pip install duckdb pyarrow pandas numpy faker`
- GnuCOBOL: `apt install gnucobol` (Ubuntu/Debian)
