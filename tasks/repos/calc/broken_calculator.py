# Broken Calculator - Syntax Error Demo
# This file contains intentional syntax errors for evaluation

def add(a, b)  # Missing colon
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

# Missing closing quote
def get_operations():
    return ["add", "subtract", "multiply", "divide]

if __name__ == "__main__":
    print("Calculator module loaded")
