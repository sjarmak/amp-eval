# Text Processor - Logic Error Demo
# The reverse function has a bug

def reverse_string(text):
    """Reverse a string - but this implementation is broken."""
    result = ""
    for i in range(len(text)):  # Bug: should be range(len(text)-1, -1, -1)
        result += text[i]
    return result

def uppercase(text):
    """Convert text to uppercase."""
    return text.upper()

def word_count(text):
    """Count words in text."""
    return len(text.split())

def remove_whitespace(text):
    """Remove all whitespace from text."""
    return text.replace(" ", "").replace("\t", "").replace("\n", "")
