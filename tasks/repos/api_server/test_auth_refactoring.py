"""Tests for auth refactoring."""
import pytest
import json
from app import app


@pytest.fixture
def client():
    """Test client fixture."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_auth_middleware_exists():
    """Test that auth middleware is properly implemented."""
    try:
        from auth_middleware import AuthMiddleware
        assert AuthMiddleware is not None
    except ImportError:
        pytest.fail("AuthMiddleware not implemented")


def test_auth_service_exists():
    """Test that auth service is properly extracted."""
    try:
        from auth_service import AuthService
        auth_service = AuthService()
        assert hasattr(auth_service, 'create_token')
        assert hasattr(auth_service, 'validate_token')
        assert hasattr(auth_service, 'authenticate_user')
    except ImportError:
        pytest.fail("AuthService not properly implemented")


def test_rbac_service_exists():
    """Test that RBAC service is implemented."""
    try:
        from rbac_service import RBACService
        rbac = RBACService()
        assert hasattr(rbac, 'check_permission')
        assert hasattr(rbac, 'has_role')
    except ImportError:
        pytest.fail("RBACService not implemented")


def test_auth_decorators_exist():
    """Test that auth decorators are implemented."""
    try:
        from auth_decorators import require_auth, require_role
        assert require_auth is not None
        assert require_role is not None
    except ImportError:
        pytest.fail("Auth decorators not implemented")


def test_login_functionality(client):
    """Test that login still works after refactoring."""
    response = client.post('/login', 
                          data=json.dumps({'username': 'admin', 'password': 'admin123'}),
                          content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'token' in data
    assert data['role'] == 'admin'


def test_admin_endpoint_protection(client):
    """Test that admin endpoints are properly protected."""
    # Test without token
    response = client.get('/admin/users')
    assert response.status_code == 401
    
    # Test with user token (should fail)
    login_response = client.post('/login',
                               data=json.dumps({'username': 'user', 'password': 'user123'}),
                               content_type='application/json')
    token = json.loads(login_response.data)['token']
    
    response = client.get('/admin/users', 
                         headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 403


def test_user_endpoint_access(client):
    """Test that user endpoints work correctly."""
    # Login as user
    login_response = client.post('/login',
                               data=json.dumps({'username': 'user', 'password': 'user123'}),
                               content_type='application/json')
    token = json.loads(login_response.data)['token']
    
    # Access user endpoint
    response = client.get('/user/data',
                         headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__])
