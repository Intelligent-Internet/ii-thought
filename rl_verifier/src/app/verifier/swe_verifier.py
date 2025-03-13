# Adapted from https://github.com/facebookresearch/swe-rl/blob/main/src/swerl/core/reward.py

import re
import difflib

from .base import BaseVerifier


def extract_code_blocks(text):
    pattern = re.compile(r"```([\w#+]+)\n(.*?)```", re.DOTALL)

    matches = pattern.findall(text)

    if matches:
        _, code = matches[-1]  # Get the last match
        return code.strip()

    return None


def generate_unified_diff(
    old_code: str,
    new_code: str,
    n_context: int = 3,
) -> str:
    """Generate a unified diff between two code.

    Args:
        old_code: The original code.
        new_code: The modified code.
        n_context: The number of context lines to show.

    Returns:
        A string representing the unified diff."""

    original_lines = old_code.splitlines()
    modified_lines = new_code.splitlines()

    diff = difflib.unified_diff(
        original_lines,
        modified_lines,
        fromfile="old",
        tofile="new",
        lineterm="",
        n=n_context,
    )
    try:
        next(diff)
        next(diff)
        diff_code = "\n".join(diff)
        return diff_code
    except StopIteration:
        return ""


def compute_change_similarities(pred_diff: str, oracle_diff: str) -> float:
    if pred_diff == "" or oracle_diff == "":
        # Both are empty changes, meaning search = replace. We should penalize this to avoid
        # the model predicting empty changes to hack the reward.
        return 0.0

    else:
        change_similarity = difflib.SequenceMatcher(
            None,
            pred_diff,
            oracle_diff,
            autojunk=False,
        ).ratio()

        return change_similarity


class SWEVerifier(BaseVerifier):
    def verify(self, llm_output: str, verification_info: dict) -> float:
        input_code = verification_info["answer"]["input"].strip()
        reference_code = verification_info["answer"]["ground_truth"].strip()

        llm_output_code = extract_code_blocks(llm_output)
        if not llm_output_code:
            return 0.0

        oracle_diff = generate_unified_diff(input_code, reference_code)
        pred_diff = generate_unified_diff(input_code, llm_output_code)

        similarity = compute_change_similarities(pred_diff, oracle_diff)

        return similarity
