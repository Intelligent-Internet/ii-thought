from abc import ABC, abstractmethod


class BaseVerifier(ABC):
    @abstractmethod
    def verify(self, llm_output: str, verification_info: dict) -> float:
        pass

    def __call__(self, llm_output: str, verification_info: dict) -> float:
        return self.verify(llm_output, verification_info)
