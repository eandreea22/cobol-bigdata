       IDENTIFICATION DIVISION.
       PROGRAM-ID. CUSTOMER-UPDATE.
       AUTHOR. Thesis Project.

      *> CUSTOMER-UPDATE.cbl
      *> Customer Record Update Validation
      *>
      *> Accepts a customer ID and validates customer record fields
      *> according to business rules. Returns a 52-byte response record
      *> with validation result (00=pass, 01=fail) and message.
      *>
      *> Invocation: CUSTOMER-UPDATE <input_file>
      *> Example: ./customer-update /tmp/customer-update.dat
      *>
      *> Input file (207 bytes):
      *>   Bytes 1-7:     Customer ID (PIC X(7))
      *>   Bytes 8-57:    Name (PIC X(50))
      *>   Bytes 58-157:  Email (PIC X(100))
      *>   Bytes 158-207: City (PIC X(50))
      *>
      *> Output to stdout (52 bytes):
      *>   Bytes 1-2:   Return code (PIC XX: "00"=pass, "01"=fail)
      *>   Bytes 3-52:  Message (PIC X(50))

       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT INPUT-FILE ASSIGN TO WS-INPUT-FILENAME
               ORGANIZATION IS LINE SEQUENTIAL
               FILE STATUS IS WS-FILE-STATUS.

       DATA DIVISION.
       FILE SECTION.
       FD  INPUT-FILE.
       01  INPUT-RECORD                  PIC X(207).

       WORKING-STORAGE SECTION.

      *> Input file parameter
       01  WS-INPUT-FILENAME             PIC X(256) VALUE SPACES.
       01  WS-ARG-LENGTH                 PIC 9(4) COMP-5 VALUE 0.

      *> File status
       01  WS-FILE-STATUS                PIC XX VALUE SPACES.
       01  WS-EOF-FLAG                   PIC X VALUE "N".

      *> Input record overlay
       01  WS-INPUT-RECORD.
           05  WS-CUSTOMER-ID            PIC X(7).
           05  WS-NAME                   PIC X(50).
           05  WS-EMAIL                  PIC X(100).
           05  WS-CITY                   PIC X(50).

      *> Working variables for validation
       01  WS-TRIMMED-NAME               PIC X(50) VALUE SPACES.
       01  WS-TRIMMED-CITY               PIC X(50) VALUE SPACES.
       01  WS-NAME-LENGTH                PIC 9(4) COMP-5 VALUE 0.
       01  WS-CITY-LENGTH                PIC 9(4) COMP-5 VALUE 0.
       01  WS-EMAIL-LENGTH               PIC 9(4) COMP-5 VALUE 0.
       01  WS-AT-POS                     PIC 9(4) COMP-5 VALUE 0.
       01  WS-FOUND-AT                   PIC X VALUE "N".
       01  WS-I                          PIC 9(4) COMP-5 VALUE 0.
       01  WS-CHAR                       PIC X VALUE SPACE.

      *> Validation result
       01  WS-RETURN-CODE                PIC 99 VALUE 0.
       01  WS-MESSAGE                    PIC X(50) VALUE SPACES.

      *> Response record (52 bytes)
       01  WS-RESPONSE-RECORD.
           05  WS-RESP-CODE              PIC XX.
           05  WS-RESP-MESSAGE           PIC X(50).

       PROCEDURE DIVISION.
       MAIN-PROCEDURE.
           PERFORM INITIALIZE-PROGRAM.
           PERFORM VALIDATE-ARGUMENTS.

           IF WS-RETURN-CODE NOT = 0
               PERFORM WRITE-RESPONSE
               STOP RUN
           END-IF.

           PERFORM OPEN-INPUT-FILE.
           PERFORM READ-INPUT-RECORD.

           IF WS-RETURN-CODE NOT = 0
               PERFORM WRITE-RESPONSE
               STOP RUN
           END-IF.

           PERFORM PARSE-INPUT-RECORD.
           PERFORM VALIDATE-FIELDS.
           PERFORM WRITE-RESPONSE.
           STOP RUN.

       INITIALIZE-PROGRAM.
           ACCEPT WS-INPUT-FILENAME FROM ARGUMENT-VALUE.
           IF WS-INPUT-FILENAME = SPACES
               MOVE 99 TO WS-RETURN-CODE
               MOVE "No input file specified" TO WS-MESSAGE
           END-IF.

       VALIDATE-ARGUMENTS.
           IF WS-INPUT-FILENAME = SPACES
               MOVE 99 TO WS-RETURN-CODE
               MOVE "Missing input file argument" TO WS-MESSAGE
           END-IF.

       OPEN-INPUT-FILE.
           OPEN INPUT INPUT-FILE.
           IF WS-FILE-STATUS NOT = "00"
               MOVE 99 TO WS-RETURN-CODE
               STRING "Cannot open input file: " WS-FILE-STATUS
                   DELIMITED BY SIZE INTO WS-MESSAGE
           END-IF.

       READ-INPUT-RECORD.
           IF WS-RETURN-CODE = 0
               READ INPUT-FILE INTO WS-INPUT-RECORD
                   AT END
                       MOVE 99 TO WS-RETURN-CODE
                       MOVE "Input file is empty" TO WS-MESSAGE
                   NOT AT END
                       MOVE "N" TO WS-EOF-FLAG
               END-READ
               CLOSE INPUT-FILE
           END-IF.

       PARSE-INPUT-RECORD.
           IF WS-RETURN-CODE = 0
               MOVE WS-INPUT-RECORD(1:7) TO WS-CUSTOMER-ID
               MOVE WS-INPUT-RECORD(8:50) TO WS-NAME
               MOVE WS-INPUT-RECORD(58:100) TO WS-EMAIL
               MOVE WS-INPUT-RECORD(158:50) TO WS-CITY
           END-IF.

       VALIDATE-FIELDS.
           IF WS-RETURN-CODE NOT = 0
               EXIT PARAGRAPH
           END-IF.

      *> Validation 1: Customer ID must start with "C-"
           IF WS-CUSTOMER-ID(1:2) NOT = "C-"
               MOVE 01 TO WS-RETURN-CODE
               MOVE "Customer ID must start with C-" TO WS-MESSAGE
               EXIT PARAGRAPH
           END-IF.

      *> Validation 2: Name length (≥ 2 after trim)
           MOVE FUNCTION TRIM(WS-NAME) TO WS-TRIMMED-NAME.
           MOVE FUNCTION LENGTH(FUNCTION TRIM(WS-NAME))
               TO WS-NAME-LENGTH.
           IF WS-NAME-LENGTH < 2
               MOVE 01 TO WS-RETURN-CODE
               MOVE "Name must be at least 2 characters" TO WS-MESSAGE
               EXIT PARAGRAPH
           END-IF.

      *> Validation 3: Email must contain @ character
           PERFORM FIND-AT-SIGN.
           IF WS-FOUND-AT = "N"
               MOVE 01 TO WS-RETURN-CODE
               MOVE "Email must contain @ character" TO WS-MESSAGE
               EXIT PARAGRAPH
           END-IF.

      *> Validation 4: City length (≥ 1 after trim)
           MOVE FUNCTION TRIM(WS-CITY) TO WS-TRIMMED-CITY.
           MOVE FUNCTION LENGTH(FUNCTION TRIM(WS-CITY))
               TO WS-CITY-LENGTH.
           IF WS-CITY-LENGTH < 1
               MOVE 01 TO WS-RETURN-CODE
               MOVE "City cannot be blank" TO WS-MESSAGE
               EXIT PARAGRAPH
           END-IF.

      *> All validations passed
           MOVE 00 TO WS-RETURN-CODE.
           MOVE "Validation passed" TO WS-MESSAGE.

       FIND-AT-SIGN.
           MOVE "N" TO WS-FOUND-AT.
           PERFORM VARYING WS-I FROM 1 BY 1
               UNTIL WS-I > 100 OR WS-FOUND-AT = "Y"
               MOVE WS-EMAIL(WS-I:1) TO WS-CHAR
               IF WS-CHAR = "@"
                   MOVE "Y" TO WS-FOUND-AT
               END-IF
           END-PERFORM.

       WRITE-RESPONSE.
      *> Format return code
           IF WS-RETURN-CODE = 0
               MOVE "00" TO WS-RESP-CODE
           ELSE
               MOVE "01" TO WS-RESP-CODE
           END-IF.

      *> Format message (max 50 chars)
           IF WS-MESSAGE NOT = SPACES
               STRING WS-MESSAGE DELIMITED BY SIZE
                   INTO WS-RESP-MESSAGE
               END-STRING
           ELSE
               MOVE SPACES TO WS-RESP-MESSAGE
           END-IF.

      *> Write 52-byte response to stdout
           DISPLAY WS-RESPONSE-RECORD NO ADVANCING.
