from rl_verifier import RLVerifierClient

client = RLVerifierClient(base_url="http://localhost:8000")


# ############################################################
# Example 1: Single verification
verification_info = {
    "answer": {
        "test_cases": [
            {"input": "1\n1", "output": "3"},  # Try wrong output
            {"input": "3\n5", "output": "8"},
            {"input": "-10\n4", "output": "-6"},
        ],
    },
    "type": "code_verifiable",
}

llm_output = """<think>Here is my thinking process</think>

Here's a simple Python solution for the problem:  

```python
a = int(input())
b = int(input())
print(a + b)
```

This program reads two integers from standard input, computes their sum, and prints the result. It works efficiently within the given constraints. 🚀"""

score = client.verify(llm_output, verification_info)
print("Single verification score: ", score)

# ############################################################


# ############################################################
# Example 2: Batch verification
verification_info_math = {
        "answer": {
            "value": "15",
        },
        "type": "math_verifiable"
    }

scores = client.verify_batch(
    batch=[
        ("The final answer: \\boxed{7 + 8}", verification_info_math),
        ("The final answer: \\boxed{15}", verification_info_math),
        ("The final answer: \\boxed{-1}", verification_info_math),
        ("最终答案: \\boxed{15}", verification_info_math),
    ]
)

print("Batch verification scores: ", scores)

# ############################################################