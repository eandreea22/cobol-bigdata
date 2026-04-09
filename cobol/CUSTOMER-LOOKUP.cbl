       IDENTIFICATION DIVISION.
       PROGRAM-ID. CUSTOMER-LOOKUP.
       AUTHOR. Thesis Project.

      *> CUSTOMER-LOOKUP.cbl
      *> Customer 360° Lookup Program
      *>
      *> Accepts a customer ID and returns a comprehensive 360-degree
      *> view including demographics, account balance, transaction
      *> statistics, and risk score.
      *>
      *> Invocation: CUSTOMER-LOOKUP <customer_id>
      *> Example: ./customer-lookup C-00001
      *>
      *> IPC Pattern:
      *>   1. CALL "SYSTEM" invokes python/customer_360.py via subprocess
      *>   2. Python writes 145-byte record to /tmp/cust-response.dat
      *>   3. COBOL reads response into copybook structure
      *>   4. FUNCTION NUMVAL() converts numeric strings
      *>   5. Display results or safe defaults on error (return code 99)

       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT RESPONSE-FILE ASSIGN TO "cust-response.dat"
               ORGANIZATION IS LINE SEQUENTIAL.

       DATA DIVISION.
       FILE SECTION.
       FD  RESPONSE-FILE.
       01  RESPONSE-RECORD               PIC X(146).

       WORKING-STORAGE SECTION.
      *> Include copybook for response record structure
           COPY "CUSTOMER-REC.cpy".

      *> Input parameters
       01  WS-CUSTOMER-ID                PIC X(10) VALUE SPACES.

      *> Command line and execution
       01  WS-CMD                        PIC X(300) VALUE SPACES.
       01  WS-CMD-RESULT                 PIC 9(4) VALUE 0.

      *> Working variables for file operations
       01  WS-EOF-FLAG                   PIC X VALUE "N".
       01  WS-FILE-STATUS                PIC XX VALUE SPACES.

      *> Safe defaults for error cases
       01  WS-SAFE-DEFAULTS.
           05  WS-SAFE-NAME              PIC X(50)
               VALUE "UNKNOWN".
           05  WS-SAFE-BALANCE           PIC 9(10)V99 VALUE 0.
           05  WS-SAFE-TXN-COUNT         PIC 9(8) VALUE 0.
           05  WS-SAFE-AVG-MONTHLY       PIC 9(8)V99 VALUE 0.
           05  WS-SAFE-RISK-SCORE        PIC 9(3) VALUE 0.
           05  WS-SAFE-LAST-DATE         PIC X(10) VALUE "0000-00-00".

       PROCEDURE DIVISION.
       MAIN-PROCEDURE.
           DISPLAY "========================================".
           DISPLAY "CUSTOMER 360° LOOKUP".
           DISPLAY "========================================".

      *> Accept customer ID from command line
           ACCEPT WS-CUSTOMER-ID FROM COMMAND-LINE.

      *> Validate input
           IF WS-CUSTOMER-ID = SPACES
               DISPLAY "ERROR: Missing customer ID"
               DISPLAY "Usage: CUSTOMER-LOOKUP <customer_id>"
               MOVE 1 TO RETURN-CODE
               STOP RUN
           END-IF.

      *> Build command to invoke Python script
      *> Windows-compatible: python script > file 2>nul
      *> (Note: timeout not used for Windows compatibility)
           STRING
               "python python/customer_360.py "
               DELIMITED BY SIZE
               WS-CUSTOMER-ID DELIMITED BY SPACE
               " > cust-response.dat 2>nul"
               DELIMITED BY SIZE
               INTO WS-CMD
           END-STRING.

      *> Execute Python script via system call
           DISPLAY "Calling: " WS-CMD.
           CALL "SYSTEM" USING WS-CMD.
           MOVE RETURN-CODE TO WS-CMD-RESULT.

           IF WS-CMD-RESULT NOT = 0
               IF WS-CMD-RESULT = 124
                   DISPLAY "ERROR: Request timeout (>5 seconds)"
               ELSE
                   DISPLAY "ERROR: Python script failed (code "
                       WS-CMD-RESULT ")"
               END-IF
               PERFORM SHOW-SAFE-DEFAULTS
               MOVE 1 TO RETURN-CODE
               STOP RUN
           END-IF.

      *> Open response file and read record
           OPEN INPUT RESPONSE-FILE.

           READ RESPONSE-FILE INTO WS-RAW-CUST-RESPONSE
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

      *> Parse response record using REDEFINES overlay
      *> Convert numeric string fields using FUNCTION NUMVAL()
           PERFORM PARSE-RESPONSE-RECORD.

      *> Check return code from Python
           IF FUNCTION NUMVAL(CR-RETURN-CODE-STR) = 1
               DISPLAY ""
               DISPLAY ">>> Customer not found: " WS-CUSTOMER-ID
               MOVE 1 TO RETURN-CODE
               STOP RUN
           END-IF.

           IF FUNCTION NUMVAL(CR-RETURN-CODE-STR) = 99
               DISPLAY ""
               DISPLAY ">>> ERROR: Python script returned error code"
               PERFORM SHOW-SAFE-DEFAULTS
               MOVE 1 TO RETURN-CODE
               STOP RUN
           END-IF.

      *> Display results
           PERFORM DISPLAY-CUSTOMER-RESULTS.

           MOVE 0 TO RETURN-CODE.
           STOP RUN.

       PARSE-RESPONSE-RECORD.
      *> Convert numeric string fields to COBOL numerics
           MOVE FUNCTION NUMVAL(CR-ACCT-BALANCE-STR)
               TO CR-ACCT-BALANCE.
           MOVE FUNCTION NUMVAL(CR-TXN-COUNT-STR)
               TO CR-TXN-COUNT.
           MOVE FUNCTION NUMVAL(CR-AVG-MONTHLY-STR)
               TO CR-AVG-MONTHLY.
           MOVE FUNCTION NUMVAL(CR-RISK-SCORE-STR)
               TO CR-RISK-SCORE.
           MOVE FUNCTION NUMVAL(CR-RETURN-CODE-STR)
               TO CR-RETURN-CODE.

       DISPLAY-CUSTOMER-RESULTS.
           DISPLAY "".
           DISPLAY "CUSTOMER PROFILE".
           DISPLAY "========================================".
           DISPLAY "Customer ID:    " WS-CUSTOMER-ID.
           DISPLAY "Name:           " CR-CUST-NAME.
           DISPLAY "Account Balance: $" CR-ACCT-BALANCE.
           DISPLAY "Transactions:    " CR-TXN-COUNT " total".
           DISPLAY "Avg Monthly:     $" CR-AVG-MONTHLY.
           DISPLAY "Risk Score:      " CR-RISK-SCORE " / 999".
           DISPLAY "Last Transaction:" CR-LAST-TXN-DATE.
           DISPLAY "========================================".

       SHOW-SAFE-DEFAULTS.
           DISPLAY "".
           DISPLAY "CUSTOMER PROFILE (DEFAULTS - UNAVAILABLE)".
           DISPLAY "========================================".
           DISPLAY "Customer ID:    " WS-CUSTOMER-ID.
           DISPLAY "Name:           " WS-SAFE-NAME.
           DISPLAY "Account Balance: $" WS-SAFE-BALANCE.
           DISPLAY "Transactions:    " WS-SAFE-TXN-COUNT " total".
           DISPLAY "Avg Monthly:     $" WS-SAFE-AVG-MONTHLY.
           DISPLAY "Risk Score:      " WS-SAFE-RISK-SCORE " / 999".
           DISPLAY "Last Transaction:" WS-SAFE-LAST-DATE.
           DISPLAY "========================================".
