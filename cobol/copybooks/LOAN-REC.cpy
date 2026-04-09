      *> LOAN-REC.cpy
      *> Loan Eligibility Response Record (51 bytes total)
      *>
      *> This copybook defines the fixed-width response record returned
      *> by python/loan_scoring.py. The record is structured as raw bytes
      *> and then overlaid with a REDEFINES for convenient field access.
      *>
      *> Layout:
      *>   Bytes 1-3:    Credit score (PIC 9(3), 300-850, zero-padded)
      *>   Byte 4:       Eligible for loan (PIC X(1), Y or N)
      *>   Bytes 5-9:    Interest rate (PIC 9V9(4), 5 chars, e.g., "04750" = 4.75%)
      *>   Bytes 10-19:  Maximum approvable amount (PIC 9(8)V99, zero-padded)
      *>   Bytes 20-49:  Rejection reason (PIC X(30), if applicable)
      *>   Bytes 50-51:  Return code (PIC 99, 00=success, 99=error)
      *> Total: 51 bytes

       01  WS-RAW-LOAN-RESPONSE        PIC X(51).

       01  WS-LOAN-RESPONSE REDEFINES WS-RAW-LOAN-RESPONSE.
           05  LR-CREDIT-SCORE-STR     PIC X(3).
           05  LR-ELIGIBLE             PIC X(1).
           05  LR-INT-RATE-STR         PIC X(5).
           05  LR-MAX-AMOUNT-STR       PIC X(10).
           05  LR-REJECT-REASON        PIC X(30).
           05  LR-RETURN-CODE-STR      PIC X(2).

      *> Working storage for numeric conversions
       01  WS-LOAN-RESPONSE-NUMERIC.
           05  LR-CREDIT-SCORE         PIC 9(3) VALUE 300.
           05  LR-INT-RATE             PIC 9V9(4) VALUE 0.
           05  LR-MAX-AMOUNT           PIC 9(8)V99 VALUE 0.
           05  LR-RETURN-CODE          PIC 99 VALUE 99.
