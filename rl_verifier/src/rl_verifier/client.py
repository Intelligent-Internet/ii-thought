import json
import requests
import random
import time
import http.client

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
        max_retries: int = 3,
        initial_retry_delay: float = 2.0,
        max_retry_delay: float = 10.0,
        retry_backoff_factor: float = 2.0,
    ):
        """Initialize the RL Verifier client.

        Args:
            base_url: The base URL of the RL Verifier API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts for failed requests
            initial_retry_delay: Initial delay between retries in seconds
            max_retry_delay: Maximum delay between retries in seconds
            retry_backoff_factor: Factor to multiply delay by after each retry
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
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay
        self.max_retry_delay = max_retry_delay
        self.retry_backoff_factor = retry_backoff_factor

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle the response from the API.

        Args:
            response: The response object from the requests library

        Returns:
            The parsed JSON response
        """
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError:
            if response.status_code == 422:
                raise ValidationError(f"Invalid request data: {response.text}")
            elif response.status_code == 400:
                raise VerificationError(f"Verification failed: {response.text}")
            else:
                raise ServerError(f"Server error: {response.text}")
        except json.JSONDecodeError:
            raise ServerError(f"Failed to parse response as JSON: {response.text}")

    def _make_request(self, base_url: str, payload: Dict[str, Any]) -> float:
        """Make a request to the verifier server with retry logic.

        Args:
            base_url: The base URL to make the request to
            payload: The request payload

        Returns:
            The verification score
        """
        retry_delay = self.initial_retry_delay
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                response = requests.post(
                    f"{base_url}/reward", json=payload, timeout=self.timeout
                )
                response_data = self._handle_response(response)
                return response_data["score"]
            except (requests.exceptions.ConnectionError, http.client.RemoteDisconnected) as e:
                last_error = ConnectionError(f"Failed to connect to the server: {str(e)}")
            except requests.exceptions.Timeout as e:
                last_error = TimeoutError(f"Request timed out: {str(e)}")
            except (ValidationError, ServerError, VerificationError):
                # Re-raise these exceptions as they're already properly typed
                raise
            except Exception as e:
                last_error = RLVerifierError(f"Unexpected error: {str(e)}")

            if attempt < self.max_retries and (isinstance(last_error, ConnectionError) or isinstance(last_error, TimeoutError)):
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * self.retry_backoff_factor, self.max_retry_delay)
                # Try a different base URL if available
                if len(self.base_urls) > 1:
                    base_url = random.choice([url for url in self.base_urls if url != base_url])

        raise last_error

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
        """
        base_url = random.choice(self.base_urls)
        verification_info_str = ensure_json_serializable(verification_info)
        payload = {"llm_output": llm_output, "verification_info": verification_info_str}
        
        return self._make_request(base_url, payload)

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
        """
        assert len(batch) > 0

        items = [
            (i, llm_output, verification_info)
            for i, (llm_output, verification_info) in enumerate(batch)
        ]
        scores = [default_value] * len(items)

        def process_single(item):
            _, llm_output, verification_info = item
            return self.verify_safe(llm_output, verification_info, default_value)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
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
