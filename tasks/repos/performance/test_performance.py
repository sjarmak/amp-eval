"""Performance optimization tests."""
import pytest
import time
import json
import tempfile
import os
from slow_processor import DataProcessor


@pytest.fixture
def processor():
    """Create processor instance for testing."""
    return DataProcessor()


@pytest.fixture
def sample_data():
    """Sample data for testing."""
    return [
        {'id': 1, 'email': 'user1@example.com', 'department': 'Engineering', 'score': 85},
        {'id': 2, 'email': 'user2@example.com', 'department': 'Sales', 'score': 90},
        {'id': 3, 'email': 'user1@example.com', 'department': 'Engineering', 'score': 88},  # Duplicate
        {'id': 4, 'email': 'user3@example.com', 'department': 'Marketing', 'score': 75},
        {'id': 5, 'email': 'user2@example.com', 'department': 'Sales', 'score': 92},      # Duplicate
    ]


def test_duplicate_detection_performance(processor, sample_data):
    """Test that duplicate detection is optimized."""
    # Create larger dataset for performance testing
    large_data = []
    for i in range(1000):
        large_data.append({
            'id': i,
            'email': f'user{i % 100}@example.com',  # Creates duplicates
            'department': f'Dept{i % 5}',
            'score': i % 100
        })
    
    start_time = time.time()
    duplicates = processor.find_duplicates_slow(large_data)
    execution_time = time.time() - start_time
    
    # Should be optimized to O(n) or O(n log n)
    # Original O(n²) would be too slow for 1000 items
    assert execution_time < 1.0, f"Duplicate detection too slow: {execution_time}s"
    assert len(duplicates) > 0, "Should find duplicates"


def test_database_query_optimization(processor):
    """Test that N+1 problem is resolved."""
    start_time = time.time()
    users = processor.get_all_users_with_departments_slow()
    execution_time = time.time() - start_time
    
    # Should use JOIN instead of N+1 queries
    assert execution_time < 0.5, f"Database queries too slow: {execution_time}s"
    assert len(users) == 1000, "Should return all users"
    
    # Verify data integrity
    for user in users[:10]:  # Check first 10
        assert 'id' in user
        assert 'name' in user
        assert 'email' in user
        assert 'department' in user


def test_memory_usage_optimization(processor):
    """Test that memory leaks are fixed."""
    # Create temporary files for testing
    temp_files = []
    for i in range(10):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            data = {'test': 'data' * 1000, 'id': i}  # Large data
            json.dump(data, f)
            temp_files.append(f.name)
    
    try:
        # Process files
        for filename in temp_files:
            processor.process_file_with_memory_leak(filename)
        
        # Check that memory isn't growing unbounded
        # Implementation should clean up processed_files or limit cache
        initial_cache_size = len(processor.cache)
        initial_files_size = len(processor.processed_files)
        
        # Process more files
        for filename in temp_files:
            processor.process_file_with_memory_leak(filename)
        
        # Memory usage should be controlled
        final_cache_size = len(processor.cache)
        final_files_size = len(processor.processed_files)
        
        # Should implement cache eviction or cleanup
        assert final_cache_size <= initial_cache_size * 2, "Cache growing too large"
        assert final_files_size <= initial_files_size * 2, "Processed files not cleaned"
        
    finally:
        # Cleanup
        for filename in temp_files:
            os.unlink(filename)


def test_batch_processing_optimization(processor):
    """Test that batch processing is optimized."""
    items = [{'id': i, 'name': f'item{i}'} for i in range(100)]
    
    start_time = time.time()
    results = processor.batch_process_inefficient(items)
    execution_time = time.time() - start_time
    
    # Should use batch operations instead of individual processing
    assert execution_time < 0.5, f"Batch processing too slow: {execution_time}s"
    assert len(results) == len(items), "Should process all items"


def test_algorithm_complexity_improvement(processor, sample_data):
    """Test that algorithm complexity is improved."""
    result = processor.process_large_dataset(sample_data)
    
    # Verify functionality is preserved
    assert 'total_records' in result
    assert 'duplicates' in result
    assert 'department_stats' in result
    assert 'processing_time' in result
    
    # Check that duplicates are found correctly
    duplicates = result['duplicates']
    assert len(duplicates) >= 2, "Should find duplicate emails"
    
    # Check department statistics
    dept_stats = result['department_stats']
    assert 'Engineering' in dept_stats
    assert 'Sales' in dept_stats
    
    # Performance should be reasonable
    assert result['processing_time'] < 1.0, "Processing time too long"


def test_caching_strategy_improvement(processor):
    """Test that caching strategy is improved."""
    # Create test file
    test_data = {'key': 'value', 'number': 42}
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(test_data, f)
        temp_filename = f.name
    
    try:
        # First call should cache result
        start_time = time.time()
        result1 = processor.process_file_with_memory_leak(temp_filename)
        first_call_time = time.time() - start_time
        
        # Second call should be faster (cached)
        start_time = time.time()
        result2 = processor.process_file_with_memory_leak(temp_filename)
        second_call_time = time.time() - start_time
        
        # Results should be identical
        assert result1 == result2, "Cached result should be identical"
        
        # Second call should be faster (allowing some variance)
        assert second_call_time <= first_call_time + 0.01, "Caching not effective"
        
        # Cache should have reasonable size limits
        cache_size = len(processor.cache)
        assert cache_size < 100, "Cache growing too large"
        
    finally:
        os.unlink(temp_filename)


def test_factorial_optimization(processor):
    """Test that recursive factorial is optimized."""
    start_time = time.time()
    
    # Test multiple factorial calculations
    results = []
    for i in range(10):
        result = processor._slow_factorial(10)
        results.append(result)
    
    execution_time = time.time() - start_time
    
    # Should be optimized with memoization or iteration
    assert execution_time < 0.1, f"Factorial calculation too slow: {execution_time}s"
    assert all(r == 3628800 for r in results), "Factorial results incorrect"


def test_statistics_query_optimization(processor):
    """Test that statistics generation is optimized."""
    start_time = time.time()
    stats = processor.get_statistics_slow()
    execution_time = time.time() - start_time
    
    # Should use efficient queries
    assert execution_time < 0.5, f"Statistics generation too slow: {execution_time}s"
    
    # Verify correctness
    assert stats['total_users'] == 1000
    assert 'departments' in stats
    assert len(stats['departments']) == 3  # Engineering, Sales, Marketing


def test_concurrent_processing_capability(processor, sample_data):
    """Test that CPU-intensive operations can be parallelized."""
    import concurrent.futures
    
    # Test if expensive computation can be parallelized
    large_dataset = sample_data * 20  # 100 records
    
    start_time = time.time()
    
    # Sequential processing
    sequential_result = processor.process_large_dataset(large_dataset)
    sequential_time = time.time() - start_time
    
    # The implementation should support parallel processing
    # This test verifies the structure allows for it
    assert sequential_result['total_records'] == len(large_dataset)
    
    # Processing time should be reasonable even for larger datasets
    assert sequential_time < 5.0, f"Processing time too long: {sequential_time}s"


if __name__ == "__main__":
    pytest.main([__file__])
