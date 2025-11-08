from unittest.mock import Mock
from services.library_service import pay_late_fees, refund_late_fee_payment
from services.payment_service import PaymentGateway


class TestPayLateFees:
    """Test suite for pay_late_fees function using stubbing and mocking."""
    
    def test_pay_late_fees_calculate_fee_returns_none(self, mocker):
        # Stub calculate_late_fee_for_book to return None
        mocker.patch(
            'services.library_service.calculate_late_fee_for_book',
            return_value=None
        )
        result = pay_late_fees("123456", 1)
        assert result == (False, "Unable to calculate late fees.", None)
    
    def test_pay_late_fees_calculate_fee_missing_amount(self, mocker):
        # Stub calculate_late_fee_for_book to return incomplete data
        mocker.patch(
            'services.library_service.calculate_late_fee_for_book',
            return_value={'status': 'overdue', 'days_overdue': 5}
        )
        result = pay_late_fees("123456", 1)
        assert result == (False, "Unable to calculate late fees.", None)
    
    def test_pay_late_fees_no_fees_to_pay(self, mocker):
        # Stub calculate_late_fee_for_book to return zero fee
        mocker.patch(
            'services.library_service.calculate_late_fee_for_book',
            return_value={
                'fee_amount': 0.0,
                'days_overdue': 0,
                'status': 'on time'
            }
        )
        result = pay_late_fees("123456", 1)
        assert result == (False, "No late fees to pay for this book.", None)
    
    def test_pay_late_fees_negative_amount(self, mocker):
        # Stub calculate_late_fee_for_book to return negative fee
        mocker.patch(
            'services.library_service.calculate_late_fee_for_book',
            return_value={
                'fee_amount': -5.0,
                'days_overdue': 0,
                'status': 'error'
            }
        )
        result = pay_late_fees("123456", 1)
        assert result == (False, "No late fees to pay for this book.", None)
    
    def test_pay_late_fees_book_not_found(self, mocker):
        # Stub calculate_late_fee_for_book to return valid fee
        mocker.patch(
            'services.library_service.calculate_late_fee_for_book',
            return_value={
                'fee_amount': 5.50,
                'days_overdue': 11,
                'status': 'overdue'
            }
        )
        # Stub get_book_by_id to return None (book not found)
        mocker.patch('services.library_service.get_book_by_id', return_value=None)
        result = pay_late_fees("123456", 1)
        assert result == (False, "Book not found.", None)
    
    def test_pay_late_fees_successful_payment(self, mocker):
        # Stub calculate_late_fee_for_book to return valid fee
        mocker.patch(
            'services.library_service.calculate_late_fee_for_book',
            return_value={
                'fee_amount': 7.50,
                'days_overdue': 15,
                'status': 'overdue'
            }
        )
        # Stub get_book_by_id to return valid book
        mocker.patch(
            'services.library_service.get_book_by_id',
            return_value={
                'id': 1,
                'title': 'Test Book',
                'author': 'Test Author',
                'isbn': '1234567890123',
                'total_copies': 3,
                'available_copies': 2
            }
        )
        # Create mock payment gateway
        mock_gateway = Mock(spec=PaymentGateway)
        mock_gateway.process_payment.return_value = (True, "txn_abc123", "Payment successful")
        
        result = pay_late_fees("123456", 1, mock_gateway)
        
        # Verify the result
        assert result[0] is True
        assert "Payment successful! Payment successful" in result[1]
        assert result[2] == "txn_abc123"
        
        # Verify payment gateway was called with correct parameters
        mock_gateway.process_payment.assert_called_once_with(
            patron_id="123456",
            amount=7.50,
            description="Late fees for 'Test Book'"
        )
    
    def test_pay_late_fees_payment_failure(self, mocker):
        """Test payment processing failure."""
        # Stub calculate_late_fee_for_book to return valid fee
        mocker.patch(
            'services.library_service.calculate_late_fee_for_book',
            return_value={
                'fee_amount': 3.00,
                'days_overdue': 6,
                'status': 'overdue'
            }
        )
        
        # Stub get_book_by_id to return valid book
        mocker.patch(
            'services.library_service.get_book_by_id',
            return_value={
                'id': 2,
                'title': 'Another Book',
                'author': 'Another Author'
            }
        )
        
        # Create mock payment gateway that fails
        mock_gateway = Mock(spec=PaymentGateway)
        mock_gateway.process_payment.return_value = (False, None, "Insufficient funds")
        
        result = pay_late_fees("123456", 2, mock_gateway)
        
        # Verify the result
        assert result[0] is False
        assert "Payment failed: Insufficient funds" in result[1]
        assert result[2] is None
    
    def test_pay_late_fees_payment_gateway_exception(self, mocker):
        """Test payment gateway throwing an exception."""
        # Stub calculate_late_fee_for_book to return valid fee
        mocker.patch(
            'services.library_service.calculate_late_fee_for_book',
            return_value={
                'fee_amount': 10.00,
                'days_overdue': 20,
                'status': 'overdue'
            }
        )
        
        # Stub get_book_by_id to return valid book
        mocker.patch(
            'services.library_service.get_book_by_id',
            return_value={
                'id': 3,
                'title': 'Exception Book',
                'author': 'Exception Author'
            }
        )
        
        # Create mock payment gateway that raises exception
        mock_gateway = Mock(spec=PaymentGateway)
        mock_gateway.process_payment.side_effect = Exception("Network timeout")
        
        result = pay_late_fees("123456", 3, mock_gateway)
        
        # Verify the result
        assert result[0] is False
        assert "Payment processing error: Network timeout" in result[1]
        assert result[2] is None
    
    def test_pay_late_fees_default_payment_gateway(self, mocker):
        """Test pay_late_fees using default payment gateway."""
        # Stub calculate_late_fee_for_book to return valid fee
        mocker.patch(
            'services.library_service.calculate_late_fee_for_book',
            return_value={
                'fee_amount': 4.50,
                'days_overdue': 9,
                'status': 'overdue'
            }
        )
        
        # Stub get_book_by_id to return valid book
        mocker.patch(
            'services.library_service.get_book_by_id',
            return_value={
                'id': 4,
                'title': 'Default Gateway Book',
                'author': 'Default Author'
            }
        )
        
        # Mock PaymentGateway
        mock_gateway_instance = Mock(spec=PaymentGateway)
        mock_gateway_instance.process_payment.return_value = (True, "txn_default123", "Success")
        
        mock_gateway_class = mocker.patch('services.library_service.PaymentGateway')
        mock_gateway_class.return_value = mock_gateway_instance
        
        result = pay_late_fees("123456", 4)
        
        # Verify the result
        assert result[0] is True
        assert "Payment successful! Success" in result[1]
        assert result[2] == "txn_default123"
        
        # Verify PaymentGateway was instantiated
        mock_gateway_class.assert_called_once()


