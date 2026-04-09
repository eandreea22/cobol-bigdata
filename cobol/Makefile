.PHONY: all compile clean run-customer-lookup run-loan-process run-fraud-check help

# COBOL Compiler Configuration
CC = cobc
CFLAGS = -x -free -I copybooks
LDFLAGS = -lm

# Source files
SOURCES = CUSTOMER-LOOKUP.cbl LOAN-PROCESS.cbl FRAUD-CHECK.cbl

# Executables
TARGETS = customer-lookup loan-process fraud-check

# Build all executables
all: $(TARGETS)
	@echo ""
	@echo "✓ All COBOL programs compiled successfully"
	@echo "  Executables: $(TARGETS)"
	@echo ""
	@echo "Usage:"
	@echo "  make run-customer-lookup [CUSTOMER_ID=C-00001]"
	@echo "  make run-loan-process [CUSTOMER_ID=C-00001]"
	@echo "  make run-fraud-check [CUSTOMER_ID=C-00001]"
	@echo ""

# Compile individual programs
customer-lookup: CUSTOMER-LOOKUP.cbl copybooks/CUSTOMER-REC.cpy
	$(CC) $(CFLAGS) -o $@ CUSTOMER-LOOKUP.cbl
	@echo "✓ Compiled: $@"

loan-process: LOAN-PROCESS.cbl copybooks/LOAN-REC.cpy
	$(CC) $(CFLAGS) -o $@ LOAN-PROCESS.cbl
	@echo "✓ Compiled: $@"

fraud-check: FRAUD-CHECK.cbl copybooks/FRAUD-REC.cpy
	$(CC) $(CFLAGS) -o $@ FRAUD-CHECK.cbl
	@echo "✓ Compiled: $@"

# Run targets
run-customer-lookup: customer-lookup
	@./customer-lookup $(CUSTOMER_ID)

run-loan-process: loan-process
	@./loan-process $(CUSTOMER_ID) $(AMOUNT) $(TERM) $(PURPOSE)

run-fraud-check: fraud-check
	@./fraud-check $(CUSTOMER_ID) $(AMOUNT) $(MCC) $(LOCATION) "$(TIMESTAMP)" $(CHANNEL)

# Benchmark target (Phase 7)
benchmark:
	@echo "Running benchmarks..."
	python3 ../benchmarks/bench_vsam_vs_parquet.py
	python3 ../benchmarks/bench_ipc_overhead.py

# Clean compiled objects
clean:
	@rm -f $(TARGETS)
	@rm -f /tmp/cust-response.dat /tmp/loan-response.dat /tmp/fraud-response.dat
	@echo "✓ Cleaned: executables and temp files"

# Help
help:
	@echo "COBOL Banking System - Makefile Commands"
	@echo "=========================================="
	@echo ""
	@echo "Building:"
	@echo "  make all                 - Compile all COBOL programs"
	@echo "  make clean               - Remove executables and temp files"
	@echo ""
	@echo "Running:"
	@echo "  make run-customer-lookup CUSTOMER_ID=C-00001"
	@echo "  make run-loan-process CUSTOMER_ID=C-00001 AMOUNT=10000 TERM=36 PURPOSE=PERS"
	@echo "  make run-fraud-check CUSTOMER_ID=C-00001 AMOUNT=500 MCC=5411 LOCATION=Bucharest TIMESTAMP='2025-01-15T14:30:00' CHANNEL=POS"
	@echo ""
	@echo "Testing:"
	@echo "  make benchmark           - Run performance benchmarks"
	@echo ""
