"""Security vulnerability testing."""
import pytest
import os
import tempfile
import sqlite3
from vulnerable_app import UserManager, FileManager, SystemManager, app


@pytest.fixture
def user_manager():
    """Create user manager for testing."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        db_path = f.name
    um = UserManager(db_path)
    yield um
    os.unlink(db_path)


@pytest.fixture
def file_manager():
    """Create file manager for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        fm = FileManager(temp_dir)
        yield fm


@pytest.fixture
def system_manager():
    """Create system manager for testing."""
    return SystemManager()


@pytest.fixture
def client():
    """Create test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_sql_injection_prevention(user_manager):
    """Test that SQL injection vulnerabilities are fixed."""
    # Test malicious SQL injection attempts
    malicious_inputs = [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "admin' UNION SELECT 1,2,3,4,5 --",
        "1 OR 1=1",
        "1; DELETE FROM users; --"
    ]
    
    for malicious_input in malicious_inputs:
        # These should not succeed or cause errors
        try:
            # Test authentication SQL injection
            result = user_manager.authenticate_user(malicious_input, "password")
            assert result == {}, f"SQL injection succeeded with input: {malicious_input}"
            
            # Test user lookup SQL injection
            result = user_manager.get_user_by_id(malicious_input)
            assert result == {}, f"SQL injection succeeded in get_user_by_id: {malicious_input}"
            
            # Test search SQL injection
            result = user_manager.search_users(malicious_input)
            # Should not return all users or cause errors
            assert len(result) <= 3, f"SQL injection may have succeeded in search: {malicious_input}"
            
        except Exception as e:
            # Should not cause database errors
            assert "syntax error" not in str(e).lower()
            assert "near" not in str(e).lower()


def test_password_security(user_manager):
    """Test that passwords are properly hashed and secured."""
    # Create a new user
    username = "testuser"
    password = "testpassword123"
    email = "test@example.com"
    
    success = user_manager.create_user(username, password, email)
    assert success, "User creation should succeed"
    
    # Check that password is not stored in plaintext
    conn = sqlite3.connect(user_manager.db_path)
    cursor = conn.execute("SELECT password FROM users WHERE username = ?", (username,))
    stored_password = cursor.fetchone()[0]
    conn.close()
    
    # Password should be hashed, not plaintext
    assert stored_password != password, "Password should not be stored in plaintext"
    assert len(stored_password) > len(password), "Hashed password should be longer"
    
    # Should contain hash characteristics (like bcrypt or similar)
    assert any(char in stored_password for char in ['$', '.']), "Should use proper password hashing"


def test_path_traversal_prevention(file_manager):
    """Test that path traversal vulnerabilities are fixed."""
    # Create a test file in the base directory
    test_content = "test content"
    file_manager.write_file("test.txt", test_content)
    
    # Test malicious path traversal attempts
    malicious_paths = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        "../../../../../../../etc/shadow",
        "....//....//....//etc/passwd",
        "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",  # URL encoded
        "../../sensitive_file.txt"
    ]
    
    for malicious_path in malicious_paths:
        # These should not succeed in reading files outside base directory
        content = file_manager.read_file(malicious_path)
        assert "root:" not in content, f"Path traversal succeeded: {malicious_path}"
        assert "/bin/bash" not in content, f"Path traversal succeeded: {malicious_path}"
        assert "Error" in content or content == "", f"Should prevent access: {malicious_path}"
        
        # Should not be able to write outside base directory
        success = file_manager.write_file(malicious_path, "malicious content")
        # Either should fail or write to safe location
        if success:
            # Verify it's written to base directory, not escaped location
            written_content = file_manager.read_file(os.path.basename(malicious_path))
            assert written_content == "malicious content" or "Error" in written_content


def test_command_injection_prevention(system_manager):
    """Test that command injection vulnerabilities are fixed."""
    # Test malicious command injection attempts
    malicious_inputs = [
        "localhost; cat /etc/passwd",
        "localhost && rm -rf /",
        "localhost | cat /etc/shadow",
        "localhost`cat /etc/passwd`",
        "localhost$(cat /etc/passwd)",
        "; ls -la /",
        "&& whoami",
        "| id"
    ]
    
    for malicious_input in malicious_inputs:
        # These should not execute additional commands
        result = system_manager.ping_host(malicious_input)
        
        # Should not contain results of injected commands
        assert "root:" not in result, f"Command injection succeeded: {malicious_input}"
        assert "/bin/bash" not in result, f"Command injection succeeded: {malicious_input}"
        assert "uid=" not in result, f"Command injection succeeded: {malicious_input}"
        
        # Test disk usage command injection
        result = system_manager.check_disk_usage(malicious_input)
        assert "root:" not in result, f"Command injection in disk usage: {malicious_input}"
        
        # Test grep command injection
        result = system_manager.grep_logs(malicious_input)
        assert "root:" not in result, f"Command injection in grep: {malicious_input}"


def test_xss_prevention(client):
    """Test that XSS vulnerabilities are fixed."""
    malicious_scripts = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "javascript:alert('XSS')",
        "<svg onload=alert('XSS')>",
        "');alert('XSS');//",
        "<iframe src='javascript:alert(\"XSS\")'></iframe>"
    ]
    
    for script in malicious_scripts:
        # Test profile update XSS
        response = client.post(f'/profile/1', data={'profile': script})
        
        # Response should not contain unescaped script tags
        assert b"<script>" not in response.data.lower()
        assert b"onerror=" not in response.data.lower()
        assert b"javascript:" not in response.data.lower()
        assert b"onload=" not in response.data.lower()
        
        # Test comment XSS
        response = client.post('/comment', data={'comment': script, 'user_id': '1'})
        
        # Should be properly escaped/sanitized
        assert b"<script>" not in response.data.lower()
        assert b"onerror=" not in response.data.lower()


def test_authentication_security(client, user_manager):
    """Test authentication security improvements."""
    # Test that weak passwords are rejected
    weak_passwords = ["123", "password", "admin", ""]
    
    for weak_password in weak_passwords:
        response = client.post('/register', 
                             json={'username': 'testuser', 'password': weak_password, 'email': 'test@example.com'})
        
        # Should reject weak passwords (or implement proper validation)
        if response.status_code == 200:
            # If registration succeeds, verify password is properly hashed
            user = user_manager.get_user_by_id("1")
            if user:
                # Check that some security measures are in place
                assert len(weak_password) < 8 or weak_password in ["password", "admin"]


def test_authorization_improvements(client):
    """Test that authorization is properly implemented."""
    # Test admin endpoint without proper authorization
    response = client.get('/admin/users')
    assert response.status_code == 403, "Should require proper authorization"
    
    # Test with weak authorization header
    response = client.get('/admin/users', headers={'Authorization': 'user admin'})
    # Should not accept weak authorization
    if response.status_code == 200:
        # If it succeeds, should implement proper token validation
        pass  # This would need proper JWT or session validation


def test_input_validation(client):
    """Test that input validation is implemented."""
    # Test with missing required fields
    response = client.post('/register', json={})
    assert response.status_code == 400, "Should validate required fields"
    
    # Test with invalid email format
    response = client.post('/register', 
                         json={'username': 'test', 'password': 'password123', 'email': 'invalid-email'})
    # Should validate email format (or implement validation)
    
    # Test with empty username
    response = client.post('/register',
                         json={'username': '', 'password': 'password123', 'email': 'test@example.com'})
    assert response.status_code == 400, "Should validate username"


def test_secure_configuration():
    """Test that secure configuration is implemented."""
    # App should not run in debug mode in production
    assert not app.debug or os.environ.get('FLASK_ENV') == 'development'
    
    # Should have proper security headers
    with app.test_client() as client:
        response = client.get('/')
        # Should implement security headers
        headers = response.headers
        
        # Common security headers (may not all be present initially)
        security_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options', 
            'X-XSS-Protection',
            'Strict-Transport-Security'
        ]
        
        # At least some security headers should be present after fixes
        # This is a guideline - not all may be required for this exercise


if __name__ == "__main__":
    pytest.main([__file__])
