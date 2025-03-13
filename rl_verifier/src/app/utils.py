def get_assistant_response(text: str, split_token: str) -> str:
    # remove everything before the split_token
    return text.split(split_token)[-1].strip()