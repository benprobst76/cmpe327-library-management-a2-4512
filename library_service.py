"""
Library Service Module - Business Logic Functions
Contains all the core business logic for the Library Management System
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from database import (
    get_book_by_id, get_book_by_isbn, get_patron_borrow_count,
    insert_book, insert_borrow_record, update_book_availability,
    update_borrow_record_return_date, get_all_books, get_patron_borrowed_books, get_db_connection
)

def add_book_to_catalog(title: str, author: str, isbn: str, total_copies: int) -> Tuple[bool, str]:
    """
    Add a new book to the catalog.
    Implements R1: Book Catalog Management
    
    Args:
        title: Book title (max 200 chars)
        author: Book author (max 100 chars)
        isbn: 13-digit ISBN
        total_copies: Number of copies (positive integer)
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Input validation
    if not title or not title.strip():
        return False, "Title is required."
    
    if len(title.strip()) > 200:
        return False, "Title must be less than 200 characters."
    
    if not author or not author.strip():
        return False, "Author is required."
    
    if len(author.strip()) > 100:
        return False, "Author must be less than 100 characters."
    
    if len(isbn) != 13:
        return False, "ISBN must be exactly 13 digits."
    
    if not isinstance(total_copies, int) or total_copies <= 0:
        return False, "Total copies must be a positive integer."
    
    # Check for duplicate ISBN
    existing = get_book_by_isbn(isbn)
    if existing:
        return False, "A book with this ISBN already exists."
    
    # Insert new book
    success = insert_book(title.strip(), author.strip(), isbn, total_copies, total_copies)
    if success:
        return True, f'Book "{title.strip()}" has been successfully added to the catalog.'
    else:
        return False, "Database error occurred while adding the book."

