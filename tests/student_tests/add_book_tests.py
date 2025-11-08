import pytest
from services.library_service import (
    add_book_to_catalog
)

def test_add_book_valid_input():
    """Test adding a book with valid input."""
    success, message = add_book_to_catalog("Test Book", "Test Author", "1234567890123", 5)
    
    assert success == True
    assert "successfully added" in message.lower()

def test_add_book_invalid_copies_negative():
    """Test adding a book with negative number of copies."""
    success, message = add_book_to_catalog("Test Book", "Test Author", "1234567890123", -1)
    
    assert success == False
    assert "positive integer" in message.lower()

def test_add_book_empty_isbn():
    """Test adding a book with empty ISBN."""
    success, message = add_book_to_catalog("Test Book", "Test Author", "", 5)

    assert success == False
    assert "13 digits" in message.lower()

def test_add_book_zero_copies():
    """Test adding a book with zero copies."""
    success, message = add_book_to_catalog("Test Book", "Test Author", "1234567890123", 0)
    
    assert success == False
    assert "positive integer" in message.lower()

def test_add_book_duplicate_isbn():
    """Test adding a book with a duplicate ISBN."""
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 5)
    success, message = add_book_to_catalog("Another Book", "Another Author", "1234567890123", 3)

    assert success == False
    assert "already exists" in message.lower()