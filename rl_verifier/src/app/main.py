import json

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from .verifier import (
    MathVerifier,
    CodeVerifier,
    SWEVerifier,
    LLMJudge,
    FormatVerifier,
    VerifierInitializationError,
)
from .config import settings
from .utils import get_assistant_response

app = FastAPI()


def get_verifier(verification_type):
    """Factory function to create verifiers on demand."""
    if verification_type == "math_verifiable":
        return MathVerifier()
    elif verification_type == "code_verifiable":
        return CodeVerifier(base_url=settings.fusion_sandbox_url)
    elif verification_type == "swe_verifiable":
        return SWEVerifier()
    elif verification_type == "llm_judge":
        return LLMJudge(
            model=settings.llm_judge_model,
            base_url=settings.llm_judge_base_url,
            api_key=settings.llm_judge_api_key,
            max_tokens=settings.llm_judge_max_tokens,
            temperature=settings.llm_judge_temperature,
        )
    else:
        raise ValueError(f"Unsupported verification type: {verification_type}")


# Cache for initialized verifiers
verifier_instances = {}

if settings.use_format_verifier:
    print("Using format verifier")
    verifier_instances["format_verifier"] = FormatVerifier()

# List of supported verifier types
SUPPORTED_VERIFIER_TYPES = [
    "math_verifiable",
    "code_verifiable",
    "swe_verifiable",
    "llm_judge",
]


class VerificationRequest(BaseModel):
    llm_output: str
    verification_info: str


class VerificationResponse(BaseModel):
    score: float


@app.get("/ping")
async def ping():
    """
    Health check endpoint to verify the service is running.

    Returns:
        dict: A simple response indicating the service is operational
    """
    return {"status": "ok", "message": "RL Verifier service is running"}


@app.post("/reward")
async def compute_reward(item: VerificationRequest) -> VerificationResponse:
    llm_output = item.llm_output
    verification_info = item.verification_info

    # Extract only the assistant's response
    llm_output = get_assistant_response(llm_output, split_token="<｜Assistant｜>")

    try:
        verification_info = json.loads(item.verification_info)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"The verification info must be in parsable JSON format",
        )

    if "answer" not in verification_info or "type" not in verification_info:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"The verification info must contain 'answer' and 'type' fields. Received: {verification_info}",
        )

    verification_type = verification_info["type"]

    if verification_type not in SUPPORTED_VERIFIER_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"The verification type {verification_type} is not supported.",
        )

    # Initialize the verifier if it hasn't been initialized yet
    if verification_type not in verifier_instances:
        try:
            verifier_instances[verification_type] = get_verifier(verification_type)
        except VerifierInitializationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to initialize {verification_type} verifier: {str(e)}",
            )

    answer_verifier = verifier_instances[verification_type]
    
    answer_score = answer_verifier(llm_output, verification_info)
    
    if not settings.use_format_verifier:
        return VerificationResponse(score=answer_score)
    
    format_score = verifier_instances["format_verifier"](llm_output, verification_info)
    score = 0.9 * answer_score + 0.1 * format_score

    return VerificationResponse(score=score)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)