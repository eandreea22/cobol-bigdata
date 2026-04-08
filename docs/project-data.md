





MODERNIZING COBOL
WITH BIG DATA PIPELINES

Integrating Python Data Pipelines into Legacy COBOL Banking Systems



Master’s Degree Final Paper
Technical Documentation & System Design


Author: [Your Name]
Supervisor: [Supervisor Name]
Academic Year: 2025–2026
 
Table of Contents


 
1. Executive Summary
This document presents the technical design and implementation plan for a master’s thesis project titled “Modernizing COBOL with Big Data Pipelines.” The project demonstrates how legacy COBOL banking systems, which remain the backbone of global financial infrastructure, can be extended with modern Python-based data pipelines without requiring a complete system rewrite.
The core innovation is an Inter-Process Communication (IPC) bridge that allows COBOL programs to delegate data-intensive operations to Python scripts. These scripts query a modern analytical data layer built on Apache Parquet columnar files and DuckDB, enabling capabilities that COBOL was never designed to handle: large-scale analytics, machine learning-based scoring, and real-time anomaly detection.
The project simulates three critical banking workflows — customer 360° lookup, loan eligibility assessment, and fraud detection — and provides measurable benchmarks comparing the hybrid COBOL-Python approach against traditional COBOL-only file processing.
 
2. Business Context & Problem Statement
2.1 The COBOL reality in banking
COBOL (Common Business-Oriented Language) was introduced in 1959 and remains one of the most widely deployed programming languages in the financial sector. According to industry estimates, approximately 95% of ATM transactions and 80% of in-person transactions globally still run through COBOL-based systems. Major banks process billions of daily transactions on COBOL mainframes, with an estimated 220 billion lines of COBOL code still in active production worldwide.
These systems are remarkably stable and performant for their original design purpose: high-throughput, sequential transaction processing with strong data integrity guarantees. However, they were architectured in an era when data volumes were measured in megabytes, not petabytes, and analytical queries were batch-processed overnight rather than executed in real time.
2.2 The big data challenge
Modern banking demands capabilities that COBOL’s architecture cannot natively support:
•	Real-time analytics: Customer risk profiling, spending pattern analysis, and portfolio optimization require scanning millions of records with complex aggregations — operations that COBOL’s sequential file processing handles poorly.
•	Machine learning integration: Credit scoring models, fraud detection algorithms, and customer segmentation require Python/R ecosystems with libraries like scikit-learn, pandas, and TensorFlow that have no COBOL equivalents.
•	Columnar data access: Modern analytical workloads benefit enormously from columnar storage formats (Parquet, ORC) that enable predicate pushdown and column pruning. COBOL’s record-oriented VSAM files force full-record reads regardless of which fields are needed.
•	Data lake integration: Banks increasingly store historical data in cloud data lakes (S3, Azure Blob Storage) that COBOL mainframes cannot query directly.
2.3 Why not rewrite everything?
Complete COBOL-to-modern-language rewrites are notoriously risky and expensive. The Commonwealth Bank of Australia’s migration from COBOL took over five years and cost an estimated $750 million. Many attempted rewrites have failed entirely, leaving organizations worse off than before. The business logic encoded in decades-old COBOL programs is often poorly documented, deeply intertwined with regulatory requirements, and understood by a shrinking pool of senior developers.
This project proposes a pragmatic middle path: keep COBOL for what it does well (transaction processing, business logic, regulatory compliance) and extend it with Python pipelines for what it cannot do (big data analytics, ML scoring, data lake queries). The IPC bridge is the key architectural component that makes this hybrid approach possible.
 
3. System Architecture
3.1 Architecture overview
The system is organized into five distinct layers, each with a clear responsibility boundary:
Layer	Technology	Responsibility
Entry points	Terminal / ATM / Batch	User-facing interfaces that trigger banking operations
Core banking	GnuCOBOL programs	Business logic, validation, workflow orchestration
IPC bridge	Subprocess / pipes / files	Communication layer between COBOL and Python
Data pipeline	Python 3.11+ scripts	Big data queries, analytics, ML scoring
Data layer	Parquet + DuckDB	Columnar storage and analytical query engine

