from __future__ import annotations

import json
from pathlib import Path

from booknook_flow.errors import ToolError
from booknook_flow.tools.calculator import evaluate
from booknook_flow.tools.files import read_shelf_file
from booknook_flow.tools.search import search_catalog


class ToolRegistry:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        index_path = data_dir / "search_index.json"
        if index_path.exists():
            self.catalog = json.loads(index_path.read_text(encoding="utf-8"))
        else:
            self.catalog = []

    def run(self, name: str, arguments: dict, attempts: int = 2) -> dict:
        last_error = "unknown tool"
        for _ in range(max(1, attempts)):
            try:
                return self._once(name, arguments)
            except ToolError as exc:
                last_error = str(exc)
        return {"name": name, "ok": False, "source": "", "summary": last_error}

    def _once(self, name: str, arguments: dict) -> dict:
        if name == "calculator":
            expression = str(arguments.get("expression", ""))
            value = evaluate(expression)
            return {
                "name": name,
                "ok": True,
                "source": "calculator",
                "summary": f"{expression} = {value:g}",
            }
        if name == "file_reader":
            relative = str(arguments.get("path", ""))
            text = read_shelf_file(self.data_dir, relative)
            return {
                "name": name,
                "ok": True,
                "source": relative,
                "summary": " ".join(text.split()),
            }
        if name == "web_search":
            query = str(arguments.get("query", ""))
            hits = search_catalog(self.catalog, query)
            if not hits:
                raise ToolError("catalog has no matching card")
            summary = " | ".join(f"{hit['title']}: {hit['snippet']}" for hit in hits)
            return {"name": name, "ok": True, "source": "catalog", "summary": summary}
        raise ToolError(f"unknown tool: {name}")
