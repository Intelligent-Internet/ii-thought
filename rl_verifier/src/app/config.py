from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Whether to use format verifier
    use_format_verifier: bool = True
    
    # Code verification
    fusion_sandbox_url: Optional[str] = None

    # LLM judge
    llm_judge_model: Optional[str] = None
    llm_judge_base_url: Optional[str] = None
    llm_judge_api_key: Optional[str] = "EMPTY"
    llm_judge_max_tokens: Optional[int] = None
    llm_judge_temperature: Optional[float] = None

    class Config:
        env_file = ".env"  # Load from a .env file if available


settings = Settings()
