# Ben Probst - 20284512 - CMPE 327 Assignment 1

```
| Function | Status | Missing |
|----------|---------|----------|
| Add Book To Catalog | complete | |
| Book Catalog Display | complete | |
| Book Borrowing Interface | partial | Allows borrowing 6 books but should be 5|
| Book Return Processing | incomplete | Has UI but not implemented |
| Late Fee Calculation API | incomplete | Calculates late fees for overdue books |
| Book Search Functionality | incomplete | Has UI but not implemented |
| Patron Status Report | incomplete | All |
```

## Test Coverage

### R1: Add Book To Catalog (`tests/add_book_tests.py`)
- **5 test cases** covering:
  - Valid book addition
  - Input validation (negative copies, empty isbn, zero copies)
  - Duplicate ISBN detection

### R2: Book Catalog Display (`tests/catalog_display_tests.py`) 
- **5 test cases** covering:
  - Empty catalog display
  - Single and multiple book display
  - Alphabetical sorting by title
  - Zero available copies

### R3: Book Borrowing Interface (`tests/borrow_book_tests.py`)
- **5 test cases** covering:
  - Valid borrowing scenarios
  - Patron ID validation (6-digit format)
  - Book availability checking
  - Borrowing limit enforcement (max 5 books)

### R4: Book Return Processing (`tests/return_book_tests.py`)
- **5 test cases** covering:
  - Valid book returns
  - Patron and book validation
  - Return authorization (book must be borrowed by patron)
  - Late fee integration

### R5: Late Fee Calculation API (`tests/late_fee_tests.py`)
- **5 test cases** covering:
  - Patron ID validation
  - Overdue vs non-overdue scenarios
  - JSON response structure for API

### R6: Book Search Functionality (`tests/search_books_tests.py`)
- **5 test cases** covering:
  - Title search (exact and partial, case-insensitive)
  - ISBN search (exact match only)
  - No results handling

### R7: Patron Status Report (`tests/patron_status_tests.py`)
- **5 test cases** covering:
  - Currently borrowed books
  - Total late fees calculation
  - Books borrowed count
  - Data consistency and validation