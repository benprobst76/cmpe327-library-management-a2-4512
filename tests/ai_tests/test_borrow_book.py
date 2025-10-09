import pytest
from datetime import datetime, timedelta
from library_service import borrow_book_by_patron, add_book_to_catalog
from database import init_database, get_db_connection, get_book_by_isbn, get_patron_borrow_count

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

def test_borrow_book_valid():
    """Test borrowing a book with valid patron ID and available book."""
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 5)
    book = get_book_by_isbn("1234567890123")
    success, message = borrow_book_by_patron("123456", book['id'])
    assert success == True
    assert "successfully borrowed" in message.lower()
    assert "due date" in message.lower()

def test_borrow_book_invalid_patron_id_short():
    """Test borrowing with patron ID too short."""
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 5)
    book = get_book_by_isbn("1234567890123")
    success, message = borrow_book_by_patron("12345", book['id'])
    assert success == False
    assert "exactly 6 digits" in message.lower()

def test_borrow_book_invalid_patron_id_long():
    """Test borrowing with patron ID too long."""
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 5)
    book = get_book_by_isbn("1234567890123")
    success, message = borrow_book_by_patron("1234567", book['id'])
    assert success == False
    assert "exactly 6 digits" in message.lower()

def test_borrow_book_invalid_patron_id_non_numeric():
    """Test borrowing with non-numeric patron ID."""
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 5)
    book = get_book_by_isbn("1234567890123")
    success, message = borrow_book_by_patron("abcdef", book['id'])
    assert success == False
    assert "exactly 6 digits" in message.lower()

def test_borrow_book_invalid_patron_id_empty():
    """Test borrowing with empty patron ID."""
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 5)
    book = get_book_by_isbn("1234567890123")
    success, message = borrow_book_by_patron("", book['id'])
    assert success == False
    assert "exactly 6 digits" in message.lower()

def test_borrow_book_nonexistent_book():
    """Test borrowing a book that doesn't exist."""
    success, message = borrow_book_by_patron("123456", 999)
    assert success == False
    assert "book not found" in message.lower()

def test_borrow_book_unavailable():
    """Test borrowing a book with no available copies."""
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 1)
    book = get_book_by_isbn("1234567890123")
    # Borrow once
    borrow_book_by_patron("123456", book['id'])
    # Try to borrow again
    success, message = borrow_book_by_patron("654321", book['id'])
    assert success == False
    assert "not available" in message.lower()

def test_borrow_book_patron_at_limit():
    """Test borrowing when patron has reached the limit of 5 books."""
    # Add 5 books
    for i in range(5):
        add_book_to_catalog(f"Book {i}", "Author", f"123456789012{i}", 1)
    # Borrow 5 books
    for i in range(5):
        book = get_book_by_isbn(f"123456789012{i}")
        borrow_book_by_patron("123456", book['id'])
    # Add another book
    add_book_to_catalog("Book 6", "Author", "1234567890125", 1)
    book = get_book_by_isbn("1234567890125")
    success, message = borrow_book_by_patron("123456", book['id'])
    assert success == False
    assert "maximum borrowing limit" in message.lower()

def test_borrow_book_same_book_twice():
    """Test borrowing the same book twice by the same patron."""
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 2)
    book = get_book_by_isbn("1234567890123")
    # Borrow once
    borrow_book_by_patron("123456", book['id'])
    # Try to borrow again
    success, message = borrow_book_by_patron("123456", book['id'])
    assert success == False
    assert "already borrowed" in message.lower()

def test_borrow_book_different_patrons():
    """Test borrowing the same book by different patrons."""
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 2)
    book = get_book_by_isbn("1234567890123")
    # Borrow by first patron
    success1, _ = borrow_book_by_patron("123456", book['id'])
    # Borrow by second patron
    success2, _ = borrow_book_by_patron("654321", book['id'])
    assert success1 == True
    assert success2 == True