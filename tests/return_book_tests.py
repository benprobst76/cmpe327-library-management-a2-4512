import pytest
from datetime import datetime, timedelta
from library_service import (
    return_book_by_patron, borrow_book_by_patron, add_book_to_catalog
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

def test_return_book_valid_patron_and_book():
    """Test returning a book with valid patron ID and borrowed book."""
    # Add a book and borrow it first
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 5)
    book_id = get_book_by_isbn("1234567890123")['id']
    borrow_book_by_patron("123456", book_id)

    success, message = return_book_by_patron("123456", book_id)

    assert success == True
    assert "returned successfully" in message.lower()

def test_return_book_nonexistent_book():
    """Test returning a book that doesn't exist."""
    success, message = return_book_by_patron("123456", 999)
    
    assert success == False
    assert "book not found" in message.lower()

def test_return_book_not_borrowed_by_patron():
    """Test returning a book that wasn't borrowed by the patron."""
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 5)
    book_id = get_book_by_isbn("1234567890123")['id']
    # Borrow with different patron
    borrow_book_by_patron("654321", book_id)

    # Try to return with different patron
    success, message = return_book_by_patron("123456", book_id)
    
    assert success == False
    assert "not borrowed by the patron" in message.lower() or "already been returned" in message.lower()

def test_return_book_already_returned():
    """Test returning a book that has already been returned."""
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 1)
    book_id = get_book_by_isbn("1234567890123")['id']
    borrow_book_by_patron("123456", book_id)
    return_book_by_patron("123456", book_id)  # First return

    # Try to return again
    success, message = return_book_by_patron("123456", book_id)

    assert success == False
    assert "not borrowed by the patron" in message.lower() or "already been returned" in message.lower()

def test_return_book_with_late_fee():
    """Test returning an overdue book with late fees."""
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 5)
    book_id = get_book_by_isbn("1234567890123")['id']
    borrow_book_by_patron("123456", book_id)

    # Manipulate the borrow date to be > 14 days ago
    conn = get_db_connection()
    overdue_date = (datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d')
    conn.execute("UPDATE borrow_records SET borrow_date = ? WHERE patron_id = ? AND book_id = ?",
                 (overdue_date, "123456", book_id))
    conn.commit()
    conn.close()
    success, message = return_book_by_patron("123456", book_id)

    assert success == True
    assert "returned successfully" in message.lower()