def borrow_book_by_patron(patron_id: str, book_id: int) -> Tuple[bool, str]:
    """
    Allow a patron to borrow a book.
    Implements R3 as per requirements  
    
    Args:
        patron_id: 6-digit library card ID
        book_id: ID of the book to borrow
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits."
    
    # Check if book exists and is available
    book = get_book_by_id(book_id)
    if not book:
        return False, "Book not found."
    
    if book['available_copies'] <= 0:
        return False, "This book is currently not available."
    
    # Check patron's current borrowed books count
    current_borrowed = get_patron_borrow_count(patron_id)
    
    if current_borrowed >= 5:
        return False, "You have reached the maximum borrowing limit of 5 books."
    
    # Create borrow record
    borrow_date = datetime.now()
    due_date = borrow_date + timedelta(days=14)
    
    # Insert borrow record and update availability
    borrow_success = insert_borrow_record(patron_id, book_id, borrow_date, due_date)
    if not borrow_success:
        return False, "Database error occurred while creating borrow record."
    
    availability_success = update_book_availability(book_id, -1)
    if not availability_success:
        return False, "Database error occurred while updating book availability."
    
    return True, f'Successfully borrowed "{book["title"]}". Due date: {due_date.strftime("%Y-%m-%d")}.'

def return_book_by_patron(patron_id: str, book_id: int) -> Tuple[bool, str]:
    """
    Process book return by a patron.
    
    """
    # Validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits."

    # Check if book exists
    book = get_book_by_id(book_id)
    if not book:
        return False, "Book not found."

    # Check if the book is currently borrowed by the patron
    borrow_record = get_patron_borrowed_books(patron_id)
    borrow_record = next((record for record in borrow_record if record['book_id'] == book_id), None)
    if not borrow_record:
        return False, "This book is not borrowed by the patron."
    # update borrow record and update availability
    delete_success = update_borrow_record_return_date(patron_id, book_id, datetime.now())
    if not delete_success:
        return False, "Database error occurred while updating borrow record."

    availability_success = update_book_availability(book_id, 1)
    if not availability_success:
        return False, "Database error occurred while updating book availability."

    return True, f'Successfully returned "{book["title"]}".'

def calculate_late_fee_for_book(patron_id: str, book_id: int) -> Dict:
    """
    Calculate late fees for a specific book.

    """
    # Validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return {
            'fee_amount': 0.00,
            'days_overdue': 0,
            'status': 'invalid patron ID'
        }

    # Check if book exists
    book = get_book_by_id(book_id)
    if not book:
        return {
            'fee_amount': 0.00,
            'days_overdue': 0,
            'status': 'invalid book ID'
        }

    # Check if the book is currently borrowed by the patron
    borrow_record = get_patron_borrowed_books(patron_id)
    borrow_record = next((record for record in borrow_record if record['book_id'] == book_id), None)
    if not borrow_record:
        return {
            'fee_amount': 0.00,
            'days_overdue': 0,
            'status': 'no borrow record'
        }
    
    if borrow_record['is_overdue']:
        # Calculate late fee with tiered rates
        days_overdue = (datetime.now() - datetime.strptime(borrow_record['due_date'], '%Y-%m-%d')).days
        days_overdue = max(0, days_overdue)
        if days_overdue <= 7:
            fee_amount = days_overdue * 0.50
        else:
            fee_amount = (7 * 0.50) + ((days_overdue - 7) * 1.00)
        fee_amount = min(fee_amount, 15.00)
        return {
            'fee_amount': fee_amount,
            'days_overdue': days_overdue,
            'status': 'overdue'
        }
    return {
        'fee_amount': 0.00,
        'days_overdue': 0,
        'status': 'on time'
    }

def search_books_in_catalog(search_term: str, search_type: str) -> List[Dict]:
    """
    Search for books in the catalog.
    
    Supports:
    - Partial, case-insensitive matching for title and author
    - Exact matching for ISBN
    - Returns results in same format as get_all_books()
    """

    # Basic validation
    if not search_term or not isinstance(search_term, str):
        return []
    if not search_type or not isinstance(search_type, str):
        return []

    search_term = search_term.strip()
    search_type = search_type.strip().lower()

    if search_type not in ("title", "author", "isbn"):
        return []

    # ISBN: exact match
    if search_type == "isbn":
        book = get_book_by_isbn(search_term)
        return [book] if book else []

    # Title/Author: partial, case-insensitive match
    all_books = get_all_books()
    term_lower = search_term.lower()
    results: List[Dict] = []

    for book in all_books:
        value = (book.get(search_type) or "").lower()
        if term_lower in value:
            results.append(book)

    return results

def get_patron_status_report(patron_id: str) -> Dict:
    """
    Get status report for a patron.

    Returns a dictionary with:
    - currently_borrowed: list of currently borrowed books with title, author, due_date
    - total_late_fees: total late fees owed (sum of overdue fees, rounded to 2 decimals)
    - books_borrowed_count: number of books currently borrowed
    - borrowing_history: list of all borrow records (past and present) with dates and fees incurred
    """
    # Validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return {'error': 'Invalid patron ID. Must be exactly 6 digits.'}

    # Currently borrowed books (uses database helper which returns datetime objects)
    current_records = get_patron_borrowed_books(patron_id)
    currently_borrowed = []
    for rec in current_records:
        currently_borrowed.append({
            'book_id': rec['book_id'],
            'title': rec['title'],
            'author': rec['author'],
            'due_date': rec['due_date'].strftime('%Y-%m-%d') if hasattr(rec['due_date'], 'strftime') else str(rec['due_date'])
        })

    books_borrowed_count = get_patron_borrow_count(patron_id)

    # Build borrowing history and compute total late fees
    conn = get_db_connection()
    rows = conn.execute('''
        SELECT br.*, b.title, b.author
        FROM borrow_records br
        JOIN books b ON br.book_id = b.id
        WHERE br.patron_id = ?
        ORDER BY br.borrow_date
    ''', (patron_id,)).fetchall()
    conn.close()

    borrowing_history = []
    total_late_fees = 0.0
    now = datetime.now()

    for r in rows:
        borrow_date = datetime.fromisoformat(r['borrow_date'])
        due_date = datetime.fromisoformat(r['due_date'])
        return_date = datetime.fromisoformat(r['return_date']) if r['return_date'] else None

        # Determine the date to compare for overdue calculation
        compare_date = return_date if return_date else now
        days_overdue = max(0, (compare_date - due_date).days)

        # Calculate fee using same tiered logic as calculate_late_fee_for_book
        fee = 0.0
        if days_overdue > 0:
            if days_overdue <= 7:
                fee = days_overdue * 0.50
            else:
                fee = (7 * 0.50) + ((days_overdue - 7) * 1.00)
            fee = min(fee, 15.00)

        # Only outstanding overdue fees are considered currently owed,
        # Since the system does not track payments, treat all computed fees as owed.
        total_late_fees += fee

        borrowing_history.append({
            'book_id': r['book_id'],
            'title': r['title'],
            'author': r['author'],
            'borrow_date': borrow_date.strftime('%Y-%m-%d'),
            'due_date': due_date.strftime('%Y-%m-%d'),
            'return_date': return_date.strftime('%Y-%m-%d') if return_date else None,
            'fee_incurred': round(fee, 2)
        })

    total_late_fees = round(total_late_fees, 2)

    return {
        'currently_borrowed': currently_borrowed,
        'total_late_fees': total_late_fees,
        'books_borrowed_count': books_borrowed_count,
        'borrowing_history': borrowing_history
    }
