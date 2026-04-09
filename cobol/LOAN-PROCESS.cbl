       IDENTIFICATION DIVISION.
       PROGRAM-ID. LOAN-PROCESS.
       AUTHOR. Thesis Project.

      *> LOAN-PROCESS.cbl
      *> Loan Eligibility Assessment Program
      *>
      *> Accepts loan application details and returns eligibility
      *> decision, credit score, interest rate, and maximum amount.
      *>
      *> Invocation: LOAN-PROCESS <customer_id> <amount> <term> <purpose>
      *> Example: ./loan-process C-00001 10000 36 PERS
      *>
      *> IPC Pattern:
      *>   1. Accept 4 CLI parameters
      *>   2. CALL "SYSTEM" invokes python/loan_scoring.py
      *>   3. Python writes 51-byte record to /tmp/loan-response.dat
      *>   4. COBOL reads and parses response
      *>   5. Display eligibility decision or error

       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT RESPONSE-FILE ASSIGN TO "loan-response.dat"
               ORGANIZATION IS LINE SEQUENTIAL.

       DATA DIVISION.
       FILE SECTION.
       FD  RESPONSE-FILE.
       01  RESPONSE-RECORD               PIC X(52).

       WORKING-STORAGE SECTION.
      *> Include copybook for response record structure
           COPY "LOAN-REC.cpy".

      *> Input parameters
       01  WS-CUSTOMER-ID                PIC X(10) VALUE SPACES.
       01  WS-LOAN-AMOUNT                PIC 9(8)V99 VALUE 0.
       01  WS-LOAN-TERM                  PIC 9(3) VALUE 0.
       01  WS-PURPOSE-CODE               PIC X(4) VALUE SPACES.

      *> String versions for CLI passing
       01  WS-AMOUNT-STR                 PIC X(15) VALUE SPACES.
       01  WS-TERM-STR                   PIC X(5) VALUE SPACES.

      *> Command line and execution
       01  WS-CMD                        PIC X(300) VALUE SPACES.
       01  WS-CMD-RESULT                 PIC 9(4) VALUE 0.

      *> Safe defaults for error cases
       01  WS-SAFE-DEFAULTS.
           05  WS-SAFE-SCORE             PIC 9(3) VALUE 300.
           05  WS-SAFE-ELIGIBLE          PIC X(1) VALUE "N".
           05  WS-SAFE-RATE              PIC 9V9(4) VALUE 0.
           05  WS-SAFE-MAX-AMT           PIC 9(8)V99 VALUE 0.
           05  WS-SAFE-REASON            PIC X(30)
               VALUE "SYSTEM_ERROR".

       PROCEDURE DIVISION.
       MAIN-PROCEDURE.
           DISPLAY "========================================".
           DISPLAY "LOAN ELIGIBILITY ASSESSMENT".
           DISPLAY "========================================".

      *> Accept parameters from command line
           ACCEPT WS-CUSTOMER-ID FROM COMMAND-LINE.

      *> Validate input
           IF WS-CUSTOMER-ID = SPACES
               DISPLAY "ERROR: Missing parameters"
               DISPLAY "Usage: LOAN-PROCESS <id> <amount> <term> "
                   "<purpose>"
               MOVE 1 TO RETURN-CODE
               STOP RUN
           END-IF.

      *> TODO: Parse additional parameters (amount, term, purpose)
      *> For now, using default values for simplicity
      *> Production version would parse from COMMAND-LINE split by spaces
           MOVE 10000 TO WS-LOAN-AMOUNT.
           MOVE 36 TO WS-LOAN-TERM.
           MOVE "PERS" TO WS-PURPOSE-CODE.

      *> Convert numerics to strings for CLI
           MOVE WS-LOAN-AMOUNT TO WS-AMOUNT-STR.
           MOVE WS-LOAN-TERM TO WS-TERM-STR.

      *> Build command to invoke Python script
      *> Windows-compatible: python script > file 2>nul
           STRING
               "python python/loan_scoring.py "
               DELIMITED BY SIZE
               WS-CUSTOMER-ID DELIMITED BY SPACE
               " "
               DELIMITED BY SIZE
               WS-AMOUNT-STR DELIMITED BY SPACE
               " "
               DELIMITED BY SIZE
               WS-TERM-STR DELIMITED BY SPACE
               " "
               DELIMITED BY SIZE
               WS-PURPOSE-CODE DELIMITED BY SPACE
               " > loan-response.dat 2>nul"
               DELIMITED BY SIZE
               INTO WS-CMD
           END-STRING.

      *> Execute Python script
           DISPLAY "Calling: " WS-CMD.
           CALL "SYSTEM" USING WS-CMD.
           MOVE RETURN-CODE TO WS-CMD-RESULT.

           IF WS-CMD-RESULT NOT = 0
               DISPLAY "ERROR: Python script failed (code "
                   WS-CMD-RESULT ")"
               PERFORM SHOW-SAFE-DEFAULTS
               MOVE 1 TO RETURN-CODE
               STOP RUN
           END-IF.

      *> Open response file and read record
           OPEN INPUT RESPONSE-FILE.

           READ RESPONSE-FILE INTO WS-RAW-LOAN-RESPONSE
               AT END
                   DISPLAY "ERROR: No response from Python script"
                   CLOSE RESPONSE-FILE
                   PERFORM SHOW-SAFE-DEFAULTS
                   MOVE 1 TO RETURN-CODE
                   STOP RUN
               NOT AT END
                   CONTINUE
           END-READ.

           CLOSE RESPONSE-FILE.

      *> Parse response record
           PERFORM PARSE-RESPONSE-RECORD.

      *> Check return code from Python
           IF FUNCTION NUMVAL(LR-RETURN-CODE-STR) = 99
               DISPLAY ""
               DISPLAY ">>> ERROR: Python script returned error code"
               PERFORM SHOW-SAFE-DEFAULTS
               MOVE 1 TO RETURN-CODE
               STOP RUN
           END-IF.

      *> Display results
           PERFORM DISPLAY-LOAN-RESULTS.

           MOVE 0 TO RETURN-CODE.
           STOP RUN.

       PARSE-RESPONSE-RECORD.
      *> Convert numeric string fields
           MOVE FUNCTION NUMVAL(LR-CREDIT-SCORE-STR)
               TO LR-CREDIT-SCORE.
           MOVE FUNCTION NUMVAL(LR-INT-RATE-STR)
               TO LR-INT-RATE.
           MOVE FUNCTION NUMVAL(LR-MAX-AMOUNT-STR)
               TO LR-MAX-AMOUNT.
           MOVE FUNCTION NUMVAL(LR-RETURN-CODE-STR)
               TO LR-RETURN-CODE.

       DISPLAY-LOAN-RESULTS.
           DISPLAY "".
           DISPLAY "LOAN ELIGIBILITY ASSESSMENT".
           DISPLAY "========================================".
           DISPLAY "Customer ID:     " WS-CUSTOMER-ID.
           DISPLAY "Loan Amount:     $" WS-LOAN-AMOUNT.
           DISPLAY "Term (months):   " WS-LOAN-TERM.
           DISPLAY "Purpose:         " WS-PURPOSE-CODE.
           DISPLAY "".
           DISPLAY "ASSESSMENT RESULTS".
           DISPLAY "----------------------------------------".
           DISPLAY "Credit Score:    " LR-CREDIT-SCORE " (300-850)".
           DISPLAY "Eligible:        " LR-ELIGIBLE.

           IF LR-ELIGIBLE = "Y"
               DISPLAY "Interest Rate:   " LR-INT-RATE "%"
               DISPLAY "Max Loan Amount: $" LR-MAX-AMOUNT
           ELSE
               DISPLAY "Rejection Reason:" LR-REJECT-REASON
           END-IF.

           DISPLAY "========================================".

       SHOW-SAFE-DEFAULTS.
           DISPLAY "".
           DISPLAY "LOAN ELIGIBILITY ASSESSMENT (ERROR)".
           DISPLAY "========================================".
           DISPLAY "Customer ID:     " WS-CUSTOMER-ID.
           DISPLAY "Loan Amount:     $" WS-LOAN-AMOUNT.
           DISPLAY "Term (months):   " WS-LOAN-TERM.
           DISPLAY "Purpose:         " WS-PURPOSE-CODE.
           DISPLAY "".
           DISPLAY "ASSESSMENT RESULTS (DEFAULTS)".
           DISPLAY "----------------------------------------".
           DISPLAY "Credit Score:    " WS-SAFE-SCORE " (300-850)".
           DISPLAY "Eligible:        " WS-SAFE-ELIGIBLE.
           DISPLAY "Rejection Reason:" WS-SAFE-REASON.
           DISPLAY "========================================".
