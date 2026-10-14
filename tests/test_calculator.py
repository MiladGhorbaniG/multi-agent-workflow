import pytest

from booknook_flow.errors import ToolError
from booknook_flow.tools.calculator import evaluate


def test_arithmetic() -> None:
    assert evaluate("4 * 21") == 84
    assert evaluate("(2 + 3) * -2") == -10


def test_rejects_names_and_calls() -> None:
    with pytest.raises(ToolError):
        evaluate("__import__('os').system('echo hi')")
    with pytest.raises(ToolError):
        evaluate("forty + 2")
