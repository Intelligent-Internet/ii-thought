from .base import BaseVerifier
from .instruction_following.evaluation_lib import InputExample, verify_instruction_following_strict

class IFVerifier(BaseVerifier):
    def verify(self, llm_output: str, verification_info: dict) -> float:
        verifier_input = InputExample(None, verification_info["answer"]["instruction_id_list"], verification_info["answer"]["prompt"], verification_info["answer"]["kwargs"])
        output = verify_instruction_following_strict(verifier_input, llm_output)
        return sum(output.follow_instruction_list) / len(output.follow_instruction_list)

