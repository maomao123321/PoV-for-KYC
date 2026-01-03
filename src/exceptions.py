class TechnicalRejectError(Exception):
    """Raised when input fails technical quality gates."""


class ModelCallError(Exception):
    """Raised when the model call fails after retries and fallback."""


class SchemaValidationError(Exception):
    """Raised when structured output cannot be parsed."""

