"""Web application with security vulnerabilities."""
import sqlite3
import os
import subprocess
import hashlib
from flask import Flask, request, jsonify, render_template_string
from typing import Dict, List, Any


app = Flask(__name__)


class UserManager:
    """User manager with security vulnerabilities."""
    
    def __init__(self, db_path: str = "users.db"):
        self.db_path = db_path
        self.setup_database()
    
    def setup_database(self):
        """Setup database with test data."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                password TEXT,
                email TEXT,
                role TEXT DEFAULT 'user',
                profile TEXT
            )
        """)
        
        # Insert test users with weak passwords
        test_users = [
            ("admin", "admin123", "admin@example.com", "admin", "Admin user"),
            ("user1", "password", "user1@example.com", "user", "Regular user"),
            ("guest", "guest", "guest@example.com", "guest", "Guest user")
        ]
        
        for username, password, email, role, profile in test_users:
            # VULNERABILITY: Plain text password storage
            conn.execute(
                "INSERT OR REPLACE INTO users (username, password, email, role, profile) VALUES (?, ?, ?, ?, ?)",
                (username, password, email, role, profile)
            )
        
        conn.commit()
        conn.close()
    
    def authenticate_user(self, username: str, password: str) -> Dict:
        """Authenticate user - VULNERABLE TO SQL INJECTION."""
        conn = sqlite3.connect(self.db_path)
        
        # VULNERABILITY: SQL Injection
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
        cursor = conn.execute(query)
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'email': user[3],
                'role': user[4],
                'profile': user[5]
            }
        return {}
    
    def get_user_by_id(self, user_id: str) -> Dict:
        """Get user by ID - VULNERABLE TO SQL INJECTION."""
        conn = sqlite3.connect(self.db_path)
        
        # VULNERABILITY: SQL Injection via string concatenation
        query = "SELECT * FROM users WHERE id = " + user_id
        cursor = conn.execute(query)
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'email': user[3],
                'role': user[4],
                'profile': user[5]
            }
        return {}
    
    def search_users(self, search_term: str) -> List[Dict]:
        """Search users - VULNERABLE TO SQL INJECTION."""
        conn = sqlite3.connect(self.db_path)
        
        # VULNERABILITY: SQL Injection in LIKE clause
        query = f"SELECT id, username, email, role FROM users WHERE username LIKE '%{search_term}%' OR email LIKE '%{search_term}%'"
        cursor = conn.execute(query)
        users = cursor.fetchall()
        conn.close()
        
        return [
            {'id': user[0], 'username': user[1], 'email': user[2], 'role': user[3]}
            for user in users
        ]
    
    def update_user_profile(self, user_id: str, profile: str) -> bool:
        """Update user profile - VULNERABLE TO SQL INJECTION."""
        conn = sqlite3.connect(self.db_path)
        
        # VULNERABILITY: SQL Injection in UPDATE
        query = f"UPDATE users SET profile = '{profile}' WHERE id = {user_id}"
        try:
            conn.execute(query)
            conn.commit()
            conn.close()
            return True
        except Exception:
            conn.close()
            return False
    
    def create_user(self, username: str, password: str, email: str) -> bool:
        """Create new user - INSECURE PASSWORD STORAGE."""
        conn = sqlite3.connect(self.db_path)
        
        try:
            # VULNERABILITY: Plain text password storage
            conn.execute(
                "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                (username, password, email)
            )
            conn.commit()
            conn.close()
            return True
        except Exception:
            conn.close()
            return False


class FileManager:
    """File manager with path traversal vulnerabilities."""
    
    def __init__(self, base_dir: str = "uploads"):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)
    
    def read_file(self, filename: str) -> str:
        """Read file - VULNERABLE TO PATH TRAVERSAL."""
        # VULNERABILITY: No path validation
        file_path = os.path.join(self.base_dir, filename)
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {e}"
    
    def write_file(self, filename: str, content: str) -> bool:
        """Write file - VULNERABLE TO PATH TRAVERSAL."""
        # VULNERABILITY: No path validation
        file_path = os.path.join(self.base_dir, filename)
        try:
            with open(file_path, 'w') as f:
                f.write(content)
            return True
        except Exception:
            return False
    
    def list_files(self, directory: str = ".") -> List[str]:
        """List files - VULNERABLE TO PATH TRAVERSAL."""
        # VULNERABILITY: User can access any directory
        full_path = os.path.join(self.base_dir, directory)
        try:
            return os.listdir(full_path)
        except Exception:
            return []
    
    def delete_file(self, filename: str) -> bool:
        """Delete file - VULNERABLE TO PATH TRAVERSAL."""
        # VULNERABILITY: Can delete files outside base directory
        file_path = os.path.join(self.base_dir, filename)
        try:
            os.remove(file_path)
            return True
        except Exception:
            return False


