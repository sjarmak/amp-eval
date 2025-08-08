# Fibonacci - Infinite Loop Demo
# This implementation has an infinite loop bug

def fibonacci(n):
    """Calculate the nth Fibonacci number - but this has a bug."""
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        a, b = 0, 1
        i = 2
        while i <= n:  # Bug: condition creates infinite loop when n is negative
            a, b = b, a + b
            # Bug: forgot to increment i
        return b

def fibonacci_sequence(count):
    """Generate a sequence of Fibonacci numbers."""
    sequence = []
    for i in range(count):
        sequence.append(fibonacci(i))
    return sequence
