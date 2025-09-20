import pytest
from library_service import (
    search_books_in_catalog, add_book_to_catalog
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
    add_book_to_catalog("The Catcher in the Rye", "J.D. Salinger", "9780316769174", 1)

def test_search_books_by_title_exact_match():
    """Test searching for books by exact title match."""
    setup_sample_books()
    
    results = search_books_in_catalog("1984", "title")
    
    assert len(results) == 1
    assert results[0]['title'] == "1984"
    assert results[0]['author'] == "George Orwell"

def test_search_books_by_title_partial_match():
    """Test searching for books by partial title match."""
    setup_sample_books()
    
    results = search_books_in_catalog("Great", "title")
    
    assert len(results) == 1
    assert "Great" in results[0]['title']

def test_search_books_by_title_no_results():
    """Test searching for books by title with no matches."""
    setup_sample_books()
    
    results = search_books_in_catalog("Nonexistent Book", "title")
    
    assert len(results) == 0

def test_search_books_by_title_multiple_results():
    """Test searching for books by title returning multiple results."""
    setup_sample_books()
    # Add more books with "The" in title
    add_book_to_catalog("The Hobbit", "J.R.R. Tolkien", "9780547928227", 2)
    
    results = search_books_in_catalog("The", "title")
    
    assert len(results) >= 2  # Should find multiple books with "The"

def test_search_books_by_isbn_exact_match():
    """Test searching for books by exact ISBN match."""
    setup_sample_books()
    
    results = search_books_in_catalog("9780451524935", "isbn")
    
    assert len(results) == 1
    assert results[0]['title'] == "1984"
    assert results[0]['isbn'] == "9780451524935"