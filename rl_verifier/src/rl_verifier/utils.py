import json
from typing import Dict, Any, Union


def ensure_json_serializable(data: Union[str, Dict[str, Any]]) -> str:
    """
    Ensures that the data is a JSON serializable string.

    Args:
        data: Either a JSON string or a dictionary

    Returns:
        A JSON string
    """
    if isinstance(data, str):
        # Validate that the string is valid JSON
        try:
            json.loads(data)
            return data
        except json.JSONDecodeError:
            raise ValueError("The provided string is not valid JSON")
    elif isinstance(data, dict):
        # Convert dictionary to JSON string
        return json.dumps(data)
    else:
        raise TypeError("Data must be either a JSON string or a dictionary")


def parse_response(response_text: str) -> Dict[str, Any]:
    """
    Parse the response text from the server.

    Args:
        response_text: The response text from the server

    Returns:
        A dictionary containing the parsed response
    """
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        raise ValueError(f"Failed to parse response as JSON: {response_text}")