class SystemManager:
    """System manager with command injection vulnerabilities."""
    
    def ping_host(self, hostname: str) -> str:
        """Ping host - VULNERABLE TO COMMAND INJECTION."""
        # VULNERABILITY: Direct command execution without validation
        try:
            result = subprocess.run(
                f"ping -c 1 {hostname}",
                shell=True,
                capture_output=True,
                text=True
            )
            return result.stdout
        except Exception as e:
            return f"Error: {e}"
    
    def check_disk_usage(self, path: str) -> str:
        """Check disk usage - VULNERABLE TO COMMAND INJECTION."""
        # VULNERABILITY: Command injection in path parameter
        try:
            result = subprocess.run(
                f"du -sh {path}",
                shell=True,
                capture_output=True,
                text=True
            )
            return result.stdout
        except Exception as e:
            return f"Error: {e}"
    
    def grep_logs(self, pattern: str, log_file: str = "/var/log/app.log") -> str:
        """Search logs - VULNERABLE TO COMMAND INJECTION."""
        # VULNERABILITY: Both pattern and file path can be exploited
        try:
            result = subprocess.run(
                f"grep '{pattern}' {log_file}",
                shell=True,
                capture_output=True,
                text=True
            )
            return result.stdout
        except Exception as e:
            return f"Error: {e}"


# Initialize managers
user_manager = UserManager()
file_manager = FileManager()
system_manager = SystemManager()


@app.route('/login', methods=['POST'])
def login():
    """Login endpoint - vulnerable to SQL injection."""
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')
    
    user = user_manager.authenticate_user(username, password)
    if user:
        return jsonify({'success': True, 'user': user})
    return jsonify({'success': False, 'error': 'Invalid credentials'}), 401


@app.route('/user/<user_id>')
def get_user(user_id):
    """Get user endpoint - vulnerable to SQL injection."""
    user = user_manager.get_user_by_id(user_id)
    if user:
        return jsonify(user)
    return jsonify({'error': 'User not found'}), 404


@app.route('/search')
def search_users():
    """Search users - vulnerable to SQL injection."""
    query = request.args.get('q', '')
    users = user_manager.search_users(query)
    return jsonify({'users': users})


@app.route('/profile/<user_id>', methods=['POST'])
def update_profile(user_id):
    """Update profile - vulnerable to XSS and SQL injection."""
    profile = request.form.get('profile', '')
    
    if user_manager.update_user_profile(user_id, profile):
        # VULNERABILITY: XSS via template injection
        template = f"<h1>Profile Updated</h1><p>New profile: {profile}</p>"
        return render_template_string(template)
    
    return "Error updating profile", 400


@app.route('/file/<filename>')
def read_file(filename):
    """Read file - vulnerable to path traversal."""
    content = file_manager.read_file(filename)
    return jsonify({'content': content})


@app.route('/file/<filename>', methods=['POST'])
def write_file(filename):
    """Write file - vulnerable to path traversal."""
    content = request.form.get('content', '')
    if file_manager.write_file(filename, content):
        return jsonify({'success': True})
    return jsonify({'success': False}), 400


@app.route('/files')
def list_files():
    """List files - vulnerable to path traversal."""
    directory = request.args.get('dir', '.')
    files = file_manager.list_files(directory)
    return jsonify({'files': files})


@app.route('/ping')
def ping():
    """Ping endpoint - vulnerable to command injection."""
    hostname = request.args.get('host', 'localhost')
    result = system_manager.ping_host(hostname)
    return jsonify({'result': result})


@app.route('/disk-usage')
def disk_usage():
    """Disk usage - vulnerable to command injection."""
    path = request.args.get('path', '/tmp')
    result = system_manager.check_disk_usage(path)
    return jsonify({'result': result})


@app.route('/search-logs')
def search_logs():
    """Search logs - vulnerable to command injection."""
    pattern = request.args.get('pattern', 'error')
    log_file = request.args.get('file', '/var/log/app.log')
    result = system_manager.grep_logs(pattern, log_file)
    return jsonify({'result': result})


@app.route('/register', methods=['POST'])
def register():
    """Register new user - insecure password storage."""
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')
    email = data.get('email', '')
    
    # VULNERABILITY: No input validation
    if user_manager.create_user(username, password, email):
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Registration failed'}), 400


@app.route('/admin/users')
def admin_users():
    """Admin endpoint - no proper authorization check."""
    # VULNERABILITY: No proper role-based access control
    auth_header = request.headers.get('Authorization', '')
    if 'admin' in auth_header:  # Weak authorization check
        users = user_manager.search_users('')
        return jsonify({'users': users})
    return jsonify({'error': 'Unauthorized'}), 403


@app.route('/comment', methods=['POST'])
def add_comment():
    """Add comment - vulnerable to XSS."""
    comment = request.form.get('comment', '')
    user_id = request.form.get('user_id', '1')
    
    # VULNERABILITY: Stored XSS
    template = f"""
    <div class="comment">
        <p>User {user_id} says:</p>
        <div class="comment-text">{comment}</div>
    </div>
    """
    return render_template_string(template)


if __name__ == '__main__':
    app.run(debug=True)  # VULNERABILITY: Debug mode in production
