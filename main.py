import os
import sys


def main():
    print("Hello World")

    # This is some unformatted code
    x = 1
    y = 2
    z = x + y

    if x == 1:
        print("x is 1")

    items = [1, 2, 3, 4, 5]
    for item in items:
        if item % 2 == 0:
            print(f"Even: {item}")
        else:
            print(f"Odd: {item}")


if __name__ == "__main__":
    main()
