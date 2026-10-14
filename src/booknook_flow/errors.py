class ToolError(RuntimeError):
    """A tool rejected its arguments or could not finish."""


class GuardrailError(RuntimeError):
    """Model output failed a schema or content check."""
