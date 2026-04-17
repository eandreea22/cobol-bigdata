# Documentation Index & Navigation

This index organizes all documentation by role and task. Start here.

---

## Quick Links by Role

### 👨‍💻 **Developer: Setting up or debugging**
1. **[SETUP.md](SETUP.md)** — Installation steps
2. **[architecture.md](architecture.md)** — System design + IPC contracts
3. **[implementation.md](implementation.md)** — Module reference, APIs, algorithms

### 📊 **Data Analyst: Understanding the data**
1. **[README.md](README.md)** — Project overview
2. **[data.md](data.md)** — Datasets, schemas, query patterns, performance
3. **[implementation.md](implementation.md)** — Algorithm details

### 🎓 **Researcher: Writing the thesis**
1. **[README.md](README.md)** — Research questions
2. **[thesis.md](thesis.md)** — Thesis outline, benchmarks, contributions
3. **[architecture.md](architecture.md)** — Design decisions + trade-offs

### 👤 **User: Using the application**
1. **[README.md](README.md)** — Quick start in 4 commands
2. **[ui.md](ui.md)** — Both UIs explained (Streamlit vs React)
3. **[SETUP.md](SETUP.md)** — Running the systems

---

## Master File List

| File | Purpose | Length |
|------|---------|--------|
| **[README.md](README.md)** | Project overview, 5-layer architecture, quick start | 6KB |
| **[architecture.md](architecture.md)** | Complete system design, IPC contracts, data flows, design decisions | 25KB |
| **[data.md](data.md)** | Data layer reference, schemas, generation, query patterns | 8KB |
| **[implementation.md](implementation.md)** | Developer reference, all modules, algorithms, APIs | 12KB |
| **[thesis.md](thesis.md)** | Thesis guide, research questions, 8-chapter outline, benchmarks | 10KB |
| **[ui.md](ui.md)** | User interface guide (Streamlit + React), both systems | 12KB |
| **[SETUP.md](SETUP.md)** | Installation and running instructions | 4KB |
| **[INSTALLATION_SUMMARY.md](INSTALLATION_SUMMARY.md)** | Quick reference for installation | 2KB |
| **[fixes.md](fixes.md)** | Bug fix history and iterative improvements | 6KB |
| **[progress.md](progress.md)** | Project status (all 21 tasks complete) | 4KB |

---

## Topic-Based Navigation

### Architecture & Design
- **Overall system design**: [README.md](README.md) § "System Architecture"
- **5-layer breakdown**: [architecture.md](architecture.md) § "Layer 1-5"
- **IPC protocol design**: [architecture.md](architecture.md) § "Layer 3: IPC Bridge"
- **Data flow diagrams**: [architecture.md](architecture.md) § "Data Flow Diagrams"

### Data & Queries
- **Data schemas**: [data.md](data.md) § "Dataset Schemas"
- **DuckDB queries**: [data.md](data.md) § "Query Patterns"
- **Hive partitioning**: [data.md](data.md) § "Hive Partitioning"
- **Performance baselines**: [data.md](data.md) § "Performance Baselines"

### Implementation Details
- **COBOL programs**: [implementation.md](implementation.md) § "COBOL Programs"
- **Python analytics**: [implementation.md](implementation.md) § "Python Analytics Scripts"
- **IPC formatters**: [implementation.md](implementation.md) § "IPC Formatter"
- **API reference**: [implementation.md](implementation.md) § "API Reference"
- **Algorithms**: [implementation.md](implementation.md) § "Algorithm Details"

### User Interfaces
- **Streamlit UI**: [ui.md](ui.md) § "Streamlit UI"
- **React UI**: [ui.md](ui.md) § "React UI"
- **SearchWidget pattern**: [ui.md](ui.md) § "SearchWidget"
- **Running both UIs**: [ui.md](ui.md) § "Running Both UIs Simultaneously"

### Research & Thesis
- **Research questions**: [thesis.md](thesis.md) § "Research Questions"
- **8-chapter outline**: [thesis.md](thesis.md) § "8-Chapter Outline"
- **Benchmark methodology**: [thesis.md](thesis.md) § "Benchmark Methodology"
- **Contributions**: [thesis.md](thesis.md) § "Contribution Statement"

### Getting Started
- **Quick start (4 commands)**: [README.md](README.md) § "Quick Start"
- **Installation details**: [SETUP.md](SETUP.md)
- **Running each component**: [implementation.md](implementation.md) § "Running Components"
- **Running both UIs**: [ui.md](ui.md) § "Running Both UIs Simultaneously"

---

## Key Concepts Reference

| Concept | Location |
|---------|----------|
| COBOL programs (4 total) | [architecture.md](architecture.md) § "Layer 1" + [implementation.md](implementation.md) § "COBOL Programs" |
| IPC contracts (3 recordtypes) | [architecture.md](architecture.md) § "Copybooks" |
| Fixed-width encoding | [architecture.md](architecture.md) § "Numeric Encoding" |
| DuckDB queries | [data.md](data.md) § "Query Patterns" |
| Risk scoring algorithm | [implementation.md](implementation.md) § "Risk Score" |
| Credit scoring algorithm | [implementation.md](implementation.md) § "Credit Score" |
| Fraud detection algorithm | [implementation.md](implementation.md) § "Fraud Score" |
| SearchWidget component | [ui.md](ui.md) § "SearchWidget" |
| Streamlit pages | [ui.md](ui.md) § "Streamlit UI" |
| React pages | [ui.md](ui.md) § "React UI" |

---

## Documentation Statistics

- **Total files:** 10 maintained + 4 reference files (QUICKSTART.sh, REACT_MIGRATION.md, etc.)
- **Total length:** ~87 KB of documentation
- **Coverage:** All 5 architecture layers, all algorithms, all UIs, setup & deployment
- **Quality:** Thesis-ready, suitable for academic review

---

## Version History

| Date | Change |
|------|--------|
| 2026-04-17 | Complete rewrite: 7 core docs + INDEX + supporting files |
| 2026-04-15 | Removed 7 obsolete files (CLAUDE.md, SESSION-SUMMARY.md, etc.) |
| 2026-04-10 | Earlier documentation accumulation phase |

---

## How to Update This Index

When adding new documentation:
1. Create the file with clear section headings
2. Add entry to "Master File List" table with length estimate
3. Add relevant sections to "Topic-Based Navigation"
4. Update "Key Concepts Reference" if new concepts introduced
5. Update version history

---

**Last Updated:** 2026-04-17  
**Status:** All 10 files complete and cross-referenced
