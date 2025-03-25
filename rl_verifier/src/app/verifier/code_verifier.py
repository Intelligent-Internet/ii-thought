import requests

from sandbox_fusion import (
    run_concurrent,
    submit,
    SubmitRequest,
    TestConfig,
    set_endpoint,
)
from .base import BaseVerifier
from .exception import VerifierInitializationError
from .utils import get_code_block


class CodeVerifier(BaseVerifier):
    def __init__(
        self,
        base_url: str,
        timeout: float = 30,
        max_attempts: int = 1,
        concurrency: int = 5,
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.max_attempts = max_attempts
        self.concurrency = concurrency

        self._validate_base_url(self.base_url)
        set_endpoint(self.base_url)

    def _validate_base_url(self, base_url: str) -> bool:
        if not base_url or not base_url.strip():
            raise VerifierInitializationError(
                "Fusion Sandbox base URL cannot be empty."
            )
        try:
            requests.get(f"{base_url}/v1/ping", timeout=5)
        except:
            raise VerifierInitializationError(
                f"Failed to connect Fusion Sandbox at '{self.base_url}'."
            )

    def verify(self, llm_output: str, verification_info: dict) -> float:
        test_cases = verification_info["answer"]["test_cases"]
        language = verification_info["answer"].get("language", "python")

        if not get_code_block(llm_output, language):
            return 0.0

        fmt_test_cases = [
            {"input": {"stdin": tc["input"]}, "output": {"stdout": tc["output"]}}
            for tc in test_cases
        ]

        kwargs = []
        for idx, tc in enumerate(fmt_test_cases):
            submit_request = SubmitRequest(
                dataset="custom_dataset",
                id=idx,
                completion=llm_output,
                config=TestConfig(
                    dataset_type="CommonOJDataset",
                    language=language,
                    provided_data={
                        "id": idx,
                        "content": "Optional: Problem description",
                        "test": [tc],
                    },
                ),
            )

            kwargs.append(
                {
                    "request": submit_request,
                    "client_timeout": self.timeout,
                    "max_attempts": self.max_attempts,
                }
            )

        responses = run_concurrent(
            func=submit,
            kwargs=kwargs,
            concurrency=self.concurrency,
        )

        num_passed = len([item for item in responses if item.tests[0].passed])

        return num_passed / len(responses)
