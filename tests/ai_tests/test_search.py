import pytest
from library_service import search_books_in_catalog, add_book_to_catalog
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

def setup_sample_books():
    """Add sample books for testing."""
    add_book_to_catalog("The Great Gatsby", "F. Scott Fitzgerald", "9780743273565", 3)
    add_book_to_catalog("To Kill a Mockingbird", "Harper Lee", "9780061120084", 2)
    add_book_to_catalog("1984", "George Orwell", "9780451524935", 1)
    add_book_to_catalog("Pride and Prejudice", "Jane Austen", "9780141439518", 1)

def test_search_by_title_exact():
    """Test searching by title with exact match."""
    setup_sample_books()
    results = search_books_in_catalog("The Great Gatsby", "title")
    assert len(results) == 1
    assert results[0]['title'] == "The Great Gatsby"

def test_search_by_title_partial():
    """Test searching by title with partial match."""
    setup_sample_books()
    results = search_books_in_catalog("Great", "title")
    assert len(results) == 1
    assert "Great Gatsby" in results[0]['title']

def test_search_by_title_case_insensitive():
    """Test searching by title is case insensitive."""
    setup_sample_books()
    results = search_books_in_catalog("great gatsby", "title")
    assert len(results) == 1
    assert results[0]['title'] == "The Great Gatsby"

def test_search_by_author_exact():
    """Test searching by author with exact match."""
    setup_sample_books()
    results = search_books_in_catalog("F. Scott Fitzgerald", "author")
    assert len(results) == 1
    assert results[0]['author'] == "F. Scott Fitzgerald"

def test_search_by_author_partial():
    """Test searching by author with partial match."""
    setup_sample_books()
    results = search_books_in_catalog("Fitzgerald", "author")
    assert len(results) == 1
    assert results[0]['author'] == "F. Scott Fitzgerald"

def test_search_by_author_case_insensitive():
    """Test searching by author is case insensitive."""
    setup_sample_books()
    results = search_books_in_catalog("f. scott fitzgerald", "author")
    assert len(results) == 1
    assert results[0]['author'] == "F. Scott Fitzgerald"

def test_search_by_isbn_exact():
    """Test searching by ISBN with exact match."""
    setup_sample_books()
    results = search_books_in_catalog("9780743273565", "isbn")
    assert len(results) == 1
    assert results[0]['isbn'] == "9780743273565"

def test_search_by_isbn_partial():
    """Test searching by ISBN with partial match (should not match)."""
    setup_sample_books()
    results = search_books_in_catalog("978074", "isbn")
    assert len(results) == 0

def test_search_no_results():
    """Test searching with no matching results."""
    setup_sample_books()
    results = search_books_in_catalog("Nonexistent Book", "title")
    assert len(results) == 0

def test_search_empty_term():
    """Test searching with empty search term."""
    setup_sample_books()
    results = search_books_in_catalog("", "title")
    assert len(results) == 0

def test_search_invalid_type():
    """Test searching with invalid search type."""
    setup_sample_books()
    results = search_books_in_catalog("Test", "invalid")
    assert len(results) == 0

def test_search_type_case_insensitive():
    """Test that search type is case insensitive."""
    setup_sample_books()
    results = search_books_in_catalog("The Great Gatsby", "TITLE")
    assert len(results) == 1
    assert results[0]['title'] == "The Great Gatsby"

def test_search_whitespace_term():
    """Test searching with whitespace-only term."""
    setup_sample_books()
    results = search_books_in_catalog("   ", "title")
    assert len(results) == 0

def test_search_multiple_results():
    """Test searching that returns multiple results."""
    setup_sample_books()
    results = search_books_in_catalog("g", "author")
    assert len(results) == 2  # All authors that contain 'g'

def test_search_non_string_term():
    """Test searching with non-string term."""
    setup_sample_books()
    results = search_books_in_catalog(123, "title")
    assert len(results) == 0

def test_search_non_string_type():
    """Test searching with non-string type."""
    setup_sample_books()
    results = search_books_in_catalog("Test", 123)
    assert len(results) == 0