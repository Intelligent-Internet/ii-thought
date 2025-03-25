import math_verify

from .base import BaseVerifier
from .utils import get_last_boxed


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
