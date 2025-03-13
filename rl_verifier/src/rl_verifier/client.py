import json
import requests
import random

from typing import Dict, Any, Union, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from .exception import (
    RLVerifierError,
    ConnectionError,
    ValidationError,
    ServerError,
    TimeoutError,
    VerificationError,
)
from .utils import ensure_json_serializable


class RLVerifierClient:
    """
    Client for interacting with the RL Verifier API.
    """

    def __init__(
        self,
        base_url: Union[str, List[str]] = None,
        timeout: int = 30,
    ):
        """
        Initialize the RL Verifier client.

        Args:
            base_url: The base URL of the RL Verifier API
            timeout: Request timeout in seconds
        """
        if isinstance(base_url, list):
            self.base_urls = [url.rstrip("/") for url in base_url]
        else:
            self.base_urls = [base_url.rstrip("/")]
        for base_url in self.base_urls:
            rsp = requests.get(f"{base_url}/ping", timeout=5)
            if rsp.status_code != 200:
                raise RLVerifierError(f"Failed to connect {base_url}: {rsp.text}")

        self.timeout = timeout

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle the response from the API.

        Args:
            response: The response object from the requests library

        Returns:
            The parsed JSON response

        Raises:
            ValidationError: If the request data is invalid
            VerificationError: If the verification fails
            ServerError: If the server returns an error
        """
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 422:
                raise ValidationError(f"Invalid request data: {response.text}")
            elif response.status_code == 400:
                raise VerificationError(f"Verification failed: {response.text}")
            else:
                raise ServerError(f"Server error: {response.text}")
        except json.JSONDecodeError:
            raise ServerError(f"Failed to parse response as JSON: {response.text}")

    def _verify_pure(
        self, llm_output: str, verification_info: str, base_url: str
    ) -> float:
        """
        Verify the LLM output using the pure verification API.
        """
        payload = {"llm_output": llm_output, "verification_info": verification_info}

        response = requests.post(
            f"{base_url}/reward", json=payload, timeout=self.timeout
        )

        response_data = self._handle_response(response)

        return response_data["score"]

    def verify(
        self, llm_output: str, verification_info: Union[str, Dict[str, Any]]
    ) -> float:
        """
        Compute the reward for an LLM output.

        Args:
            llm_output: The output from the LLM to be verified
            verification_info: Verification information as a JSON string or dictionary
                               Must contain 'answer' and 'type' fields

        Returns:
            The verification score between 0 and 1

        Raises:
            ConnectionError: If there's an issue connecting to the server
            TimeoutError: If the request times out
            ValidationError: If the request data is invalid
            VerificationError: If the verification fails
            ServerError: If the server returns an error
        """

        base_url = random.choice(self.base_urls)
        # Ensure verification_info is a JSON string
        verification_info_str = ensure_json_serializable(verification_info)

        try:
            score = self._verify_pure(llm_output, verification_info_str, base_url)
            return score

        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(f"Failed to connect to the server: {str(e)}")
        except requests.exceptions.Timeout as e:
            raise TimeoutError(f"Request timed out: {str(e)}")
        except (ValidationError, ServerError, VerificationError) as e:
            # Re-raise these exceptions as they're already handled
            raise
        except Exception as e:
            # Catch any other exceptions
            raise RLVerifierError(f"Unexpected error: {str(e)}")

    def verify_safe(
        self,
        llm_output: str,
        verification_info: Union[str, Dict[str, Any]],
        default_value: float = 0.0,
    ) -> float:
        """
        Compute the reward for an LLM output, returning a default value if any error occurs.

        Args:
            llm_output: The output from the LLM to be verified
            verification_info: Verification information as a JSON string or dictionary
                               Must contain 'answer' and 'type' fields
            default_value: Value to return if verification fails (default: 0.0)

        Returns:
            The verification score between 0 and 1, or default_value if an error occurs
        """
        try:
            return self.verify(llm_output, verification_info)
        except Exception as e:
            # Log the error but continue with default value
            print(f"Verification error (returning {default_value}): {str(e)}")
            return default_value

    def verify_batch(
        self,
        batch: List[Tuple[str, Union[str, Dict[str, Any]]]],
        max_workers: int = 5,
        default_value: float = 0.0,
        progress_bar: bool = True,
    ) -> list[float]:
        """
        Compute rewards for multiple LLM outputs in parallel.

        Args:
            batch: List of tuples, each containing (llm_output, verification_info)
                  where verification_info is a JSON string or dictionary
            max_workers: Maximum number of concurrent workers for processing
            default_value: Value to return if verification fails (default: 0.0)
            progress_bar: Whether to show a progress bar (default: True)

        Returns:
            List of verification scores between 0 and 1, in the same order as the input batch

        Raises:
            ConnectionError: If there's an issue connecting to the server
            TimeoutError: If the request times out
            ValidationError: If the request data is invalid
            ServerError: If the server returns an error
            VerificationError: If the verification fails
        """
        assert len(batch) > 0

        items = [
            (i, llm_output, verification_info)
            for i, (llm_output, verification_info) in enumerate(batch)
        ]
        scores = [default_value] * len(items)

        # Function to process a single verification request
        def process_single(item):
            _, llm_output, verification_info = item
            return self.verify_safe(llm_output, verification_info, default_value)

        # Process the batch in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Create a dictionary mapping futures to their indices
            future_to_index = {
                executor.submit(process_single, item): item[0] for item in items
            }

            loop = (
                tqdm(as_completed(future_to_index), total=len(items))
                if progress_bar
                else as_completed(future_to_index)
            )

            for future in loop:
                index = future_to_index[future]
                try:
                    scores[index] = future.result()
                except Exception as e:
                    print(f"Error processing index {index}: {e}")

        return scores
