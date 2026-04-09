      *> CUSTOMER-REC.cpy
      *> Customer 360° Response Record (145 bytes total)
      *>
      *> This copybook defines the fixed-width response record returned
      *> by python/customer_360.py. The record is structured as raw bytes
      *> and then overlaid with a REDEFINES for convenient field access.
      *>
      *> Layout:
      *>   Bytes 1-50:   Customer name (PIC X(50), left-justified)
      *>   Bytes 51-62:  Account balance (PIC 9(10)V99, zero-padded)
      *>   Bytes 63-70:  Transaction count (PIC 9(8), zero-padded)
      *>   Bytes 71-80:  Average monthly spending (PIC 9(8)V99, zero-padded)
      *>   Bytes 81-83:  Risk score (PIC 9(3), 000-999)
      *>   Bytes 84-93:  Last transaction date (YYYY-MM-DD)
      *>   Bytes 94-95:  Return code (00=success, 01=not found, 99=error)
      *> Total: 145 bytes

       01  WS-RAW-CUST-RESPONSE        PIC X(145).

       01  WS-CUST-RESPONSE REDEFINES WS-RAW-CUST-RESPONSE.
           05  CR-CUST-NAME            PIC X(50).
           05  CR-ACCT-BALANCE-STR     PIC X(12).
           05  CR-TXN-COUNT-STR        PIC X(8).
           05  CR-AVG-MONTHLY-STR      PIC X(10).
           05  CR-RISK-SCORE-STR       PIC X(3).
           05  CR-LAST-TXN-DATE        PIC X(10).
           05  CR-RETURN-CODE-STR      PIC X(2).
           05  CR-RESERVED             PIC X(50).

      *> Working storage for numeric conversions
       01  WS-CUST-RESPONSE-NUMERIC.
           05  CR-ACCT-BALANCE         PIC 9(10)V99 VALUE 0.
           05  CR-TXN-COUNT            PIC 9(8) VALUE 0.
           05  CR-AVG-MONTHLY          PIC 9(8)V99 VALUE 0.
           05  CR-RISK-SCORE           PIC 9(3) VALUE 0.
           05  CR-RETURN-CODE          PIC 99 VALUE 99.