3.2 Data flow pattern
Every interaction follows the same fundamental pattern regardless of which module is invoked:
1.	A trigger event occurs (teller input, ATM request, or scheduled batch job).
2.	The appropriate COBOL program receives the request and validates input parameters against its PICTURE clause definitions.
3.	COBOL packages the validated parameters into a standardized request format and invokes the IPC bridge.
4.	The IPC bridge launches the corresponding Python script, passing parameters via command-line arguments, environment variables, or a request file.
5.	The Python script queries the Parquet-based data lake through DuckDB, performs any required analytics or scoring computations, and formats the result as a fixed-width record matching the COBOL copybook layout.
6.	The result is returned through the IPC bridge (stdout pipe or response file).
7.	COBOL reads the response record into its WORKING-STORAGE variables and continues its business logic with the enriched data.
3.3 Design principles
•	Separation of concerns: COBOL owns business logic and validation. Python owns data access and analytics. Neither crosses into the other’s domain.
•	COBOL-native interfaces: The IPC bridge uses fixed-width records that map directly to COBOL copybooks. Python adapts to COBOL’s data format, not the other way around.
•	Stateless Python scripts: Each Python invocation is independent. No shared state, no sessions, no connection pooling. This matches COBOL’s batch-oriented processing model.
•	Fail-safe defaults: If the Python script fails or times out, COBOL falls back to a safe default (e.g., FLAG-RISK = “UNKNOWN”, LOAN-ELIGIBLE = “N”). The legacy system never depends on the modern layer being available.
 
4. Module Specifications
4.1 Module 1: Customer 360° lookup
4.1.1 Business scenario
A bank teller receives a customer at the counter. The customer wants to inquire about their account status, recent transactions, and available products. The teller enters the customer’s ID into the terminal. The COBOL program needs to return a comprehensive 360-degree view of the customer, including data aggregated from millions of historical transaction records stored in the data lake.
4.1.2 COBOL program: CUSTOMER-LOOKUP.cbl
The COBOL program defines the following data structures in its WORKING-STORAGE SECTION:
Field	PIC Clause	Description
WS-CUSTOMER-ID	PIC X(10)	Input: customer identifier
WS-CUST-NAME	PIC X(50)	Output: full customer name
WS-ACCT-BALANCE	PIC 9(10)V99	Output: current account balance
WS-TXN-COUNT	PIC 9(8)	Output: total lifetime transactions
WS-AVG-MONTHLY	PIC 9(8)V99	Output: average monthly spending
WS-RISK-SCORE	PIC 9(3)	Output: computed risk score (0–999)
WS-LAST-TXN-DATE	PIC X(10)	Output: date of last transaction
WS-RETURN-CODE	PIC 99	Output: 00=success, 01=not found, 99=error

4.1.3 Python script: customer_360.py
The Python script accepts a customer ID as a command-line argument, queries the data lake, and returns a fixed-width string that maps byte-for-byte to the COBOL copybook:
Usage: python3 customer_360.py <customer_id>
Output: Fixed-width record (145 bytes) to stdout

