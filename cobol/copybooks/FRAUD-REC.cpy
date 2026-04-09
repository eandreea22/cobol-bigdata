      *> FRAUD-REC.cpy
      *> Fraud Detection Response Record (78 bytes total)
      *>
      *> This copybook defines the fixed-width response record returned
      *> by python/fraud_detect.py. The record is structured as raw bytes
      *> and then overlaid with a REDEFINES for convenient field access.
      *>
      *> Layout:
      *>   Bytes 1-6:    Fraud risk level (PIC X(6), "LOW   ", "MEDIUM", "HIGH  ")
      *>   Bytes 7-9:    Fraud score (PIC 9(3), 0-100, zero-padded)
      *>   Bytes 10-69:  Fraud flags (PIC X(60), comma-separated list of anomalies)
      *>   Bytes 70-76:  Recommendation (PIC X(7), "APPROVE", "REVIEW ", "DECLINE")
      *>   Bytes 77-78:  Return code (PIC 99, 00=success, 99=error)
      *> Total: 78 bytes

       01  WS-RAW-FRAUD-RESPONSE       PIC X(78).

       01  WS-FRAUD-RESPONSE REDEFINES WS-RAW-FRAUD-RESPONSE.
           05  FR-FRAUD-RISK           PIC X(6).
           05  FR-FRAUD-SCORE-STR      PIC X(3).
           05  FR-FRAUD-FLAGS          PIC X(60).
           05  FR-RECOMMEND            PIC X(7).
           05  FR-RETURN-CODE-STR      PIC X(2).

      *> Working storage for numeric conversions
       01  WS-FRAUD-RESPONSE-NUMERIC.
           05  FR-FRAUD-SCORE          PIC 9(3) VALUE 0.
           05  FR-RETURN-CODE          PIC 99 VALUE 99.
