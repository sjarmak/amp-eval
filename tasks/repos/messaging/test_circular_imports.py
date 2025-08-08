"""Tests to validate circular import resolution."""
import pytest
import sys
import importlib


def test_no_circular_import_errors():
    """Test that all modules can be imported without circular import errors."""
    # Clear any previously imported modules
    modules_to_clear = ['user_manager', 'message_handler', 'notifications']
    for module in modules_to_clear:
        if module in sys.modules:
            del sys.modules[module]
    
    try:
        # These should not raise ImportError due to circular imports
        import user_manager
        import message_handler  
        import notifications
        
        # Force reload to ensure clean imports
        importlib.reload(user_manager)
        importlib.reload(message_handler)
        importlib.reload(notifications)
        
    except ImportError as e:
        pytest.fail(f"Circular import error: {e}")


def test_user_manager_independent():
    """Test that UserManager can be created independently."""
    try:
        from user_manager import UserManager
        
        # Should be able to create without circular dependency issues
        user_mgr = UserManager()
        assert user_mgr is not None
        
    except Exception as e:
        pytest.fail(f"UserManager creation failed: {e}")


def test_message_handler_independent():
    """Test that MessageHandler can work without circular dependencies."""
    try:
        # Should be able to import and use MessageHandler
        from message_handler import MessageHandler
        from user_manager import UserManager
        
        user_mgr = UserManager()
        msg_handler = MessageHandler(user_mgr)
        assert msg_handler is not None
        
    except Exception as e:
        pytest.fail(f"MessageHandler creation failed: {e}")


def test_notification_service_independent():
    """Test that NotificationService can work without circular dependencies."""
    try:
        from notifications import NotificationService
        from user_manager import UserManager
        
        user_mgr = UserManager()
        notif_service = NotificationService(user_mgr)
        assert notif_service is not None
        
    except Exception as e:
        pytest.fail(f"NotificationService creation failed: {e}")


def test_functionality_preserved():
    """Test that functionality is preserved after fixing circular imports."""
    try:
        from user_manager import UserManager
        
        # Create system
        user_mgr = UserManager()
        
        # Create users
        user1 = user_mgr.create_user("u1", "alice", "alice@example.com")
        user2 = user_mgr.create_user("u2", "bob", "bob@example.com")
        
        assert user1.user_id == "u1"
        assert user2.user_id == "u2"
        
        # Test messaging functionality
        user_mgr.send_message("u1", "u2", "Hello Bob!")
        messages = user_mgr.get_user_messages("u2")
        assert len(messages) > 0
        
        # Test friend functionality
        user_mgr.add_friend("u1", "u2")
        assert "u2" in user1.friends
        assert "u1" in user2.friends
        
    except Exception as e:
        pytest.fail(f"Functionality not preserved: {e}")


def test_dependency_injection_pattern():
    """Test that proper dependency injection is implemented."""
    try:
        # Should be able to create components with proper DI
        from user_manager import UserManager
        from message_handler import MessageHandler
        from notifications import NotificationService
        
        # Create in proper order without circular dependencies
        user_mgr = UserManager()
        
        # Should be able to inject dependencies properly
        msg_handler = MessageHandler(user_mgr)
        notif_service = NotificationService(user_mgr)
        
        # Verify proper references
        assert msg_handler.user_manager is user_mgr
        assert notif_service.user_manager is user_mgr
        
    except Exception as e:
        pytest.fail(f"Dependency injection not properly implemented: {e}")


def test_event_system_or_interfaces():
    """Test that proper decoupling mechanism is implemented."""
    # This test checks for alternative solutions like event systems or interfaces
    try:
        from user_manager import UserManager
        
        user_mgr = UserManager()
        
        # Should have some form of event system or interface
        # to avoid direct circular dependencies
        if hasattr(user_mgr, 'event_bus'):
            assert user_mgr.event_bus is not None
        elif hasattr(user_mgr, 'message_service'):
            # Using interface/service pattern
            assert user_mgr.message_service is not None
        elif hasattr(user_mgr, 'notification_service'):
            # Using service injection
            assert user_mgr.notification_service is not None
        else:
            # At minimum, should not have direct circular imports
            # Check that the classes exist and work
            user = user_mgr.create_user("test", "test", "test@example.com")
            assert user is not None
            
    except Exception as e:
        pytest.fail(f"Proper decoupling mechanism not implemented: {e}")


def test_no_import_at_module_level():
    """Test that problematic imports are not at module level."""
    # Read the source files to check for import patterns
    with open('user_manager.py', 'r') as f:
        user_mgr_content = f.read()
    
    with open('message_handler.py', 'r') as f:
        msg_handler_content = f.read()
    
    with open('notifications.py', 'r') as f:
        notifications_content = f.read()
    
    # Should not have direct imports at module level that create circular deps
    # This is a simplified check - actual implementation may vary
    lines_to_check = [
        ('user_manager.py', user_mgr_content),
        ('message_handler.py', msg_handler_content), 
        ('notifications.py', notifications_content)
    ]
    
    for filename, content in lines_to_check:
        lines = content.split('\n')
        for i, line in enumerate(lines[:20]):  # Check first 20 lines
            if line.strip().startswith('from ') and any(
                module in line for module in ['user_manager', 'message_handler', 'notifications']
            ):
                # If found, should be conditional import or in function
                if i < 10:  # Top-level import area
                    pytest.fail(f"Potential circular import in {filename}: {line}")


if __name__ == "__main__":
    pytest.main([__file__])
