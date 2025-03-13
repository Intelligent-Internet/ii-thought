class RLVerifierError(Exception):
    """Base exception for all RL Verifier errors."""

    pass


class ConnectionError(RLVerifierError):
    """Raised when there's an issue connecting to the verifier server."""

    pass


class ValidationError(RLVerifierError):
    """Raised when the request data is invalid."""

    pass


class ServerError(RLVerifierError):
    """Raised when the server returns an error response."""

    pass


class TimeoutError(RLVerifierError):
    """Raised when a request to the server times out."""

    pass


class VerificationError(RLVerifierError):
    """Raised when the verification fails."""

    pass
