"""Performance-critical code with optimization opportunities."""
import time
import sqlite3
from typing import List, Dict, Any
import json


class DataProcessor:
    """Data processor with performance issues."""
    
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.cache = {}  # Poor caching implementation
        self.processed_files = []  # Memory leak - never cleared
        self.setup_database()
    
    def setup_database(self):
        """Setup test database."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT,
                email TEXT,
                department_id INTEGER
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """)
        
        # Insert test data
        departments = [
            (1, "Engineering"),
            (2, "Sales"), 
            (3, "Marketing")
        ]
        conn.executemany("INSERT OR REPLACE INTO departments VALUES (?, ?)", departments)
        
        users = []
        for i in range(1000):
            users.append((i, f"User{i}", f"user{i}@example.com", (i % 3) + 1))
        conn.executemany("INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?)", users)
        conn.commit()
        conn.close()
    
    def find_duplicates_slow(self, data: List[Dict]) -> List[Dict]:
        """Inefficient O(n²) duplicate detection - NEEDS OPTIMIZATION."""
        duplicates = []
        
        # O(n²) algorithm - very slow for large datasets
        for i in range(len(data)):
            for j in range(i + 1, len(data)):
                if data[i]['email'] == data[j]['email']:
                    if data[i] not in duplicates:
                        duplicates.append(data[i])
                    if data[j] not in duplicates:
                        duplicates.append(data[j])
        
        return duplicates
    
    def process_large_dataset(self, dataset: List[Dict]) -> Dict[str, Any]:
        """Process large dataset with performance issues."""
        start_time = time.time()
        
        # Inefficient processing - should be optimized
        result = {
            'total_records': len(dataset),
            'duplicates': [],
            'department_stats': {},
            'processing_time': 0
        }
        
        # Slow duplicate detection
        result['duplicates'] = self.find_duplicates_slow(dataset)
        
        # Inefficient aggregation - recalculates everything
        for record in dataset:
            dept = record.get('department', 'Unknown')
            if dept not in result['department_stats']:
                result['department_stats'][dept] = {
                    'count': 0,
                    'avg_score': 0,
                    'total_score': 0
                }
            
            # Poor aggregation logic
            result['department_stats'][dept]['count'] += 1
            result['department_stats'][dept]['total_score'] += record.get('score', 0)
            # Recalculating average every time - inefficient
            result['department_stats'][dept]['avg_score'] = (
                result['department_stats'][dept]['total_score'] / 
                result['department_stats'][dept]['count']
            )
        
        result['processing_time'] = time.time() - start_time
        return result
    
    def get_user_with_department_slow(self, user_id: int) -> Dict:
        """Inefficient database query with N+1 problem."""
        conn = sqlite3.connect(self.db_path)
        
        # First query to get user
        cursor = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return {}
        
        # N+1 problem - separate query for department
        cursor = conn.execute("SELECT name FROM departments WHERE id = ?", (user[3],))
        department = cursor.fetchone()
        
        conn.close()
        
        return {
            'id': user[0],
            'name': user[1], 
            'email': user[2],
            'department': department[0] if department else 'Unknown'
        }
    
    def get_all_users_with_departments_slow(self) -> List[Dict]:
        """Very inefficient - N+1 queries problem."""
        conn = sqlite3.connect(self.db_path)
        
        # Get all users
        cursor = conn.execute("SELECT id FROM users")
        user_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        # N+1 problem - query each user individually
        users = []
        for user_id in user_ids:
            user = self.get_user_with_department_slow(user_id)
            users.append(user)
        
        return users
    
    def process_file_with_memory_leak(self, filename: str) -> Dict:
        """File processing with memory leak."""
        # Memory leak - files are never cleaned up
        with open(filename, 'r') as f:
            content = f.read()
            # Keep reference to large data - causes memory leak
            self.processed_files.append({
                'filename': filename,
                'content': content,  # Keeping full content in memory
                'size': len(content),
                'timestamp': time.time()
            })
        
        # Inefficient JSON parsing and processing
        try:
            data = json.loads(content)
            
            # Poor caching - cache never expires or is cleaned
            cache_key = f"file_{filename}"
            if cache_key not in self.cache:
                # Expensive computation every time
                processed_data = self._expensive_computation(data)
                self.cache[cache_key] = processed_data
            
            return self.cache[cache_key]
        except json.JSONDecodeError:
            return {'error': 'Invalid JSON'}
    
    def _expensive_computation(self, data: Dict) -> Dict:
        """Simulated expensive computation that could be optimized."""
        # Simulate CPU-intensive work that could be parallelized
        result = {}
        
        if isinstance(data, dict):
            for key, value in data.items():
                # Inefficient string operations
                processed_key = key.upper().replace(' ', '_').replace('-', '_')
                
                if isinstance(value, (int, float)):
                    # Expensive mathematical operations
                    result[processed_key] = {
                        'original': value,
                        'squared': value ** 2,
                        'sqrt': value ** 0.5,
                        'factorial': self._slow_factorial(min(int(abs(value)), 10))
                    }
                elif isinstance(value, str):
                    # Inefficient string processing
                    result[processed_key] = {
                        'original': value,
                        'length': len(value),
                        'words': len(value.split()),
                        'chars': [c for c in value]  # Memory inefficient
                    }
        
        return result
    
    def _slow_factorial(self, n: int) -> int:
        """Inefficient recursive factorial - should use iteration or memoization."""
        if n <= 1:
            return 1
        return n * self._slow_factorial(n - 1)
    
    def batch_process_inefficient(self, items: List[Any]) -> List[Any]:
        """Inefficient batch processing."""
        results = []
        
        # Processing one by one instead of batch operations
        for item in items:
            # Simulate individual database operations
            time.sleep(0.001)  # Simulate I/O delay
            
            # Inefficient data transformation
            if isinstance(item, dict):
                transformed = {}
                for k, v in item.items():
                    # Expensive operations on each item
                    transformed[k.upper()] = str(v).lower()
                results.append(transformed)
            else:
                results.append(str(item).upper())
        
        return results
    
    def get_statistics_slow(self) -> Dict:
        """Generate statistics with poor performance."""
        # Inefficient data gathering
        all_users = self.get_all_users_with_departments_slow()  # N+1 problem
        
        stats = {
            'total_users': len(all_users),
            'departments': {},
            'cache_size': len(self.cache),
            'processed_files': len(self.processed_files)
        }
        
        # Inefficient aggregation
        for user in all_users:
            dept = user['department']
            if dept not in stats['departments']:
                stats['departments'][dept] = 0
            stats['departments'][dept] += 1
        
        return stats
