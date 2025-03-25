import re

from typing import Optional


def get_code_block(text: str, language: str) -> Optional[str]:
    """Extract the code block in the given language from the text.

    Args:
        text (str): The text to check
        language (str): The language of the code blocks to check for

    Returns:
        str: The code block in the given language, or None if not found
    """
    pattern = rf"```{language}\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)

    return match.group(1) if match else None


def get_last_boxed(text: str) -> Optional[str]:
    """Extract the last boxed expression (\\boxed{...}) from the text.

    Args:
        text (str): The text to check

    Returns:
        str: The last boxed expression, or None if not found
    """
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
