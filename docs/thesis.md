# Thesis: Outline, Benchmarks & Roadmap

**Consolidated from:** thesis_outline.md, NEXT-STEPS.md

---

## Thesis Outline

### Title
**"Modernizing COBOL with Big Data Pipelines: A Hybrid Architecture for Legacy Banking Systems"**

### Chapter 1: Introduction
- Hook: COBOL powers 95% of ATM transactions globally; still critical to banking
- Problem: COBOL wasn't designed for big data analytics; modern banking demands real-time insights
- Thesis: Legacy COBOL systems can be extended with Python data pipelines via IPC bridges without rewriting
- Scope: 3 banking modules (Customer 360°, Loan Scoring, Fraud Detection) with 3 IPC mechanisms
- Contributions: Practical framework, empirical benchmarks, IPC analysis, cost-benefit model

### Chapter 2: Background & Literature Review
- COBOL history and current state in banking (1959–present)
- Big data analytics technology stack (Parquet, DuckDB, Python)
- IPC mechanisms in distributed systems (subprocess, files, named pipes)
- Related work: COBOL modernization efforts (AWS Mainframe Modernization, rehosting approaches)
- Research gaps: Comparative analysis of hybrid architectures

### Chapter 3: System Architecture
- 5-layer system design (Entry → COBOL → IPC → Python → Parquet+DuckDB)
- Design principles (separation of concerns, COBOL-native interfaces, stateless Python)
- 3 IPC mechanisms (subprocess, flat files, named pipes) with trade-offs
- Data flow patterns and error handling strategy
- Module specifications (Customer 360°, Loan Assessment, Fraud Detection)

### Chapter 4: Implementation Details
- Phase 1–2: Foundation (utilities, data generation)
- Phase 3–5: Core system (copybooks, Python scripts, COBOL programs)
- Phase 6–7: Operations (build system, benchmarks)
- Phase 8: UI layer (Streamlit analytics dashboard)
- Code snippets, design decisions, gotchas

### Chapter 5: Benchmarking Methodology
- Hypothesis 1: Hybrid approach outperforms COBOL-only for 1M+ record queries
- Hypothesis 2: IPC overhead varies by mechanism (subprocess > files > pipes)
- Hypothesis 3: Certain analytics impossible in pure COBOL become feasible via Python
- Test methodology: controlled environments, reproducible data, statistical analysis
- Metrics: latency (mean, P95, P99), throughput, resource usage

### Chapter 6: Results & Analysis
- Benchmark 1 results: Crossover point at ~1M records (VSAM → Parquet)
- Benchmark 2 results: IPC latency distributions (subprocess: 50–100ms, pipes: 10–20ms)
- Feature comparison: COBOL-only vs hybrid (LOC, execution time, readability)
- Performance characteristics across data scales (10K–10M records)
- Statistical significance and error margins

### Chapter 7: Discussion
- Interpretation of results in context of original hypotheses
- Trade-offs: performance vs complexity, cost vs benefit
- Limitations of the simulation (GnuCOBOL on Linux vs real mainframe)
- Applicability beyond banking (healthcare, insurance, government)
- Recommendations for practitioners considering modernization

### Chapter 8: Conclusion
- Summary of contributions
- Answer to research questions (Can COBOL be extended? At what threshold? Which IPC is best?)
- Impact on legacy system modernization strategies
- Future work (security hardening, cloud deployment, ML integration)
- Final thoughts on pragmatic modernization

### Appendix A: Data Contracts (Byte-Level Specs)
- Customer 360 record (145 bytes)
- Loan Scoring record (51 bytes)
- Fraud Detection record (78 bytes)
- Fixed-width formatting rules

### Appendix B: Code Listings
- Key Python scripts (customer_360.py, loan_scoring.py, fraud_detect.py)
- COBOL programs (CUSTOMER-LOOKUP, LOAN-PROCESS, FRAUD-CHECK)
- Benchmark scripts (bench_ipc_overhead.py, bench_vsam_vs_parquet.py)

