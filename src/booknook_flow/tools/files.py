from __future__ import annotations

from pathlib import Path

from booknook_flow.errors import ToolError


def read_shelf_file(root: Path, relative: str, limit: int = 4000) -> str:
    """Read a UTF-8 note that stays inside the sample shelf folder."""
    if not relative or relative.strip() != relative or "\\" in relative:
        raise ToolError("path is not a shelf note")
    base = root.resolve()
    target = (base / relative).resolve()
    if target != base and base not in target.parents:
        raise ToolError("path escapes the shelf folder")
    if not target.is_file():
        raise ToolError("file is not on the shelf")
    return target.read_text(encoding="utf-8")[:limit]
