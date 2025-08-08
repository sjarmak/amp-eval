import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from text_processor import reverse_string, uppercase, word_count, remove_whitespace

def test_reverse():
    assert reverse_string("hello") == "olleh"
    assert reverse_string("python") == "nohtyp"
    assert reverse_string("") == ""
    assert reverse_string("a") == "a"

def test_uppercase():
    assert uppercase("hello") == "HELLO"
    assert uppercase("Python") == "PYTHON"

def test_word_count():
    assert word_count("hello world") == 2
    assert word_count("one") == 1
    assert word_count("") == 1  # split() on empty string returns ['']

def test_remove_whitespace():
    assert remove_whitespace("hello world") == "helloworld"
    assert remove_whitespace("  python  ") == "python"
