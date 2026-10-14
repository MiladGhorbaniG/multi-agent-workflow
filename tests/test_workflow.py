import json
from pathlib import Path

import pytest

from booknook_flow.cli import main
from booknook_flow.config import Settings
from booknook_flow.factory import build_llm
from booknook_flow.llm import MockLLM
from booknook_flow.tools.registry import ToolRegistry
from booknook_flow.workflow import run_workflow

ROOT = Path(__file__).resolve().parents[1] / "sample_data"


def test_mock_workflow_approves_a_note() -> None:
    state = run_workflow("Draft a loan reminder", MockLLM(), ToolRegistry(ROOT))
    assert state.status == "approved"
    assert state.attempts == 1
    assert state.draft is not None
    assert "BookNook" in state.draft["body"]
    assert "84" in state.draft["body"]
    agents = [event["agent"] for event in state.trace]
    assert agents == ["planner", "researcher", "researcher_summary", "writer", "reviewer"]


class ReviseOnce(MockLLM):
    def __init__(self) -> None:
        self.reviews = 0

    def complete(self, *, role: str, instructions: str, payload: dict) -> str:
        if role == "reviewer":
            self.reviews += 1
            if self.reviews == 1:
                return json.dumps({"verdict": "revise", "notes": ["Mention the blue cart."]})
        return super().complete(role=role, instructions=instructions, payload=payload)


def test_reviewer_can_request_one_retry() -> None:
    state = run_workflow("Draft a loan reminder", ReviseOnce(), ToolRegistry(ROOT), max_revisions=2)
    assert state.status == "approved"
    assert state.attempts == 2
    assert "blue cart" in state.draft["body"].lower()


def test_cli_and_api(capsys: pytest.CaptureFixture[str]) -> None:
    from fastapi.testclient import TestClient

    from booknook_flow.api import create_app

    assert main(["Draft a loan reminder"]) == 0
    printed = capsys.readouterr().out
    assert "Reading-room note" in printed

    with TestClient(create_app(Settings(data_dir=ROOT))) as client:
        health = client.get("/health")
        assert health.json()["llm"] == "mock"
        response = client.post("/workflows", json={"task": "Draft a loan reminder"})
        assert response.status_code == 200
        assert response.json()["status"] == "approved"


def test_openai_provider_requires_a_key() -> None:
    with pytest.raises(RuntimeError):
        build_llm(Settings(llm_provider="openai"))
