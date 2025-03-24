import math_verify

from .base import BaseVerifier


def get_last_boxed(text: str):
    start_idx = text.rfind("\\boxed")
    if start_idx < 0:
        return None

    right_brace_idx = None
    num_left_braces_open = 0
    for i in range(start_idx, len(text)):
        if text[i] == "{":
            num_left_braces_open += 1
        if text[i] == "}":
            num_left_braces_open -= 1
            if num_left_braces_open == 0:
                right_brace_idx = i
                break

    if not right_brace_idx:
        return None
    return text[start_idx : right_brace_idx + 1]


class MathVerifier(BaseVerifier):
    def verify(self, llm_output: str, verification_info: dict) -> float:
        ground_truth = verification_info["answer"]["value"]
        # Extract the boxed answer from the prediction
        extracted_prediction = get_last_boxed(llm_output)

        # If the prediction is not in the correct format
        if not extracted_prediction:
            return 0.0

        # Parse the prediction and the ground truth
        parsed_prediction = math_verify.parse(extracted_prediction)
        parsed_ground_truth = math_verify.parse(f"\\boxed{{{ground_truth}}}")

        # Verify the prediction
        verified = math_verify.verify(parsed_prediction, parsed_ground_truth)
        return 1.0 if verified else 0.0
