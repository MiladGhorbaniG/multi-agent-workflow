import json
from pathlib import Path

import pytest

from booknook_flow.errors import ToolError
from booknook_flow.tools.files import read_shelf_file
from booknook_flow.tools.registry import ToolRegistry
from booknook_flow.tools.search import search_catalog

ROOT = Path(__file__).resolve().parents[1] / "sample_data"


def test_file_reader_stays_in_the_shelf() -> None:
    text = read_shelf_file(ROOT, "shelf_notes.md")
    assert "twenty-one days" in text
    with pytest.raises(ToolError):
        read_shelf_file(ROOT, "../pyproject.toml")
    with pytest.raises(ToolError):
        read_shelf_file(ROOT, "missing.md")


def test_catalog_search_ranks_loan_card() -> None:
    rows = json.loads((ROOT / "search_index.json").read_text(encoding="utf-8"))
    hits = search_catalog(rows, "How long is a loan of four books?")
    assert hits[0]["title"] == "Loan card"


def test_unknown_tool_is_reported_not_raised() -> None:
    result = ToolRegistry(ROOT).run("telescope", {}, attempts=2)
    assert result["ok"] is False
    assert "unknown tool" in result["summary"]


def test_tool_retries_then_succeeds() -> None:
    class Flaky(ToolRegistry):
        def __init__(self) -> None:
            super().__init__(ROOT)
            self.calls = 0

        def _once(self, name: str, arguments: dict) -> dict:
            if name == "calculator":
                self.calls += 1
                if self.calls == 1:
                    raise ToolError("scratch paper slipped")
            return super()._once(name, arguments)

    tool = Flaky()
    result = tool.run("calculator", {"expression": "2 + 2"}, attempts=2)
    assert tool.calls == 2
    assert result["ok"] is True
    assert "4" in result["summary"]
