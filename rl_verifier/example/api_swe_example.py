import requests
import json

# Server URL
BASE_URL = "http://localhost:8000"

verification_info = {
    "type": "swe_verifiable",
    "answer": {
        "input": "def add(a, b):\n    return a + b",
        "ground_truth": "def add_plus_one(a, b):\n    return a + b + 1",
    },
}

llm_output = """### Solution
```python
def add_plus_one(a, b):\n    return a + b + 1
```"""


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
