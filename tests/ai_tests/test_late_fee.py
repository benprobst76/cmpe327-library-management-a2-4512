import pytest
from datetime import datetime, timedelta
from library_service import calculate_late_fee_for_book, add_book_to_catalog, borrow_book_by_patron
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

def test_calculate_late_fee_not_overdue():
    """Test calculating late fee for a book that is not overdue."""
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 1)
    book = get_book_by_isbn("1234567890123")
    borrow_book_by_patron("123456", book['id'])
    result = calculate_late_fee_for_book("123456", book['id'])
    assert result['fee_amount'] == 0.00
    assert result['days_overdue'] == 0
    assert result['status'] == 'on time'

def test_calculate_late_fee_overdue_1_day():
    """Test calculating late fee for 1 day overdue."""
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 1)
    book = get_book_by_isbn("1234567890123")
    borrow_book_by_patron("123456", book['id'])
    # Simulate 15 days passed (1 day overdue)
    conn = get_db_connection()
    conn.execute('UPDATE borrow_records SET borrow_date = ?, due_date = ? WHERE patron_id = ? AND book_id = ?',
                 ((datetime.now() - timedelta(days=15)).isoformat(), (datetime.now() - timedelta(days=1)).isoformat(), "123456", book['id']))
    conn.commit()
    conn.close()
    result = calculate_late_fee_for_book("123456", book['id'])
    assert result['fee_amount'] == 0.50
    assert result['days_overdue'] == 1
    assert result['status'] == 'overdue'

def test_calculate_late_fee_overdue_7_days():
    """Test calculating late fee for 7 days overdue."""
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 1)
    book = get_book_by_isbn("1234567890123")
    borrow_book_by_patron("123456", book['id'])
    # Simulate 21 days passed (7 days overdue)
    conn = get_db_connection()
    conn.execute('UPDATE borrow_records SET borrow_date = ?, due_date = ? WHERE patron_id = ? AND book_id = ?',
                 ((datetime.now() - timedelta(days=21)).isoformat(), (datetime.now() - timedelta(days=7)).isoformat(), "123456", book['id']))
    conn.commit()
    conn.close()
    result = calculate_late_fee_for_book("123456", book['id'])
    assert result['fee_amount'] == 3.50  # 7 * 0.50
    assert result['days_overdue'] == 7
    assert result['status'] == 'overdue'

def test_calculate_late_fee_overdue_8_days():
    """Test calculating late fee for 8 days overdue."""
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 1)
    book = get_book_by_isbn("1234567890123")
    borrow_book_by_patron("123456", book['id'])
    # Simulate 22 days passed (8 days overdue)
    conn = get_db_connection()
    conn.execute('UPDATE borrow_records SET borrow_date = ?, due_date = ? WHERE patron_id = ? AND book_id = ?',
                 ((datetime.now() - timedelta(days=22)).isoformat(), (datetime.now() - timedelta(days=8)).isoformat(), "123456", book['id']))
    conn.commit()
    conn.close()
    result = calculate_late_fee_for_book("123456", book['id'])
    assert result['fee_amount'] == 4.50  # 7*0.50 + 1*1.00
    assert result['days_overdue'] == 8
    assert result['status'] == 'overdue'

def test_calculate_late_fee_overdue_30_days():
    """Test calculating late fee for 30 days overdue, capped at 15.00."""
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 1)
    book = get_book_by_isbn("1234567890123")
    borrow_book_by_patron("123456", book['id'])
    # Simulate 34 days passed (20 days overdue)
    conn = get_db_connection()
    conn.execute('UPDATE borrow_records SET borrow_date = ?, due_date = ? WHERE patron_id = ? AND book_id = ?',
                 ((datetime.now() - timedelta(days=34)).isoformat(), (datetime.now() - timedelta(days=20)).isoformat(), "123456", book['id']))
    conn.commit()
    conn.close()
    result = calculate_late_fee_for_book("123456", book['id'])
    assert result['fee_amount'] == 15.00  # Max fee
    assert result['days_overdue'] == 20
    assert result['status'] == 'overdue'

def test_calculate_late_fee_invalid_patron_id():
    """Test calculating late fee with invalid patron ID."""
    result = calculate_late_fee_for_book("12345", 1)
    assert result['fee_amount'] == 0.00
    assert result['days_overdue'] == 0
    assert result['status'] == 'invalid patron ID'

def test_calculate_late_fee_invalid_book_id():
    """Test calculating late fee with invalid book ID."""
    result = calculate_late_fee_for_book("123456", 999)
    assert result['fee_amount'] == 0.00
    assert result['days_overdue'] == 0
    assert result['status'] == 'invalid book ID'

def test_calculate_late_fee_not_borrowed():
    """Test calculating late fee for a book not borrowed by the patron."""
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 1)
    book = get_book_by_isbn("1234567890123")
    result = calculate_late_fee_for_book("123456", book['id'])
    assert result['fee_amount'] == 0.00
    assert result['days_overdue'] == 0
    assert result['status'] == 'no borrow record'

def test_calculate_late_fee_returned_book():
    """Test calculating late fee for a returned book."""
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 1)
    book = get_book_by_isbn("1234567890123")
    borrow_book_by_patron("123456", book['id'])
    # Return the book
    from library_service import return_book_by_patron
    return_book_by_patron("123456", book['id'])
    result = calculate_late_fee_for_book("123456", book['id'])
    assert result['fee_amount'] == 0.00
    assert result['days_overdue'] == 0
    assert result['status'] == 'no borrow record'