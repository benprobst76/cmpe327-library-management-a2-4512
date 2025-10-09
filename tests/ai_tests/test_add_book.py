import pytest
from library_service import add_book_to_catalog
from database import init_database, get_db_connection

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

def test_add_book_valid_input():
    """Test adding a book with all valid inputs."""
    success, message = add_book_to_catalog("The Great Gatsby", "F. Scott Fitzgerald", "9780743273565", 3)
    assert success == True
    assert "successfully added" in message.lower()

def test_add_book_title_empty():
    """Test adding a book with empty title."""
    success, message = add_book_to_catalog("", "Author", "1234567890123", 1)
    assert success == False
    assert "required" in message.lower()

def test_add_book_title_whitespace():
    """Test adding a book with title that is only whitespace."""
    success, message = add_book_to_catalog("   ", "Author", "1234567890123", 1)
    assert success == False
    assert "required" in message.lower()

def test_add_book_title_too_long():
    """Test adding a book with title exceeding 200 characters."""
    long_title = "A" * 201
    success, message = add_book_to_catalog(long_title, "Author", "1234567890123", 1)
    assert success == False
    assert "200 characters" in message.lower()

def test_add_book_author_empty():
    """Test adding a book with empty author."""
    success, message = add_book_to_catalog("Title", "", "1234567890123", 1)
    assert success == False
    assert "required" in message.lower()

def test_add_book_author_too_long():
    """Test adding a book with author exceeding 100 characters."""
    long_author = "B" * 101
    success, message = add_book_to_catalog("Title", long_author, "1234567890123", 1)
    assert success == False
    assert "100 characters" in message.lower()

def test_add_book_isbn_too_short():
    """Test adding a book with ISBN shorter than 13 digits."""
    success, message = add_book_to_catalog("Title", "Author", "123456789012", 1)
    assert success == False
    assert "13 digits" in message.lower()

def test_add_book_isbn_too_long():
    """Test adding a book with ISBN longer than 13 digits."""
    success, message = add_book_to_catalog("Title", "Author", "12345678901234", 1)
    assert success == False
    assert "13 digits" in message.lower()

def test_add_book_isbn_non_numeric():
    """Test adding a book with non-numeric ISBN."""
    success, message = add_book_to_catalog("Title", "Author", "abcdefghijklm", 1)
    assert success == False
    assert "13 digits" in message.lower()

def test_add_book_copies_zero():
    """Test adding a book with zero copies."""
    success, message = add_book_to_catalog("Title", "Author", "1234567890123", 0)
    assert success == False
    assert "positive integer" in message.lower()

def test_add_book_copies_negative():
    """Test adding a book with negative copies."""
    success, message = add_book_to_catalog("Title", "Author", "1234567890123", -1)
    assert success == False
    assert "positive integer" in message.lower()

def test_add_book_copies_non_integer():
    """Test adding a book with non-integer copies."""
    success, message = add_book_to_catalog("Title", "Author", "1234567890123", 1.5)
    assert success == False
    assert "positive integer" in message.lower()

def test_add_book_duplicate_isbn():
    """Test adding a book with duplicate ISBN."""
    add_book_to_catalog("First Book", "Author", "1234567890123", 1)
    success, message = add_book_to_catalog("Second Book", "Author", "1234567890123", 1)
    assert success == False
    assert "already exists" in message.lower()

def test_add_book_title_stripped():
    """Test that title is stripped of whitespace."""
    success, message = add_book_to_catalog("  Title  ", "Author", "1234567890123", 1)
    assert success == True
    assert '"Title"' in message

def test_add_book_author_stripped():
    """Test that author is stripped of whitespace."""
    success, message = add_book_to_catalog("Title", "  Author  ", "1234567890123", 1)
    assert success == True
