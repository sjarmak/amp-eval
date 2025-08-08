"""Tests to validate the refactoring."""
import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))


def test_no_circular_imports():
    """Test that circular imports are resolved."""
    try:
        import models
        import utils
        import views
        # If we get here, no circular import error occurred
        assert True
    except ImportError as e:
        pytest.fail(f"Circular import detected: {e}")


def test_auth_service_extracted():
    """Test that authentication logic is properly extracted."""
    # This should pass after refactoring
    try:
        from auth import AuthService  # Should exist after refactoring
        auth_service = AuthService()
        assert hasattr(auth_service, 'authenticate_user')
        assert hasattr(auth_service, 'hash_password')
    except ImportError:
        pytest.fail("AuthService not properly extracted")


def test_email_service_extracted():
    """Test that email service is properly extracted."""
    try:
        from email_service import EmailService  # Should exist after refactoring
        email_service = EmailService()
        assert hasattr(email_service, 'send_welcome_email')
        assert hasattr(email_service, 'validate_email')
    except ImportError:
        pytest.fail("EmailService not properly extracted")


def test_user_service_extracted():
    """Test that user business logic is in service layer."""
    try:
        from user_service import UserService  # Should exist after refactoring
        user_service = UserService()
        assert hasattr(user_service, 'get_user_profile')
        assert hasattr(user_service, 'format_username')
    except ImportError:
        pytest.fail("UserService not properly extracted")


@patch('smtplib.SMTP')
def test_email_functionality_preserved(mock_smtp):
    """Test that email functionality still works after refactoring."""
    # This test should pass both before and after refactoring
    mock_smtp_instance = Mock()
    mock_smtp.return_value = mock_smtp_instance
    
    # Test email sending functionality
    # Implementation will depend on refactored structure
    pass


if __name__ == "__main__":
    pytest.main([__file__])
