import unicodedata
import re

from .base import BaseVerifier
from .utils import get_last_boxed, get_code_block


def contains_chinese_language(text: str) -> bool:
    return any("CJK" in unicodedata.name(char, "") for char in text if char.isalpha())


def contains_thinking_block(text: str) -> bool:
    return re.search(r"<think>.*?</think>", text, re.DOTALL) is not None


def contains_eos_token(text: str, eos_token="<｜end▁of▁sentence｜>"):
    # Deepseek eos_token
    return eos_token in text


class FormatVerifier(BaseVerifier):
    def verify(self, llm_output: str, verification_info: dict) -> float:
        if contains_chinese_language(llm_output):
            return 0.0
        if not contains_thinking_block(llm_output):
            return 0.0
        if not contains_eos_token(llm_output):
            return 0.0
        if verification_info["type"] == "math_verifiable" and not get_last_boxed(
            llm_output
        ):
            return 0.0
        if verification_info["type"] == "code_verifiable" and not get_code_block(
            llm_output, verification_info.get("language", "python")
        ):
            return 0.0

        return 1.0