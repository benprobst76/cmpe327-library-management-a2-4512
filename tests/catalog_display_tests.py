import pytest
from library_service import add_book_to_catalog
from database import init_database, get_db_connection, get_all_books, get_book_by_isbn

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

def test_catalog_display_empty_catalog():
    """Test displaying catalog when no books exist."""
    books = get_all_books()
    
    assert isinstance(books, list)
    assert len(books) == 0

def test_catalog_display_single_book():
    """Test displaying catalog with a single book."""
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 5)
    
    books = get_all_books()
    
    assert len(books) == 1
    book = books[0]
    
    # Check all required fields are present
    required_fields = ['id', 'title', 'author', 'isbn', 'total_copies', 'available_copies']
    for field in required_fields:
        assert field in book
    
    assert book['title'] == "Test Book"
    assert book['author'] == "Test Author"
    assert book['isbn'] == "1234567890123"
    assert book['total_copies'] == 5
    assert book['available_copies'] == 5

def test_catalog_display_multiple_books():
    """Test displaying catalog with multiple books."""
    add_book_to_catalog("Book 1", "Author 1", "1234567890123", 3)
    add_book_to_catalog("Book 2", "Author 2", "1234567890124", 2)
    add_book_to_catalog("Book 3", "Author 3", "1234567890125", 1)
    
    books = get_all_books()
    
    assert len(books) == 3
    
    # Verify each book has all required fields
    for book in books:
        required_fields = ['id', 'title', 'author', 'isbn', 'total_copies', 'available_copies']
        for field in required_fields:
            assert field in book

def test_catalog_display_books_sorted_by_title():
    """Test that books in catalog are sorted alphabetically by title."""
    add_book_to_catalog("Zebra Book", "Author 1", "1234567890123", 1)
    add_book_to_catalog("Apple Book", "Author 2", "1234567890124", 1)
    add_book_to_catalog("Book Middle", "Author 3", "1234567890125", 1)
    
    books = get_all_books()
    
    assert len(books) == 3
    # Books should be sorted by title
    assert books[0]['title'] == "Apple Book"
    assert books[1]['title'] == "Book Middle"
    assert books[2]['title'] == "Zebra Book"

def test_catalog_display_book_with_zero_available_copies():
    """Test displaying a book with zero available copies."""
    add_book_to_catalog("Popular Book", "Famous Author", "1234567890123", 1)
    book_id = get_book_by_isbn("1234567890123")['id']
    # Simulate borrowing by updating available copies
    conn = get_db_connection()
    conn.execute('UPDATE books SET available_copies = 0 WHERE id = ?', (book_id,))
    conn.commit()
    conn.close()
    
    books = get_all_books()
    book = books[0]
    
    assert book['total_copies'] == 1
    assert book['available_copies'] == 0