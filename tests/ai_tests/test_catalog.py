import pytest
from database import get_all_books, init_database, get_db_connection
from library_service import add_book_to_catalog

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

def test_get_all_books_empty():
    """Test getting all books when catalog is empty."""
    books = get_all_books()
    assert books == []

def test_get_all_books_single():
    """Test getting all books with one book."""
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 1)
    books = get_all_books()
    assert len(books) == 1
    assert books[0]['title'] == "Test Book"
    assert books[0]['author'] == "Test Author"
    assert books[0]['isbn'] == "1234567890123"
    assert books[0]['total_copies'] == 1
    assert books[0]['available_copies'] == 1

def test_get_all_books_multiple():
    """Test getting all books with multiple books."""
    add_book_to_catalog("Book 1", "Author 1", "1234567890123", 2)
    add_book_to_catalog("Book 2", "Author 2", "1234567890124", 3)
    books = get_all_books()
    assert len(books) == 2
    # Check sorted by title
    assert books[0]['title'] == "Book 1"
    assert books[1]['title'] == "Book 2"

def test_get_all_books_with_borrowed():
    """Test getting all books when some are borrowed."""
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 2)
    from library_service import borrow_book_by_patron
    book = get_all_books()[0]
    borrow_book_by_patron("123456", book['id'])
    books = get_all_books()
    assert len(books) == 1
    assert books[0]['available_copies'] == 1
    assert books[0]['total_copies'] == 2

def test_get_all_books_format():
    """Test that get_all_books returns correct format."""
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 1)
    books = get_all_books()
    book = books[0]
    required_keys = ['id', 'title', 'author', 'isbn', 'total_copies', 'available_copies']
    for key in required_keys:
        assert key in book