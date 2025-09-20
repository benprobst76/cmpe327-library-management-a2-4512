import pytest
from datetime import datetime, timedelta
from library_service import (
    borrow_book_by_patron, add_book_to_catalog
)
from database import init_database, get_db_connection, get_book_by_isbn

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

def test_borrow_book_valid_patron_and_book():
    """Test borrowing a book with valid patron ID and available book."""
    # Add a book first
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 5)
    # get book id
    book_id = get_book_by_isbn("1234567890123")['id']
    success, message = borrow_book_by_patron("123456", book_id)
    
    assert success == True
    assert "successfully borrowed" in message.lower()
    assert "due date:" in message.lower()

def test_borrow_book_invalid_patron_id_too_short():
    """Test borrowing with patron ID too short."""
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 5)
    
    success, message = borrow_book_by_patron("12345", 1)
    
    assert success == False
    assert "exactly 6 digits" in message

def test_borrow_book_nonexistent_book():
    """Test borrowing a book that doesn't exist."""
    success, message = borrow_book_by_patron("123456", 999)
    
    assert success == False
    assert "book not found" in message.lower()

def test_borrow_book_unavailable_book():
    """Test borrowing a book with no available copies."""
    # Add a book with 1 available copy
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 1)
    # Borrow it first to make it unavailable
    book_id = get_book_by_isbn("1234567890123")['id']
    borrow_book_by_patron("123456", book_id)
    # Try to borrow again
    success, message = borrow_book_by_patron("654321", book_id)

    assert success == False
    assert "not available" in message.lower()

def test_borrow_book_patron_at_limit():
    """Test borrowing when patron has reached the 5-book limit."""
    # Add 6 books
    for i in range(6):
        isbn = f"123456789012{i}"
        add_book_to_catalog(f"Test Book {i+1}", "Test Author", isbn, 1)
    
    patron_id = "123456"
    
    # Borrow 5 books successfully
    for i in range(5):
        book_id = get_book_by_isbn(f"123456789012{i}")['id']
        success, message = borrow_book_by_patron(patron_id, book_id)
        assert success == True
    
    # Try to borrow the 6th book
    book_id = get_book_by_isbn("1234567890125")['id']
    success, message = borrow_book_by_patron(patron_id, book_id)

    assert success == False
    assert "maximum borrowing limit" in message.lower()