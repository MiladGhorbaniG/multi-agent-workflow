from __future__ import annotations

import ast
import operator

from booknook_flow.errors import ToolError

_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_ALLOWED = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.Pow,
    ast.UAdd,
    ast.USub,
    ast.Constant,
)


def evaluate(expression: str) -> float:
    """Evaluate a plain arithmetic expression. Names and calls are rejected."""
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ToolError("expression is not arithmetic") from exc
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED):
            raise ToolError("expression is not arithmetic")
        if isinstance(node, ast.Constant) and not isinstance(node.value, (int, float)):
            raise ToolError("expression is not arithmetic")
    return float(_eval(tree.body))


def _eval(node: ast.AST) -> float:
    if isinstance(node, ast.Constant):
        return float(node.value)
    if isinstance(node, ast.UnaryOp):
        value = _eval(node.operand)
        if isinstance(node.op, ast.USub):
            return -value
        return value
    if isinstance(node, ast.BinOp):
        op = _BINOPS[type(node.op)]
        return float(op(_eval(node.left), _eval(node.right)))
    raise ToolError("expression is not arithmetic")