### Appendix C: Setup & Reproduction Guide
- System requirements (Python 3.11+, GnuCOBOL 3.2+, DuckDB)
- Data generation (`python3 data/generate_synthetic.py`)
- Build commands (`cd cobol && make all`)
- Running benchmarks
- Reproducing all results

### Appendix D: Configuration Reference
- Environment variables and settings
- DuckDB connection options
- COBOL compiler flags
- IPC timeout and retry logic

### Appendix E: Known Issues & Limitations
- Limitations of simulation vs production mainframe
- Security considerations (not implemented in prototype)
- Scalability limits and recommendations
- Gotchas and workarounds (documented in progress.md)

---

## Benchmark Methodology & Expected Results

### Benchmark 1: VSAM vs. Parquet Query Performance

**Hypothesis:** For datasets exceeding 1 million records, the COBOL + Python + DuckDB/Parquet hybrid outperforms COBOL-only VSAM sequential scanning.

**Test Methodology:**
1. Generate datasets at scales: 10K, 100K, 1M, 5M, 10M customer records
2. For each scale, execute 100 random customer lookups:
   - **Approach A (COBOL-only):** Read VSAM-equivalent indexed file sequentially
   - **Approach B (Hybrid):** Call Python + DuckDB on Parquet
3. Measure wall-clock time per lookup (milliseconds)
4. Record mean, median, P95, P99
5. Plot crossover point on chart

**Expected Results:**
```
Query Time (ms)
     ▲
100  |                    VSAM (pure COBOL)
     |                   /
 50  |                 /
     |    Parquet    /
 20  | (hybrid)    /
     |   -----   /
 10  |         /
     |       /
  5  |     /
     |_____________________________►
       10K  100K  1M   5M   10M
           Dataset Size
     
Crossover point: ~1 Million records
(Parquet faster for larger datasets)
```

**Metrics Captured:**
- Latency: Mean, P50, P95, P99 per scale
- Throughput: Queries/second per approach
- Resource usage: RAM, CPU time
- I/O statistics: Bytes read, partition pruning effectiveness

### Benchmark 2: IPC Overhead Analysis

**Hypothesis:** The IPC bridge introduces measurable but acceptable latency that varies by communication mechanism.

**Test Methodology:**
1. Execute 1,000 identical customer_360.py requests through each IPC option:
   - **Option A:** Subprocess with stdout pipe
   - **Option B:** Flat file exchange (request file → response file)
   - **Option C:** Named pipes (FIFO, Linux only)
2. Measure round-trip time (COBOL invocation → response received)
3. Record distribution: mean, median, P50, P95, P99

**Expected Results:**

| Mechanism | Mean | P95 | P99 | Notes |
|-----------|------|-----|-----|-------|
| **Subprocess** | 50ms | 80ms | 120ms | Process creation overhead visible |
| **Flat File** | 30ms | 50ms | 70ms | Disk I/O effects, more consistent |
| **Named Pipes** | 12ms | 18ms | 25ms | Persistent connection, lowest latency |

**Use Case Recommendations:**
- **Real-time fraud detection** (P99 < 50ms): Use named pipes
- **Interactive customer lookup** (< 500ms acceptable): Subprocess or flat file
- **Batch reporting** (throughput > latency): Any mechanism, flat file optimal

---

## Thesis Writing Roadmap

**Timeline:** 8 weeks from implementation completion

### Phase 8.1: Benchmark Execution (2 weeks)
- Run both benchmarks with 3 data scales (100K, 1M, 5M records minimum)
- Capture output logs and timing data
- Create result tables and charts
- Document any anomalies or system effects

**Checklist:**
- ✅ Generate synthetic data at required scales
- ✅ Run Benchmark 1 (VSAM vs Parquet) 3 times each scale
- ✅ Run Benchmark 2 (IPC overhead) with 1000 requests
- ✅ Collect latency distributions (mean, P50, P95, P99)
- ✅ Create performance charts for thesis