class TestRefundLateFeePayment:
    """Test suite for refund_late_fee_payment function using stubbing and mocking."""
    
    def test_refund_successful(self):
        """Test successful refund processing."""
        # Create mock payment gateway
        mock_gateway = Mock(spec=PaymentGateway)
        mock_gateway.refund_payment.return_value = (True, "Refund processed successfully")
        
        result = refund_late_fee_payment("txn_abc123", 8.50, mock_gateway)
        
        # Verify the result
        assert result[0] is True
        assert result[1] == "Refund processed successfully"
        
        # Verify payment gateway was called with correct parameters
        mock_gateway.refund_payment.assert_called_once_with("txn_abc123", 8.50)
    
    def test_refund_payment_failure(self):
        """Test refund processing failure."""
        # Create mock payment gateway that fails
        mock_gateway = Mock(spec=PaymentGateway)
        mock_gateway.refund_payment.return_value = (False, "Transaction not found")
        
        result = refund_late_fee_payment("txn_notfound", 5.00, mock_gateway)
        
        # Verify the result
        assert result[0] is False
        assert result[1] == "Refund failed: Transaction not found"
    
    def test_refund_payment_gateway_exception(self):
        """Test refund gateway throwing an exception."""
        # Create mock payment gateway that raises exception
        mock_gateway = Mock(spec=PaymentGateway)
        mock_gateway.refund_payment.side_effect = Exception("API connection failed")
        
        result = refund_late_fee_payment("txn_exception", 7.25, mock_gateway)
        
        # Verify the result
        assert result[0] is False
        assert result[1] == "Refund processing error: API connection failed"
    
    def test_refund_default_payment_gateway(self, mocker):
        """Test refund using default payment gateway."""
        # Mock the PaymentGateway
        mock_gateway_instance = Mock(spec=PaymentGateway)
        mock_gateway_instance.refund_payment.return_value = (True, "Default refund successful")
        
        mock_gateway_class = mocker.patch('services.library_service.PaymentGateway')
        mock_gateway_class.return_value = mock_gateway_instance
        
        result = refund_late_fee_payment("txn_default456", 12.00)
        
        # Verify the result
        assert result[0] is True
        assert result[1] == "Default refund successful"
        
        # Verify PaymentGateway was called
        mock_gateway_class.assert_called_once()
        
        # Verify refund_payment was called with correct parameters
        mock_gateway_instance.refund_payment.assert_called_once_with("txn_default456", 12.00)
    
    def test_refund_edge_case_maximum_amount(self):
        """Test refund with exactly the maximum allowed amount."""
        # Create mock payment gateway
        mock_gateway = Mock(spec=PaymentGateway)
        mock_gateway.refund_payment.return_value = (True, "Maximum refund processed")
        
        result = refund_late_fee_payment("txn_maxrefund", 15.00, mock_gateway)
        
        # Verify the result
        assert result[0] is True
        assert result[1] == "Maximum refund processed"
    
    def test_refund_edge_case_minimum_amount(self):
        """Test refund with minimum positive amount."""
        # Create mock payment gateway
        mock_gateway = Mock(spec=PaymentGateway)
        mock_gateway.refund_payment.return_value = (True, "Minimum refund processed")
        
        result = refund_late_fee_payment("txn_minrefund", 0.01, mock_gateway)
        
        # Verify the result
        assert result[0] is True
        assert result[1] == "Minimum refund processed"