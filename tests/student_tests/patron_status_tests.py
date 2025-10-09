import pytest
from datetime import datetime, timedelta
from library_service import (
    get_patron_status_report, borrow_book_by_patron, return_book_by_patron, add_book_to_catalog, get_book_by_isbn
)
from database import init_database, get_db_connection

# Fixture to ensure clean database for each test
@pytest.fixture(autouse=True)
def setup_database():
    """Initialize database before each test."""
    init_database()
    # Clear existing data
    conn = get_db_connection()
    conn.execute('DELETE FROM borrow_records')
    conn.execute('DELETE FROM books')
    conn.commit()
    conn.close()

def setup_sample_books():
    """Helper function to set up sample books for testing."""
    add_book_to_catalog("The Great Gatsby", "F. Scott Fitzgerald", "9780743273565", 3)
    add_book_to_catalog("To Kill a Mockingbird", "Harper Lee", "9780061120084", 2)
    add_book_to_catalog("1984", "George Orwell", "9780451524935", 1)
    add_book_to_catalog("Animal Farm", "George Orwell", "9780451526342", 2)

def test_patron_status_valid_patron_id():
    """Test getting patron status with valid patron ID."""
    setup_sample_books()
    
    result = get_patron_status_report("123456")
    
    assert isinstance(result, dict)
    # Should have the required fields for patron status
    expected_fields = ['currently_borrowed', 'total_late_fees', 'books_borrowed_count', 'borrowing_history']
    for field in expected_fields:
        assert field in result

def test_patron_status_patron_with_no_borrowing_history():
    """Test patron status for patron with no borrowing history."""
    setup_sample_books()
    
    result = get_patron_status_report("123456")
    
    # Check all expected fields exist and their values are 0 or empty
    expected_fields = ['currently_borrowed', 'total_late_fees', 'books_borrowed_count', 'borrowing_history']
    for field in expected_fields:
        assert field in result

    assert result['books_borrowed_count'] == 0
    assert result['total_late_fees'] == 0.00
    assert isinstance(result['currently_borrowed'], list) and len(result['currently_borrowed']) == 0
    assert isinstance(result['borrowing_history'], list) and len(result['borrowing_history']) == 0

def test_patron_status_patron_with_currently_borrowed_books():
    """Test patron status for patron with currently borrowed books."""
    setup_sample_books()
    # Borrow some books
    book1 = get_book_by_isbn("9780743273565")
    assert book1 is not None, "Book with ISBN 9780743273565 not found in catalog"
    borrow_book_by_patron("123456", book1['id'])
    book2 = get_book_by_isbn("9780061120084")
    assert book2 is not None, "Book with ISBN 9780061120084 not found in catalog"
    borrow_book_by_patron("123456", book2['id'])

    result = get_patron_status_report("123456")

    expected_fields = ['currently_borrowed', 'total_late_fees', 'books_borrowed_count', 'borrowing_history']
    for field in expected_fields:
        assert field in result
    
    assert isinstance(result, dict)
    assert result['books_borrowed_count'] == 2
    assert len(result['currently_borrowed']) == 2
    # Each borrowed book should have title, author, due_date
    for book in result['currently_borrowed']:
            assert 'title' in book
            assert 'author' in book
            assert 'due_date' in book

def test_patron_status_patron_with_returned_books():
    """Test patron status for patron who has returned books."""
    setup_sample_books()
    book_id = get_book_by_isbn("9780743273565")
    assert book_id is not None, "Book with ISBN 9780743273565 not found in catalog"
    # Borrow and return a book
    borrow_book_by_patron("123456", book_id['id'])
    return_book_by_patron("123456", book_id['id'])

    result = get_patron_status_report("123456")
    
    expected_fields = ['currently_borrowed', 'total_late_fees', 'books_borrowed_count', 'borrowing_history']
    for field in expected_fields:
        assert field in result

    assert isinstance(result, dict)
    assert result['books_borrowed_count'] == 0  
    assert isinstance(result['borrowing_history'], list)
    assert len(result['borrowing_history']) == 1

def test_patron_status_patron_with_late_fees():
    """Test patron status for patron with late fees."""
    setup_sample_books()

    book_id_1 = get_book_by_isbn("9780743273565")
    assert book_id_1 is not None, "Book with ISBN 9780743273565 not found in catalog"
    book_id_2 = get_book_by_isbn("9780061120084")
    assert book_id_2 is not None, "Book with ISBN 9780061120084 not found in catalog"
    borrow_book_by_patron("123456", book_id_1['id'])
    borrow_book_by_patron("123456", book_id_2['id'])

    result = get_patron_status_report("123456")

    expected_fields = ['currently_borrowed', 'total_late_fees', 'books_borrowed_count', 'borrowing_history']
    for field in expected_fields:
        assert field in result
    
    assert isinstance(result, dict)
    assert isinstance(result['total_late_fees'], (int, float))
    assert result['total_late_fees'] >= 0.00