**Deliverable:** `results/` folder with all benchmark output data

### Phase 8.2: Results Documentation (1 week)
- Analyze benchmark results against hypotheses
- Create tables and visualizations for Chapter 6
- Document deviations from expected outcomes
- Prepare summary statistics

**Checklist:**
- ✅ Crossover point identified (at what scale does hybrid become faster?)
- ✅ IPC overhead quantified (latency by mechanism)
- ✅ Performance claims validated or refuted
- ✅ All charts have proper labels and legends
- ✅ Results section draft complete

**Deliverable:** Chapter 6 (Results & Analysis) draft

### Phase 8.3: Thesis Writing (4 weeks)
- Write chapters in order: 1, 2, 3, 4, 5, 7, 8 (results already done)
- Integrate code snippets and examples
- Cross-reference all sections
- Add figures and tables

**Weekly Breakdown:**
- **Week 1:** Chapters 1–2 (Introduction, Background)
- **Week 2:** Chapters 3–4 (Architecture, Implementation)
- **Week 3:** Chapter 5 (Methodology), Appendices A–B
- **Week 4:** Chapters 7–8 (Discussion, Conclusion), polish

**Checklist:**
- ✅ Minimum 30 pages, max 60 pages
- ✅ All sections have citations
- ✅ Code snippets properly formatted and explained
- ✅ Figures have captions and references
- ✅ Bibliography complete

**Deliverable:** Full thesis draft (PDF + DOCX)

### Phase 8.4: Review & Revision (1 week)
- Supervisor review and feedback
- Grammar/spelling check
- Verify all claims are evidence-based
- Revise based on feedback

**Checklist:**
- ✅ Proofread for typos and grammar
- ✅ Verify all section cross-references work
- ✅ Check all citations have full info
- ✅ Ensure conclusions match evidence
- ✅ Format according to university standards

**Deliverable:** Final revised thesis

### Phase 8.5: Submission Preparation (1 week)
- Format according to submission guidelines
- Create index and table of contents
- Prepare abstract and keywords
- Generate final PDF

**Checklist:**
- ✅ Title page correct and complete
- ✅ Abstract written (150–250 words)
- ✅ Keywords identified (5–8 terms)
- ✅ Table of contents auto-generated
- ✅ Page numbering correct
- ✅ All margins and formatting per guidelines

**Deliverable:** Submission-ready PDF

### Phase 8.6: Final Submission
- Submit to university by deadline
- Submit supplementary materials (code, data)
- Archive all work for reference

---

## Validation Checklist

**Before submitting thesis:**

- ✅ All 8 chapters written and polished
- ✅ Benchmarks run and results documented
- ✅ All hypotheses addressed (confirmed or refuted)
- ✅ Code snippets verified for correctness
- ✅ All figures have captions and are referenced
- ✅ Bibliography complete and properly formatted
- ✅ No undefined terms (all jargon explained on first use)
- ✅ All claims have evidence (benchmarks, code, analysis)
- ✅ Conclusion directly answers research questions
- ✅ Appendices complete and usable for reproduction
- ✅ Submitted to advisor for final review
- ✅ Meets university formatting requirements
- ✅ Spell-checked and grammar-reviewed

---

## Windows-Specific Notes

All implementation works on Windows 11 via WSL2. Key considerations:

1. **COBOL Compilation:** Requires WSL2 with GnuCOBOL installed
2. **Named Pipes (FIFO):** Only works on Linux; benchmark skips on Windows
3. **Path Handling:** Use pathlib for cross-platform compatibility
4. **Python Scripts:** Always use `sys.executable` instead of hardcoded python3

For detailed Windows setup, see `WINDOWS-TESTING-REPORT.md`.

---

## Key References

- **architecture.md** — System design & data layer
- **implementation.md** — Phase implementations & features
- **progress.md** — Project status & metrics
- **ui.md** — UI documentation & guides
- **fixes.md** — Bug fixes & improvements
- **CLAUDE.md** — Claude Code session guidance

