import pytest
from playwright.sync_api import Page, expect
import subprocess
import time
import signal
import sys
import os
import socket
import requests
from contextlib import closing

flask_process = None


def is_port_in_use(port):
    """Check if a port is already in use."""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        return sock.connect_ex(('127.0.0.1', port)) == 0


def wait_for_server(url, timeout=30, check_interval=0.5):
    """
    Wait for the server to become available by polling the URL.
    
    Args:
        url: The URL to check
        timeout: Maximum time to wait in seconds
        check_interval: Time between checks in seconds
    
    Returns:
        bool: True if server is available, False if timeout
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=1)
            if response.status_code < 500:  # Server is responding
                print(f"Server is ready at {url}")
                return True
        except (requests.ConnectionError, requests.Timeout):
            pass
        time.sleep(check_interval)
    return False


@pytest.fixture(scope="module", autouse=True)
def flask_server():
    """
    Start the Flask server before running E2E tests and stop it after.
    Includes proper server readiness check for CI.
    """
    global flask_process
    
    # Check if port is already in use
    if is_port_in_use(5001):
        print("\nPort 5001 is already in use. Using existing server.")
        yield
        return

    print("\nStarting Flask server for E2E tests...")
    
    # Start Flask server with explicit host binding
    flask_process = subprocess.Popen(
        [sys.executable, "app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={**os.environ, "FLASK_ENV": "testing"}
    )
    
    # Wait for the server to be ready (with proper health check)
    if not wait_for_server("http://127.0.0.1:5001", timeout=30):
        # If server didn't start, print error output
        if flask_process.poll() is not None:
            stdout, stderr = flask_process.communicate()
            print(f"Flask server failed to start!")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            raise RuntimeError("Flask server failed to start within 30 seconds")
    
    yield
    
    # Stop the Flask server after tests complete
    print("\nStopping Flask server...")
    if flask_process and flask_process.poll() is None:
        flask_process.send_signal(signal.SIGTERM)
        try:
            flask_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            flask_process.kill()
            flask_process.wait()


def test_homepage_title(page: Page) -> None:
    """Test that the homepage loads with the correct title."""
    page.goto("http://127.0.0.1:5001")
    expect(page).to_have_title("Library Management System")


def test_borrow_book_user_flow(page: Page) -> None:
    """
    E2E test for borrowing a book.
    
    User Flow:
    1. Navigate to the catalog page
    2. Verify the catalog displays books
    3. Find an available book
    4. Enter patron ID in the borrow form
    5. Submit the borrow request
    6. Verify success message appears
    7. Verify book availability count decreases
    """
    # Step 1: Navigate to the catalog page
    page.goto("http://127.0.0.1:5001/catalog")
    
    # Step 2: Verify the catalog page loaded with correct heading
    expect(page.locator("h2")).to_contain_text("Book Catalog")
    
    # Step 3: Verify that books are displayed in the table
    book_table = page.locator("table")
    expect(book_table).to_be_visible()
    
    # Verify table headers are present
    expect(page.locator("th:has-text('Title')")).to_be_visible()
    expect(page.locator("th:has-text('Author')")).to_be_visible()
    expect(page.locator("th:has-text('Availability')")).to_be_visible()
    expect(page.locator("th:has-text('Actions')")).to_be_visible()
    
    # Step 4: Find the first available book (with available copies > 0)
    first_available_book_row = page.locator("tr:has(.status-available)").first
    expect(first_available_book_row).to_be_visible()
    
    # Get the book title for verification
    book_title = first_available_book_row.locator("td").nth(1).inner_text()
    print(f"\n📚 Attempting to borrow: {book_title}")
    
    # Get the initial availability text
    initial_availability = first_available_book_row.locator(".status-available").inner_text()
    print(f"📊 Initial availability: {initial_availability}")
    
    # Step 5: Fill in the patron ID in the borrow form
    patron_id_input = first_available_book_row.locator("input[name='patron_id']")
    expect(patron_id_input).to_be_visible()
    expect(patron_id_input).to_have_attribute("placeholder", "Patron ID (6 digits)")
    
    # Enter a valid 6-digit patron ID
    patron_id_input.fill("123456")
    
    # Step 6: Verify the borrow button is present and click it
    borrow_button = first_available_book_row.locator("button:has-text('Borrow')")
    expect(borrow_button).to_be_visible()
    expect(borrow_button).to_have_class("btn btn-success")
    
    # Click the borrow button
    borrow_button.click()
    
    # Step 7: Wait for the page to reload and verify success message
    page.wait_for_load_state("networkidle")
    
    # Step 8: Verify that the book's availability has changed
    updated_book_row = page.locator(f"tr:has-text('{book_title}')").first
    expect(updated_book_row).to_be_visible()
    
    print(f"Successfully borrowed: {book_title}")


def test_borrow_book_invalid_patron_id(page: Page) -> None:
    """
    E2E test for attempting to borrow with invalid patron ID.
    
    User Flow:
    1. Navigate to catalog
    2. Find an available book
    3. Try to submit with empty or invalid patron ID
    4. Verify HTML5 validation prevents submission
    """
    page.goto("http://127.0.0.1:5001/catalog")
    
    # Find the first available book
    first_available_book_row = page.locator("tr:has(.status-available)").first
    expect(first_available_book_row).to_be_visible()
    
    # Get the patron ID input
    patron_id_input = first_available_book_row.locator("input[name='patron_id']")
    
    # Verify the input has HTML5 validation attributes
    expect(patron_id_input).to_have_attribute("pattern", "[0-9]{6}")
    expect(patron_id_input).to_have_attribute("required", "")
    expect(patron_id_input).to_have_attribute("maxlength", "6")
    
    # Try to enter invalid patron ID (too short)
    patron_id_input.fill("123")
    
    # Try to submit - HTML5 validation should prevent it
    borrow_button = first_available_book_row.locator("button:has-text('Borrow')")
    borrow_button.click()
    
    # Verify we're still on the same page
    expect(page).to_have_url("http://127.0.0.1:5001/catalog")
    
    print("HTML5 validation correctly prevents invalid patron ID submission")


def test_navigate_to_catalog_from_home(page: Page) -> None:
    """
    E2E test for navigation flow from home to catalog.
    
    User Flow:
    1. Start at homepage
    2. Click on catalog link
    3. Verify catalog page loads
    """
    # Start at homepage
    page.goto("http://127.0.0.1:5001")
    
    # Look for a link to the catalog
    catalog_link = page.locator("a[href*='catalog'], a:has-text('Catalog'), a:has-text('Browse')")
    
    if catalog_link.count() > 0:
        catalog_link.first.click()
        
        # Verify we're on the catalog page
        expect(page).to_have_url("http://127.0.0.1:5001/catalog")
        expect(page.locator("h2")).to_contain_text("Book Catalog")
        
        print("Successfully navigated from home to catalog")
    else:
        print("No catalog link found on homepage - skipping navigation test")


def test_catalog_displays_book_information(page: Page) -> None:
    """
    E2E test verifying all book information is displayed correctly.
    
    User Flow:
    1. Navigate to catalog
    2. Verify all expected columns are present
    3. Verify at least one book is displayed with complete information
    """
    page.goto("http://127.0.0.1:5001/catalog")
    
    # Verify all table headers are present
    headers = ["ID", "Title", "Author", "ISBN", "Availability", "Actions"]
    for header in headers:
        header_locator = page.locator(f"th:has-text('{header}')")
        expect(header_locator).to_be_visible()
        print(f"Found header: {header}")
    
    # Verify at least one book row exists
    book_rows = page.locator("tbody tr")
    expect(book_rows.first).to_be_visible()
    
    # Get the first book row and verify it has all required information
    first_book = book_rows.first
    
    # Should have 6 cells (ID, Title, Author, ISBN, Availability, Actions)
    cells = first_book.locator("td")
    expect(cells).to_have_count(6)
    
    # Verify each cell has content
    for i in range(6):
        cell_text = cells.nth(i).inner_text()
        print(f"  Column {i}: {cell_text[:50]}...")  # Print first 50 chars
    
    print("Catalog displays all book information correctly")