Key operations performed by the script:
1.	Parse customer_id from sys.argv[1].
2.	Connect to DuckDB (in-memory instance).
3.	Query customers.parquet for demographic data.
4.	Query transactions/*.parquet with aggregation: COUNT(*), AVG(amount), MAX(txn_date).
5.	Compute risk score based on transaction frequency, average amount, and recency.
6.	Format all fields as fixed-width strings matching PIC clauses (right-justified numerics, left-justified alphanumerics, zero-padded).
7.	Write the single-line record to stdout.
4.1.4 IPC contract
The fixed-width response record is structured as follows (total 145 bytes):
Field	Start byte	Length	Format
CUST-NAME	1	50	Left-justified, space-padded
ACCT-BALANCE	51	12	Right-justified, zero-padded, implied V99
TXN-COUNT	63	8	Right-justified, zero-padded
AVG-MONTHLY	71	10	Right-justified, zero-padded, implied V99
RISK-SCORE	81	3	Right-justified, zero-padded (000–999)
LAST-TXN-DATE	84	10	YYYY-MM-DD format
RETURN-CODE	94	2	00, 01, or 99

 
4.2 Module 2: Loan eligibility assessment
4.2.1 Business scenario
A customer applies for a personal loan. The loan officer enters the application details into the system: customer ID, requested loan amount, desired term in months, and the loan purpose code. The COBOL program must determine whether the customer is eligible based on their historical financial behavior — data that resides in the Parquet-based data lake across millions of historical records.
4.2.2 COBOL program: LOAN-PROCESS.cbl
Input parameters collected by the COBOL program:
Field	PIC Clause	Description
WS-CUSTOMER-ID	PIC X(10)	Customer identifier
WS-LOAN-AMOUNT	PIC 9(8)V99	Requested loan amount
WS-LOAN-TERM	PIC 9(3)	Loan term in months
WS-PURPOSE-CODE	PIC X(4)	Loan purpose (HOME, AUTO, PERS, EDUC)

Output fields returned from the Python pipeline:
Field	PIC Clause	Description
WS-CREDIT-SCORE	PIC 9(3)	Computed credit score (300–850)
WS-ELIGIBLE	PIC X(1)	Y = approved, N = rejected
WS-INT-RATE	PIC 9V9(4)	Recommended interest rate
WS-MAX-AMOUNT	PIC 9(8)V99	Maximum approvable amount
WS-REJECT-REASON	PIC X(30)	Reason code if rejected

4.2.3 Python script: loan_scoring.py
The Python script performs the following analytical operations on the data lake:
•	Payment history analysis: Queries loans.parquet for the customer’s historical loan records. Calculates on-time payment ratio, average days-past-due, and number of defaults.
•	Income stability assessment: Analyzes recurring credit transactions (salary deposits) from transactions.parquet. Computes income consistency coefficient over the past 12 months.
•	Debt-to-income ratio: Sums all active loan obligations and compares against estimated monthly income to derive DTI percentage.
•	Credit score computation: Applies a weighted formula: payment_history (35%) + credit_utilization (30%) + credit_length (15%) + new_credit (10%) + credit_mix (10%), normalized to the 300–850 range.
•	Eligibility decision: If credit_score >= 650 and DTI < 0.43 and no recent defaults, the customer is eligible. The interest rate is computed as base_rate + risk_premium based on the score tier.
 
4.3 Module 3: Fraud detection
4.3.1 Business scenario
During real-time transaction processing, every transaction must be screened for potential fraud before approval. The COBOL transaction engine passes transaction details to the fraud detection pipeline, which analyzes the transaction against the customer’s historical patterns stored in the data lake. The response must arrive within an acceptable latency window (target: under 500ms) to avoid degrading the customer experience.
4.3.2 COBOL program: FRAUD-CHECK.cbl
The COBOL program passes the following transaction details to the Python fraud detector:
Field	PIC Clause	Description
WS-CUSTOMER-ID	PIC X(10)	Customer identifier
WS-TXN-AMOUNT	PIC 9(8)V99	Transaction amount
WS-MERCHANT-CAT	PIC X(4)	Merchant category code (MCC)
WS-TXN-LOCATION	PIC X(20)	Transaction city/country
WS-TXN-TIMESTAMP	PIC X(19)	ISO 8601 timestamp
WS-TXN-CHANNEL	PIC X(3)	POS, ATM, ONL, MOB

The Python script returns a fraud assessment:
Field	PIC Clause	Description
WS-FRAUD-RISK	PIC X(6)	LOW, MEDIUM, or HIGH
WS-FRAUD-SCORE	PIC 9(3)	Numerical risk score (0–100)
WS-FRAUD-FLAGS	PIC X(60)	Comma-separated risk indicators
WS-RECOMMEND	PIC X(7)	APPROVE, REVIEW, or DECLINE

4.3.3 Python script: fraud_detect.py
The fraud detection script implements a rule-based anomaly scoring system with the following checks:
•	Amount anomaly: Compares the transaction amount against the customer’s historical mean and standard deviation. Transactions exceeding 3 standard deviations from the mean receive a high score.
•	Geographic anomaly: Checks if the transaction location is consistent with the customer’s typical transaction geography. A sudden change from Bucharest to Lagos within hours triggers a flag.
•	Velocity check: Counts the number of transactions within the last hour and last 24 hours. Unusual spikes in transaction frequency indicate potential card compromise.
•	Category anomaly: Identifies merchant categories the customer has never transacted with before. First-time high-value transactions in unfamiliar categories receive additional scrutiny.
•	Time-of-day analysis: Transactions occurring outside the customer’s normal active hours receive a minor risk increment.
 
5. IPC Bridge Design
5.1 Communication mechanisms
The project implements and benchmarks three IPC approaches, allowing for comparative analysis in the thesis:
5.1.1 Option A: Subprocess with stdout pipe
The simplest approach. COBOL uses the CALL "SYSTEM" statement to invoke Python as a subprocess. Parameters are passed as command-line arguments. Python writes the response record to stdout, which COBOL reads from the pipe.
CALL "SYSTEM" USING
  "python3 customer_360.py C-10042 > /tmp/response.dat"
END-CALL.
OPEN INPUT RESPONSE-FILE.
READ RESPONSE-FILE INTO WS-RESPONSE-REC.

Advantages: Minimal complexity, no persistent processes, easy to debug. Disadvantages: Process creation overhead on every call, not suitable for high-frequency invocations.
5.1.2 Option B: Flat file exchange
The most COBOL-native approach. COBOL writes a fixed-width request record to a request file. A Python watcher script or a direct invocation reads the request, processes it, and writes the response to a separate file. COBOL reads the response.
OPEN OUTPUT REQUEST-FILE.
WRITE REQUEST-REC FROM WS-REQUEST-REC.
CLOSE REQUEST-FILE.
CALL "SYSTEM" USING "python3 process_request.py"
OPEN INPUT RESPONSE-FILE.
READ RESPONSE-FILE INTO WS-RESPONSE-REC.

Advantages: Mirrors traditional COBOL I/O patterns, easy audit trail (files can be archived), supports batch processing of multiple requests. Disadvantages: Disk I/O overhead, file locking complexity in concurrent scenarios.
5.1.3 Option C: Named pipes (FIFO)
The most advanced approach. Python runs as a persistent daemon listening on a UNIX named pipe (FIFO). COBOL writes request records to the FIFO, and Python responds on a second FIFO. This simulates a microservice-like architecture.
OPEN OUTPUT REQUEST-PIPE.
WRITE REQUEST-REC FROM WS-REQUEST-REC.
CLOSE REQUEST-PIPE.
OPEN INPUT RESPONSE-PIPE.
READ RESPONSE-PIPE INTO WS-RESPONSE-REC.

Advantages: No process creation overhead per request, persistent Python process can maintain DuckDB connections and caches, lowest latency. Disadvantages: Requires process management (systemd or supervisor), more complex error handling, debugging is harder.
5.2 Data format contract
All three IPC options use the same data format: fixed-width records defined by COBOL copybooks. The Python utility module ipc_formatter.py provides functions to serialize Python data structures into COBOL-compatible fixed-width strings:
def format_pic_x(value: str, length: int) -> str:
    return value.ljust(length)[:length]

def format_pic_9(value: float, integer_digits: int,
                  decimal_digits: int = 0) -> str:
    scaled = int(value * (10 ** decimal_digits))
    total = integer_digits + decimal_digits
    return str(abs(scaled)).zfill(total)[:total]
5.3 Error handling strategy
The IPC bridge implements a three-tier error handling strategy:
•	Tier 1 — Python script failure: If the Python script exits with a non-zero return code or produces malformed output, the COBOL program detects this via the RETURN-CODE field (99 = error) and falls back to a safe default response.
•	Tier 2 — Timeout: COBOL implements a timeout mechanism. If the response file is not available within 5 seconds (configurable), the program proceeds with a default “UNKNOWN” risk assessment or “N” eligibility.
•	Tier 3 — Data integrity: The Python script validates all output fields against the expected PIC clause lengths before writing. If any field would overflow or underflow, the script logs a warning and pads/truncates to fit.
 
6. Data Layer Design
6.1 Synthetic data generation
The project uses a Python script (generate_synthetic.py) to create realistic banking data. All data is synthetic but statistically representative of real banking patterns:
Dataset	Record count	Key fields
customers.parquet	100,000	customer_id, name, dob, city, account_open_date, credit_tier
transactions/	10,000,000+	txn_id, customer_id, amount, merchant, mcc, city, timestamp
loans.parquet	500,000	loan_id, customer_id, amount, term, rate, status, payments[]
fraud_labels.parquet	50,000	txn_id, is_fraud, fraud_type, detection_method

6.2 Parquet partitioning strategy
The transactions dataset is partitioned by date to enable efficient predicate pushdown. When a Python script queries transactions for a specific customer within the last 12 months, DuckDB’s Parquet reader automatically prunes partitions outside the date range, dramatically reducing I/O:
data/transactions/
  date=2024-01-01/part-0000.parquet
  date=2024-01-02/part-0000.parquet
  ...
  date=2025-12-31/part-0000.parquet

Each daily partition contains approximately 27,000 transaction records (10M records / 365 days). This partitioning granularity balances file count against partition pruning efficiency.
6.3 DuckDB as the query engine
DuckDB is used as an in-process analytical database engine. Each Python script creates a DuckDB in-memory instance and queries Parquet files directly using the read_parquet() function. Key advantages for this project:
•	Zero infrastructure: DuckDB is an embedded database — no server to install, configure, or maintain. It runs inside the Python process.
•	Columnar execution: DuckDB uses a vectorized execution engine optimized for analytical queries. It reads only the columns needed for each query, not entire records.
•	Parquet native: DuckDB reads Parquet files natively with predicate pushdown, statistics-based pruning, and parallel scanning.
•	SQL interface: Queries are written in standard SQL, making the code readable and maintainable.
6.4 VSAM simulation for benchmarking
To benchmark the hybrid approach against traditional COBOL processing, the project also generates VSAM-equivalent indexed sequential files. These are flat files with fixed-width records and a separate index file, simulating how COBOL would natively access data without the Python pipeline. The benchmark compares query times for identical operations (customer lookup, loan history scan, transaction pattern analysis) across both approaches.
 
7. Project Structure
The repository is organized to clearly separate concerns between COBOL, Python, and shared data:
cobol-bigdata-thesis/
├── cobol/
│   ├── CUSTOMER-LOOKUP.cbl
│   ├── LOAN-PROCESS.cbl
│   ├── FRAUD-CHECK.cbl
│   ├── copybooks/
│   │   ├── CUSTOMER-REC.cpy
│   │   ├── LOAN-REC.cpy
│   │   └── FRAUD-REC.cpy
│   └── Makefile
├── python/
│   ├── customer_360.py
│   ├── loan_scoring.py
│   ├── fraud_detect.py
│   ├── report_aggregator.py
│   └── utils/
│       ├── parquet_reader.py
│       └── ipc_formatter.py
├── data/
│   ├── generate_synthetic.py
│   ├── customers.parquet
│   ├── transactions/
│   └── loans.parquet
├── benchmarks/
│   ├── bench_vsam_vs_parquet.py
│   ├── bench_ipc_overhead.py
│   └── results/
├── docs/
│   ├── architecture.mermaid
│   └── thesis_outline.md
└── README.md

7.1 Build and compilation
COBOL programs are compiled using GnuCOBOL (formerly OpenCOBOL), the open-source COBOL compiler available on Linux. The Makefile provides targets for compiling individual programs and running the full test suite:
# Compile all COBOL programs
make all

# Compile and run Module 1
make run-customer-lookup CUSTOMER_ID=C-10042

# Run full benchmark suite
make benchmark
 
8. Benchmarking Methodology
8.1 Performance benchmarks
The thesis makes three measurable performance claims. Each is validated through controlled benchmarks:
8.1.1 Claim 1: Big data query performance
Hypothesis: For datasets exceeding 1 million records, the COBOL + Python + DuckDB/Parquet hybrid outperforms COBOL-only VSAM sequential scanning for analytical queries.
Test methodology:
1.	Generate datasets at varying scales: 10K, 100K, 1M, 5M, 10M records.
2.	Implement the same customer lookup query in both approaches: (a) COBOL reading a VSAM-equivalent indexed file, and (b) COBOL calling Python + DuckDB on Parquet.
3.	Measure wall-clock time for 100 random customer lookups at each scale.
4.	Record the crossover point where the hybrid approach becomes faster.
5.	Plot results as a line chart (x = dataset size, y = average query time).
8.1.2 Claim 2: IPC overhead analysis
Hypothesis: The IPC bridge introduces measurable but acceptable latency overhead that varies by communication mechanism.
Test methodology: Execute 1,000 identical requests through each IPC option (subprocess, flat file, named pipe) and measure the distribution of round-trip times. Report mean, P50, P95, and P99 latencies.
8.1.3 Claim 3: Analytical capability comparison
Hypothesis: Certain analytical operations that are impractical in pure COBOL become feasible through the Python pipeline.
Demonstrate by implementing in both COBOL-only and COBOL+Python: (a) compute standard deviation of transaction amounts for a customer, (b) identify the customer’s most frequent merchant category, (c) detect geographic outliers in transaction history. Measure lines of code, execution time, and result accuracy for each approach.
8.2 Maintainability metrics
Beyond performance, the thesis evaluates software engineering benefits:
•	Lines of code: Compare total LOC for COBOL-only vs. hybrid implementation of each module.
•	Deployment independence: Demonstrate that Python scripts can be updated, tested, and deployed without recompiling COBOL programs.
•	Testability: Show that Python scripts have unit tests (pytest) with mocked Parquet data, while COBOL programs can only be tested end-to-end.
•	Extensibility: Add a new analytical feature (e.g., customer lifetime value) by creating a single new Python script, with zero changes to COBOL.
 
9. Implementation Roadmap
The project is structured into six phases, designed to deliver working functionality incrementally:
Phase	Deliverable	Description	Duration
1	Data generation	generate_synthetic.py + all Parquet files	1 week
2	Module 1 E2E	Customer lookup: COBOL + Python + IPC	2 weeks
3	Module 2 + 3	Loan processing and fraud detection	2 weeks
4	Benchmarks	All three IPC options + scaling tests	1 week
5	Analysis	Results collection, charts, statistical analysis	1 week
6	Thesis writing	Paper composition, review, final submission	3 weeks

Total estimated duration: 10 weeks from project start to thesis submission.
 
10. Technology Stack
Component	Technology	Version / notes
COBOL compiler	GnuCOBOL	3.2+ (apt install gnucobol on Ubuntu)
Python runtime	Python	3.11+ (required for DuckDB compatibility)
Query engine	DuckDB	1.1+ (pip install duckdb)
Data format	Apache Parquet	Via pyarrow (pip install pyarrow)
Data generation	Faker + NumPy	Synthetic data generation libraries
Testing	pytest	Python unit tests for pipeline scripts
Benchmarking	time + matplotlib	Wall-clock measurement + chart generation
OS	Ubuntu 22.04+	Linux required for GnuCOBOL + named pipes
Version control	Git	GitHub repository

 
11. Academic Contribution & Thesis Arguments
11.1 Research questions
The thesis addresses three primary research questions:
8.	Can legacy COBOL banking systems be extended with big data capabilities through Python-based IPC bridges without modifying the core COBOL business logic?
9.	At what data volume threshold does the hybrid COBOL-Python-Parquet approach outperform traditional COBOL sequential file processing for analytical queries?
10.	What are the latency, maintainability, and extensibility trade-offs of different IPC mechanisms (subprocess, flat file, named pipe) in a COBOL-Python hybrid architecture?
11.2 Expected contributions
•	Practical framework: A reusable architectural pattern for modernizing COBOL systems with Python data pipelines, applicable beyond the banking domain.
•	Empirical benchmarks: Quantitative performance data comparing COBOL-only vs. hybrid approaches at various data scales, providing evidence-based guidance for modernization decisions.
•	IPC analysis: A comparative evaluation of three IPC mechanisms with latency distributions, helping architects choose the right bridge for their performance requirements.
•	Cost-benefit model: A framework for evaluating whether the modernization investment is justified based on data volume, query complexity, and operational requirements.
11.3 Limitations and scope
The project acknowledges the following limitations:
•	The simulation runs on a Linux workstation with GnuCOBOL, not an actual IBM mainframe. Real mainframe environments have different performance characteristics, especially for VSAM I/O.
•	The synthetic data, while statistically representative, does not capture all the complexity of real banking data (multi-currency, international regulations, real-time settlement).
•	Security considerations (encryption of data in transit between COBOL and Python, authentication of subprocess calls) are acknowledged but not implemented in this prototype.
•	The project focuses on batch and near-real-time scenarios. True real-time transaction processing at mainframe scale (thousands of TPS) is outside the scope of this simulation.

End of Technical Documentation
