import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from fibonacci import fibonacci, fibonacci_sequence

def test_fibonacci():
    assert fibonacci(0) == 0
    assert fibonacci(1) == 1
    assert fibonacci(2) == 1
    assert fibonacci(3) == 2
    assert fibonacci(4) == 3
    assert fibonacci(5) == 5
    assert fibonacci(10) == 55

def test_fibonacci_sequence():
    seq = fibonacci_sequence(6)
    expected = [0, 1, 1, 2, 3, 5]
    assert seq == expected

def test_fibonacci_large():
    # This should not hang
    result = fibonacci(20)
    assert result == 6765
