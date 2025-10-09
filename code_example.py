class Calculator:
    """A simple calculator class with basic arithmetic operations."""

    def add(self, a: float, b: float) -> float:
        """Return the sum of two numbers."""
        return a + b

    def subtract(self, a: float, b: float) -> float:
        """Return the difference between two numbers."""
        return a - b

    def multiply(self, a: float, b: float) -> float:
        """Return the product of two numbers."""
        return a * b

    def divide(self, a: float, b: float) -> float:
        """Return the quotient of two numbers. Raises ValueError if b is zero."""
        if b == 0:
            raise ValueError("Cannot divide by zero.")
        return a / b
