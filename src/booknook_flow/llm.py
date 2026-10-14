from __future__ import annotations

import json
from typing import Protocol


class LLMProvider(Protocol):
    name: str

    def complete(self, *, role: str, instructions: str, payload: dict) -> str:
        """Return a JSON object as text."""


class MockLLM:
    """Offline stand-in. Each role returns a stable JSON object."""

    name = "mock"

    def complete(self, *, role: str, instructions: str, payload: dict) -> str:
        del instructions
        if role == "planner":
            return json.dumps(
                {
                    "goal": payload.get("task", ""),
                    "steps": [
                        "read the shelf notes",
                        "check the loan arithmetic",
                        "draft a short desk note",
                    ],
                    "tools": ["file_reader", "calculator", "web_search"],
                }
            )
        if role == "researcher":
            return json.dumps(
                {
                    "tool_calls": [
                        {"name": "file_reader", "arguments": {"path": "shelf_notes.md"}},
                        {"name": "calculator", "arguments": {"expression": "4 * 21"}},
                        {
                            "name": "web_search",
                            "arguments": {"query": payload.get("task", "reading room")},
                        },
                    ]
                }
            )
        if role == "researcher_summary":
            observations = payload.get("observations", [])
            return json.dumps(
                {
                    "findings": [
                        item.get("summary", "") for item in observations if item.get("ok")
                    ],
                    "sources": [
                        item.get("source", "") for item in observations if item.get("source")
                    ],
                }
            )
        if role == "writer":
            findings = payload.get("findings") or {}
            lines = [str(item) for item in findings.get("findings", []) if item]
            extra = " ".join(payload.get("review_notes") or [])
            body = "BookNook desk note. " + " ".join(lines)
            if extra:
                body = f"{body} Revision: {extra}"
            if len(body) < 40:
                body = "BookNook desk note. Members may borrow four books for twenty-one days."
            return json.dumps(
                {
                    "title": "Reading-room note",
                    "body": body,
                    "sources": findings.get("sources", []),
                }
            )
        if role == "reviewer":
            body = (payload.get("draft") or {}).get("body", "")
            if "BookNook" in body and len(body) >= 40:
                return json.dumps(
                    {"verdict": "approve", "notes": ["The note stays on the shelf facts."]}
                )
            return json.dumps(
                {"verdict": "revise", "notes": ["Name BookNook and keep the note specific."]}
            )
        raise RuntimeError(f"unknown role: {role}")


class OpenAICompatibleLLM:
    name = "openai"

    def __init__(self, *, api_key: str, base_url: str, model: str, timeout: float = 60.0) -> None:
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is empty")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def complete(self, *, role: str, instructions: str, payload: dict) -> str:
        del role
        import httpx

        messages = [
            {"role": "system", "content": instructions + " Reply with one JSON object."},
            {"role": "user", "content": json.dumps(payload)},
        ]
        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "messages": messages, "temperature": 0},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
