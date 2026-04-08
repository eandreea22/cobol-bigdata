# 🧠 Claude Code Prompt — COBOL + Python Big Data Project

## Context

You are an expert software engineer with strong experience in:

* COBOL (GnuCOBOL)
* Python (data engineering & analytics)
* DuckDB, Parquet
* System architecture and IPC (inter-process communication)

Your task is to implement a **complete hybrid COBOL + Python system** based on the attached technical documentation.

---

## 📄 Source of Truth

Use the uploaded document as the **single source of truth**.

You must:

* Carefully read and understand ALL sections
* Follow the architecture, modules, and data contracts exactly
* Respect COBOL ↔ Python integration constraints

---

## 🎯 Objective

Generate a **fully working implementation** of the described system:

A hybrid architecture where:

* COBOL handles business logic and orchestration
* Python handles data processing, analytics, and scoring
* Communication is done via an IPC bridge using fixed-width records

---

## 🏗️ Project Structure

The project structure is **already created** (as described in the document).

Rules:

* Follow the existing structure strictly
* DO NOT restructure unless absolutely necessary
* If you modify anything, you MUST explain why

---

## ⚙️ Implementation Requirements

### 1. COBOL Layer

Implement the following programs:

* `CUSTOMER-LOOKUP.cbl`
* `LOAN-PROCESS.cbl`
* `FRAUD-CHECK.cbl`

Requirements:

* Use WORKING-STORAGE exactly as defined
* Respect PIC clauses strictly
* Implement IPC calls using `CALL "SYSTEM"`
* Handle:

  * success responses
  * error codes
  * timeouts (simulate if needed)
* Include fallback logic (safe defaults)

---

### 2. Python Layer

Implement the following scripts:

* `customer_360.py`
* `loan_scoring.py`
* `fraud_detect.py`

Requirements:

* Use Python 3.11+
* Use DuckDB to query Parquet files
* Perform all analytics described in the document
* Keep scripts **stateless**
* Input via command-line arguments
* Output via **fixed-width record to stdout**

---

### 3. IPC Contract (CRITICAL)

You MUST:

* Match COBOL copybook formats EXACTLY
* Respect:

  * field lengths
  * alignment (left/right)
  * zero-padding
* Ensure output is byte-perfect

Implement utility:

* `ipc_formatter.py` with:

  * `format_pic_x`
  * `format_pic_9`

---

### 4. Data Layer

Implement:

* `generate_synthetic.py`

Requirements:

* Generate realistic datasets:

  * customers.parquet
  * transactions (partitioned by date)
  * loans.parquet
* Use:

  * Faker
  * NumPy
* Ensure schema matches what Python scripts expect

---

### 5. Analytics Logic

#### Customer 360

* Aggregations: COUNT, AVG, MAX
* Risk scoring logic

#### Loan Scoring

* Payment history analysis
* Debt-to-income ratio
* Credit score formula
* Eligibility decision

#### Fraud Detection

* Amount anomaly
* Geo anomaly
* Velocity checks
* Category anomaly
* Time-of-day analysis

---

### 6. IPC Mechanism

Start with:

* ✅ Subprocess + stdout (mandatory)

Optional (if time permits):

* Flat file
* Named pipes

---

### 7. Error Handling

Implement:

* Return codes (00, 01, 99)
* Python failure handling
* Data validation before output
* Safe fallback values in COBOL

---

### 8. Output Format

You MUST generate:

#### 1. Code

* All COBOL programs
* All Python scripts
* Utility modules

#### 2. Project structure (ONLY if modified)

#### 3. Setup instructions

* Installation steps
* Dependencies
* How to run each module

#### 4. Example executions

* Sample inputs
* Expected outputs

---

## ❗ Important Rules

* DO NOT skip any module
* DO NOT simplify logic
* DO NOT ignore fixed-width formatting
* DO NOT invent new architecture

If something is unclear:
👉 ASK QUESTIONS BEFORE writing code

---

## ✅ Quality Expectations

* Clean, modular code
* Production-like structure
* Clear comments where needed
* Consistent naming
* Deterministic outputs

---

## 🚀 Goal

The final result should be:

* Fully runnable
* Easy to test
* Aligned with the thesis architecture
* Suitable for benchmarking and demonstration
