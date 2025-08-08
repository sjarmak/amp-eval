import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from broken_calculator import add, subtract, multiply, divide, get_operations

def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0

def test_subtract():
    assert subtract(5, 3) == 2
    assert subtract(0, 5) == -5

def test_multiply():
    assert multiply(3, 4) == 12
    assert multiply(-2, 3) == -6

def test_divide():
    assert divide(10, 2) == 5
    assert divide(7, 2) == 3.5

def test_divide_by_zero():
    with pytest.raises(ValueError):
        divide(5, 0)

def test_get_operations():
    ops = get_operations()
    assert len(ops) == 4
    assert "add" in ops
    assert "subtract" in ops
