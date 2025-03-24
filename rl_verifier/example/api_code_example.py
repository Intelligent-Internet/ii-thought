import requests
import json

# Server URL
BASE_URL = "http://localhost:8000"

problem = """Let's consider two integers, which you need to sum up.

You are given two integers **a** and **b**. Your task is to determine their sum.

### Input  

The first line contains an integer **a** (-10⁹ ≤ a ≤ 10⁹).  
The second line contains an integer **b** (-10⁹ ≤ b ≤ 10⁹).  

### Output  

Print a single integer — the sum of **a** and **b**.  

### Examples  

#### Input  
```
3
5
```
#### Output  
```
8
```"""

llm_output = """Here's a simple Python solution for the problem:  

```python
a = int(input())
b = int(input())
print(a + b)
```

This program reads two integers from standard input, computes their sum, and prints the result. It works efficiently within the given constraints. 🚀"""

# Expected score is 0.6667
verification_info = {
    "answer": {
        "test_cases": [
            {"input": "3\n5", "output": "8"},
            {"input": "-10\n4", "output": "-6"},
            {"input": "1\n1", "output": "3"},  # Try wrong output
        ],
    },
    "type": "code_verifiable",
}

payload = {"llm_output": llm_output, "verification_info": json.dumps(verification_info)}

try:
    response = requests.post(f"{BASE_URL}/reward", json=payload)

    if response.status_code == 200:
        result = response.json()
        print(f"Score received: {result['score']}")
    else:
        print(f"Error: {response.status_code}")
        print(f"Message: {response.json()['detail']}")

except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
