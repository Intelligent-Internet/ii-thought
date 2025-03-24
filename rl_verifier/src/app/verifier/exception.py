class VerifierException(Exception):
    """Base exception for verifier errors."""

    pass


class VerifierTimeout(VerifierException):
    """Exception for verifier timeout."""

    pass


class VerifierInitializationError(VerifierException):
    """Exception for verifier initialization errors."""

    pass
