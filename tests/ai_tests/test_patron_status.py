import pytest
from datetime import datetime, timedelta
from services.library_service import get_patron_status_report, add_book_to_catalog, borrow_book_by_patron, return_book_by_patron
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

def test_patron_status_no_history():
    """Test patron status for a patron with no borrowing history."""
    result = get_patron_status_report("123456")
    assert 'currently_borrowed' in result
    assert 'total_late_fees' in result
    assert 'books_borrowed_count' in result
    assert 'borrowing_history' in result
    assert result['currently_borrowed'] == []
    assert result['total_late_fees'] == 0.0
    assert result['books_borrowed_count'] == 0
    assert result['borrowing_history'] == []

def test_patron_status_invalid_patron_id():
    """Test patron status with invalid patron ID."""
    result = get_patron_status_report("12345")
    assert 'error' in result
    assert "Invalid patron ID" in result['error']

def test_patron_status_currently_borrowed():
    """Test patron status with currently borrowed books."""
    add_book_to_catalog("Test Book 1", "Author 1", "1234567890123", 1)
    add_book_to_catalog("Test Book 2", "Author 2", "1234567890124", 1)
    book1 = get_book_by_isbn("1234567890123")
    book2 = get_book_by_isbn("1234567890124")
    borrow_book_by_patron("123456", book1['id'])
    borrow_book_by_patron("123456", book2['id'])
    result = get_patron_status_report("123456")
    assert len(result['currently_borrowed']) == 2
    assert result['books_borrowed_count'] == 2
    assert result['total_late_fees'] == 0.0
    assert len(result['borrowing_history']) == 2

def test_patron_status_with_returns():
    """Test patron status including returned books."""
    add_book_to_catalog("Test Book", "Author", "1234567890123", 1)
    book = get_book_by_isbn("1234567890123")
    borrow_book_by_patron("123456", book['id'])
    return_book_by_patron("123456", book['id'])
    result = get_patron_status_report("123456")
    assert result['currently_borrowed'] == []
    assert result['books_borrowed_count'] == 0
    assert len(result['borrowing_history']) == 1
    assert result['borrowing_history'][0]['return_date'] is not None

def test_patron_status_with_overdue():
    """Test patron status with overdue books."""
    add_book_to_catalog("Test Book", "Author", "1234567890123", 1)
    book = get_book_by_isbn("1234567890123")
    borrow_book_by_patron("123456", book['id'])
    # Make it overdue by 5 days
    borrow_date = datetime.now() - timedelta(days=19)
    due_date = borrow_date + timedelta(days=14)
    conn = get_db_connection()
    conn.execute('UPDATE borrow_records SET borrow_date = ?, due_date = ? WHERE patron_id = ? AND book_id = ?',
                 (borrow_date.isoformat(), due_date.isoformat(), "123456", book['id']))
    conn.commit()
    conn.close()
    result = get_patron_status_report("123456")
    assert len(result['currently_borrowed']) == 1
    assert result['total_late_fees'] == 2.50  # 5 * 0.50
    assert result['borrowing_history'][0]['fee_incurred'] == 2.50

def test_patron_status_mixed_history():
    """Test patron status with mix of current, returned, and overdue books."""
    add_book_to_catalog("Book 1", "Author 1", "1234567890123", 1)
    add_book_to_catalog("Book 2", "Author 2", "1234567890124", 1)
    add_book_to_catalog("Book 3", "Author 3", "1234567890125", 1)
    book1 = get_book_by_isbn("1234567890123")
    book2 = get_book_by_isbn("1234567890124")
    book3 = get_book_by_isbn("1234567890125")
    
    # Borrow all three
    borrow_book_by_patron("123456", book1['id'])
    borrow_book_by_patron("123456", book2['id'])
    borrow_book_by_patron("123456", book3['id'])
    
    # Return book1 on time
    return_book_by_patron("123456", book1['id'])
    
    # Make book2 overdue by 10 days
    borrow_date = datetime.now() - timedelta(days=24)
    due_date = borrow_date + timedelta(days=14)
    conn = get_db_connection()
    conn.execute('UPDATE borrow_records SET borrow_date = ?, due_date = ? WHERE patron_id = ? AND book_id = ?',
                 (borrow_date.isoformat(), due_date.isoformat(), "123456", book2['id']))
    conn.commit()
    conn.close()
    
    result = get_patron_status_report("123456")
    assert len(result['currently_borrowed']) == 2  # book2 and book3
    assert result['books_borrowed_count'] == 2
    assert result['total_late_fees'] == 6.50  # 7*0.5 + 3*1.0 for book2
    assert len(result['borrowing_history']) == 3

def test_patron_status_fee_calculation():
    """Test detailed fee calculation in patron status."""
    add_book_to_catalog("Test Book", "Author", "1234567890123", 1)
    book = get_book_by_isbn("1234567890123")
    borrow_book_by_patron("123456", book['id'])
    # Make it overdue by 20 days
    borrow_date = datetime.now() - timedelta(days=34)
    due_date = borrow_date + timedelta(days=14)
    conn = get_db_connection()
    conn.execute('UPDATE borrow_records SET borrow_date = ?, due_date = ? WHERE patron_id = ? AND book_id = ?',
                 (borrow_date.isoformat(), due_date.isoformat(), "123456", book['id']))
    conn.commit()
    conn.close()
    result = get_patron_status_report("123456")
    assert result['total_late_fees'] == 15.00  # Max fee
    assert result['borrowing_history'][0]['fee_incurred'] == 15.00

def test_patron_status_data_format():
    """Test that the returned data is in the correct format."""
    add_book_to_catalog("Test Book", "Author", "1234567890123", 1)
    book = get_book_by_isbn("1234567890123")
    borrow_book_by_patron("123456", book['id'])
    result = get_patron_status_report("123456")
    # Check currently_borrowed format
    for book in result['currently_borrowed']:
        assert 'book_id' in book
        assert 'title' in book
        assert 'author' in book
        assert 'due_date' in book
    # Check borrowing_history format
    for record in result['borrowing_history']:
        assert 'book_id' in record
        assert 'title' in record
        assert 'author' in record
        assert 'borrow_date' in record
        assert 'due_date' in record
        assert 'return_date' in record
        assert 'fee_incurred' in record