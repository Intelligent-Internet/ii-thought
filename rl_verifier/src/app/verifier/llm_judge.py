import os

from openai import OpenAI, AuthenticationError
from .base import BaseVerifier
from .exception import VerifierInitializationError

# Prompt is adapted from https://arxiv.org/pdf/2412.18925
PROMPT_TEMPLATE = """\
<Model Response>
{model_response}
</Model Response>

<Reference Answer>
{ground_truth}
</Reference Answer>

You are provided with a model-generated response (<Model Response>) and a reference answer (<Reference Answer>). Compare the model response with the reference answer and determine its correctness. Your task is to simply output "True" if the response is correct, and "False" otherwise"""


class LLMJudge(BaseVerifier):
    def __init__(
        self,
        model: str,
        base_url: str = None,
        api_key: str = None,
        max_tokens: int = 100,
        temperature: float = 0.0,
    ):
        self._init_openai_client(api_key, base_url)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

        try:
            available_models = self.client.models.list()
            if model not in [m.id for m in available_models]:
                raise VerifierInitializationError(
                    f"Model {model} is not available for LLM Judge Verifier at base_url {base_url}"
                )
        except AuthenticationError as e:
            raise VerifierInitializationError(str(e))

    def _init_openai_client(self, api_key: str, base_url: str):
        api_key = os.getenv("OPENAI_API_KEY") if not api_key else api_key
        if not api_key:
            raise VerifierInitializationError(
                "OPENAI_API_KEY is not set for LLM Judge Verifier"
            )
        if not base_url:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = OpenAI(api_key=api_key, base_url=base_url)

    def verify(self, llm_output: str, verification_info: dict) -> float:
        reference_answer = verification_info["answer"]["value"]
        prompt = PROMPT_TEMPLATE.format(
            model_response=llm_output, ground_truth=reference_answer
        )
        messages = [{"role": "user", "content": prompt}]
        print(messages)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        response = response.choices[0].message.content
        if response.lower().strip('"') == "true":
            return 1.0
        else:
            return 0.0
