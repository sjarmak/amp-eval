"""Flask app with scattered auth logic that needs refactoring."""
import jwt
import functools
from datetime import datetime, timedelta
from flask import Flask, request, jsonify

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'

# Hardcoded user data (should be in proper user service)
USERS = {
    'admin': {'password': 'admin123', 'role': 'admin'},
    'user': {'password': 'user123', 'role': 'user'},
    'guest': {'password': 'guest123', 'role': 'guest'}
}


@app.route('/login', methods=['POST'])
def login():
    """Login endpoint with embedded JWT logic."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Auth logic scattered here (should be in auth service)
    if username in USERS and USERS[username]['password'] == password:
        # JWT creation logic (should be in auth service)
        payload = {
            'username': username,
            'role': USERS[username]['role'],
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
        return jsonify({'token': token, 'role': USERS[username]['role']})
    
    return jsonify({'error': 'Invalid credentials'}), 401


@app.route('/admin/users', methods=['GET'])
def get_users():
    """Admin endpoint with embedded auth checks."""
    # Token validation logic (should be middleware)
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return jsonify({'error': 'Token required'}), 401
    
    try:
        # JWT decoding logic (should be in auth service)
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        # Role check logic (should be in RBAC service)
        if payload.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    
    return jsonify({'users': list(USERS.keys())})


@app.route('/profile', methods=['GET'])
def get_profile():
    """Profile endpoint with duplicated auth logic."""
    # Duplicate token validation (should be middleware)
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return jsonify({'error': 'Token required'}), 401
    
    try:
        # Duplicate JWT decoding (should be centralized)
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        username = payload.get('username')
        role = payload.get('role')
        return jsonify({'username': username, 'role': role})
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401


@app.route('/user/data', methods=['GET'])
def get_user_data():
    """User endpoint with more duplicated auth logic."""
    # Yet another copy of token validation
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return jsonify({'error': 'Token required'}), 401
    
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        # Role check for user or admin (should be in RBAC)
        if payload.get('role') not in ['user', 'admin']:
            return jsonify({'error': 'User access required'}), 403
        
        return jsonify({'data': 'User specific data'})
    except jwt.ExpiredSignatureError:
        return jsonResponse({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401


if __name__ == '__main__':
    app.run(debug=True)
