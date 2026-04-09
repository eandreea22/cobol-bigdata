       IDENTIFICATION DIVISION.
       PROGRAM-ID. FRAUD-CHECK.
       AUTHOR. Thesis Project.

      *> FRAUD-CHECK.cbl
      *> Real-Time Fraud Detection Program
      *>
      *> Accepts transaction details and returns fraud risk assessment,
      *> score, detected flags, and recommended action.
      *>
      *> Invocation: FRAUD-CHECK <customer_id> <amount> <mcc> <location>
      *>                         <timestamp> <channel>
      *> Example: ./fraud-check C-00001 500 5411 Bucharest
      *>          2025-01-15T14:30:00 POS
      *>
      *> IPC Pattern:
      *>   1. Accept 6 CLI parameters
      *>   2. CALL "SYSTEM" invokes python/fraud_detect.py
      *>   3. Python writes 78-byte record to /tmp/fraud-response.dat
      *>   4. COBOL reads and parses response
      *>   5. Display fraud assessment or error

       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT RESPONSE-FILE ASSIGN TO "fraud-response.dat"
               ORGANIZATION IS LINE SEQUENTIAL.

       DATA DIVISION.
       FILE SECTION.
       FD  RESPONSE-FILE.
       01  RESPONSE-RECORD               PIC X(79).

       WORKING-STORAGE SECTION.
      *> Include copybook for response record structure
           COPY "FRAUD-REC.cpy".

      *> Input parameters
       01  WS-CUSTOMER-ID                PIC X(10) VALUE SPACES.
       01  WS-TXN-AMOUNT                 PIC 9(8)V99 VALUE 0.
       01  WS-MERCHANT-CAT               PIC X(4) VALUE SPACES.
       01  WS-TXN-LOCATION               PIC X(20) VALUE SPACES.
       01  WS-TXN-TIMESTAMP              PIC X(19) VALUE SPACES.
       01  WS-TXN-CHANNEL                PIC X(3) VALUE SPACES.

      *> String versions for CLI passing
       01  WS-AMOUNT-STR                 PIC X(15) VALUE SPACES.

      *> Command line and execution
       01  WS-CMD                        PIC X(400) VALUE SPACES.
       01  WS-CMD-RESULT                 PIC 9(4) VALUE 0.

      *> Safe defaults for error cases
       01  WS-SAFE-DEFAULTS.
           05  WS-SAFE-RISK              PIC X(6) VALUE "UNKNOW".
           05  WS-SAFE-SCORE             PIC 9(3) VALUE 50.
           05  WS-SAFE-FLAGS             PIC X(60) VALUE
               "SYSTEM_ERROR".
           05  WS-SAFE-RECOMMEND         PIC X(7) VALUE "REVIEW ".

       PROCEDURE DIVISION.
       MAIN-PROCEDURE.
           DISPLAY "========================================".
           DISPLAY "FRAUD DETECTION ASSESSMENT".
           DISPLAY "========================================".

      *> Accept parameters from command line
           ACCEPT WS-CUSTOMER-ID FROM COMMAND-LINE.

      *> Validate input
           IF WS-CUSTOMER-ID = SPACES
               DISPLAY "ERROR: Missing parameters"
               DISPLAY "Usage: FRAUD-CHECK <id> <amount> <mcc> "
                   "<location> <timestamp> <channel>"
               MOVE 1 TO RETURN-CODE
               STOP RUN
           END-IF.

      *> TODO: Parse additional parameters
      *> For demo, using default transaction values
           MOVE 500 TO WS-TXN-AMOUNT.
           MOVE "5411" TO WS-MERCHANT-CAT.
           MOVE "Bucharest" TO WS-TXN-LOCATION.
           MOVE "2025-01-15T14:30:00" TO WS-TXN-TIMESTAMP.
           MOVE "POS" TO WS-TXN-CHANNEL.

      *> Convert numerics to strings for CLI
           MOVE WS-TXN-AMOUNT TO WS-AMOUNT-STR.

      *> Build command to invoke Python script
      *> Windows-compatible: python script > file 2>nul
      *> Note: timestamp wrapped in double quotes for Windows cmd parsing
           STRING
               "python python/fraud_detect.py "
               DELIMITED BY SIZE
               WS-CUSTOMER-ID DELIMITED BY SPACE
               " "
               DELIMITED BY SIZE
               WS-AMOUNT-STR DELIMITED BY SPACE
               " "
               DELIMITED BY SIZE
               WS-MERCHANT-CAT DELIMITED BY SPACE
               " "
               DELIMITED BY SIZE
               WS-TXN-LOCATION DELIMITED BY SPACE
               " """
               DELIMITED BY SIZE
               WS-TXN-TIMESTAMP DELIMITED BY SPACE
               """ "
               DELIMITED BY SIZE
               WS-TXN-CHANNEL DELIMITED BY SPACE
               " > fraud-response.dat 2>nul"
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

           READ RESPONSE-FILE INTO WS-RAW-FRAUD-RESPONSE
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
           IF FUNCTION NUMVAL(FR-RETURN-CODE-STR) = 99
               DISPLAY ""
               DISPLAY ">>> ERROR: Python script returned error code"
               PERFORM SHOW-SAFE-DEFAULTS
               MOVE 1 TO RETURN-CODE
               STOP RUN
           END-IF.

      *> Display results
           PERFORM DISPLAY-FRAUD-RESULTS.

           MOVE 0 TO RETURN-CODE.
           STOP RUN.

       PARSE-RESPONSE-RECORD.
      *> Convert numeric string fields
           MOVE FUNCTION NUMVAL(FR-FRAUD-SCORE-STR)
               TO FR-FRAUD-SCORE.
           MOVE FUNCTION NUMVAL(FR-RETURN-CODE-STR)
               TO FR-RETURN-CODE.

       DISPLAY-FRAUD-RESULTS.
           DISPLAY "".
           DISPLAY "FRAUD DETECTION ASSESSMENT".
           DISPLAY "========================================".
           DISPLAY "Customer ID:     " WS-CUSTOMER-ID.
           DISPLAY "Transaction Amt: $" WS-TXN-AMOUNT.
           DISPLAY "Merchant Category:" WS-MERCHANT-CAT.
           DISPLAY "Location:        " WS-TXN-LOCATION.
           DISPLAY "Timestamp:       " WS-TXN-TIMESTAMP.
           DISPLAY "Channel:         " WS-TXN-CHANNEL.
           DISPLAY "".
           DISPLAY "FRAUD ASSESSMENT".
           DISPLAY "----------------------------------------".
           DISPLAY "Risk Level:      " FR-FRAUD-RISK.
           DISPLAY "Fraud Score:     " FR-FRAUD-SCORE " (0-100)".

           IF FR-FRAUD-FLAGS NOT = SPACES
               DISPLAY "Detected Flags:  " FR-FRAUD-FLAGS
           END-IF.

           DISPLAY "Recommendation:  " FR-RECOMMEND.
           DISPLAY "========================================".

       SHOW-SAFE-DEFAULTS.
           DISPLAY "".
           DISPLAY "FRAUD DETECTION ASSESSMENT (ERROR)".
           DISPLAY "========================================".
           DISPLAY "Customer ID:     " WS-CUSTOMER-ID.
           DISPLAY "Transaction Amt: $" WS-TXN-AMOUNT.
           DISPLAY "Merchant Category:" WS-MERCHANT-CAT.
           DISPLAY "Location:        " WS-TXN-LOCATION.
           DISPLAY "Timestamp:       " WS-TXN-TIMESTAMP.
           DISPLAY "Channel:         " WS-TXN-CHANNEL.
           DISPLAY "".
           DISPLAY "FRAUD ASSESSMENT (DEFAULTS)".
           DISPLAY "----------------------------------------".
           DISPLAY "Risk Level:      " WS-SAFE-RISK.
           DISPLAY "Fraud Score:     " WS-SAFE-SCORE " (0-100)".
           DISPLAY "Detected Flags:  " WS-SAFE-FLAGS.
           DISPLAY "Recommendation:  " WS-SAFE-RECOMMEND.
           DISPLAY "========================================".
