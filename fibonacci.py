def fibonacci(n):
    if n <= 0:
        return "Please enter a positive integer"
    if n == 1 or n == 2:
        return 1
    
    a, b = 1, 1
    for _ in range(3, n + 1):
        a, b = b, a + b
    return b

result = fibonacci(30)
print(f"The 30th term of the Fibonacci sequence is: {result}")