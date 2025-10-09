import pytest
from datetime import datetime, timedelta
from library_service import return_book_by_patron, add_book_to_catalog, borrow_book_by_patron
from database import init_database, get_db_connection, get_book_by_isbn

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

def test_return_book_valid():
    """Test returning a book that was borrowed by the patron."""
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 1)
    book = get_book_by_isbn("1234567890123")
    borrow_book_by_patron("123456", book['id'])
    success, message = return_book_by_patron("123456", book['id'])
    assert success == True
    assert "successfully returned" in message.lower()

def test_return_book_invalid_patron_id_short():
    """Test returning with patron ID too short."""
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 1)
    book = get_book_by_isbn("1234567890123")
    borrow_book_by_patron("123456", book['id'])
    success, message = return_book_by_patron("12345", book['id'])
    assert success == False
    assert "exactly 6 digits" in message.lower()

def test_return_book_invalid_patron_id_long():
    """Test returning with patron ID too long."""
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 1)
    book = get_book_by_isbn("1234567890123")
    borrow_book_by_patron("123456", book['id'])
    success, message = return_book_by_patron("1234567", book['id'])
    assert success == False
    assert "exactly 6 digits" in message.lower()

def test_return_book_invalid_patron_id_non_numeric():
    """Test returning with non-numeric patron ID."""
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 1)
    book = get_book_by_isbn("1234567890123")
    borrow_book_by_patron("123456", book['id'])
    success, message = return_book_by_patron("abcdef", book['id'])
    assert success == False
    assert "exactly 6 digits" in message.lower()

def test_return_book_invalid_patron_id_empty():
    """Test returning with empty patron ID."""
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 1)
    book = get_book_by_isbn("1234567890123")
    borrow_book_by_patron("123456", book['id'])
    success, message = return_book_by_patron("", book['id'])
    assert success == False
    assert "exactly 6 digits" in message.lower()

def test_return_book_nonexistent_book():
    """Test returning a book that doesn't exist."""
    success, message = return_book_by_patron("123456", 999)
    assert success == False
    assert "book not found" in message.lower()

def test_return_book_not_borrowed_by_patron():
    """Test returning a book not borrowed by the patron."""
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 1)
    book = get_book_by_isbn("1234567890123")
    borrow_book_by_patron("123456", book['id'])
    success, message = return_book_by_patron("654321", book['id'])
    assert success == False
    assert "not borrowed by the patron" in message.lower()

def test_return_book_already_returned():
    """Test returning a book that has already been returned."""
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 1)
    book = get_book_by_isbn("1234567890123")
    borrow_book_by_patron("123456", book['id'])
    return_book_by_patron("123456", book['id'])
    success, message = return_book_by_patron("123456", book['id'])
    assert success == False
    assert "not borrowed by the patron" in message.lower()

def test_return_book_multiple_copies():
    """Test returning one copy when multiple are available."""
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 2)
    book = get_book_by_isbn("1234567890123")
    borrow_book_by_patron("123456", book['id'])
    borrow_book_by_patron("654321", book['id'])
    success, message = return_book_by_patron("123456", book['id'])
    assert success == True
    # Check that one copy is still borrowed
    from database import get_book_by_id
    updated_book = get_book_by_id(book['id'])
    assert updated_book['available_copies'] == 1