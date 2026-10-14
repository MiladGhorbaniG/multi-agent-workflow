from __future__ import annotations

import json
from typing import Iterable

from booknook_flow.errors import GuardrailError

PLAN_KEYS = {"goal", "steps", "tools"}
CALL_KEYS = {"tool_calls"}
SUMMARY_KEYS = {"findings", "sources"}
DRAFT_KEYS = {"title", "body", "sources"}
REVIEW_KEYS = {"verdict", "notes"}
ALLOWED_TOOLS = {"file_reader", "calculator", "web_search"}
ALLOWED_VERDICTS = {"approve", "revise"}
BANNED = ("ignore previous", "system prompt")


def parse_object(raw: str, required: Iterable[str]) -> dict:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise GuardrailError("output is not JSON") from exc
    if not isinstance(payload, dict):
        raise GuardrailError("output is not a JSON object")
    missing = set(required) - set(payload)
    if missing:
        raise GuardrailError(f"missing keys: {', '.join(sorted(missing))}")
    return payload


def check_plan(plan: dict) -> dict:
    if not isinstance(plan["steps"], list) or not plan["steps"]:
        raise GuardrailError("plan needs steps")
    if not isinstance(plan["tools"], list):
        raise GuardrailError("plan tools must be a list")
    unknown = set(plan["tools"]) - ALLOWED_TOOLS
    if unknown:
        raise GuardrailError(f"unknown tools: {', '.join(sorted(unknown))}")
    return plan


def check_calls(payload: dict) -> dict:
    calls = payload["tool_calls"]
    if not isinstance(calls, list) or not calls:
        raise GuardrailError("researcher needs tool calls")
    for call in calls:
        if not isinstance(call, dict):
            raise GuardrailError("tool call must be an object")
        if call.get("name") not in ALLOWED_TOOLS:
            raise GuardrailError("tool call uses an unknown tool")
        if not isinstance(call.get("arguments"), dict):
            raise GuardrailError("tool call needs arguments")
    return payload


def check_summary(payload: dict) -> dict:
    if not isinstance(payload["findings"], list) or not isinstance(payload["sources"], list):
        raise GuardrailError("summary lists are malformed")
    return payload


def check_draft(payload: dict) -> dict:
    title = str(payload["title"]).strip()
    body = str(payload["body"]).strip()
    if len(title) < 3 or len(body) < 40:
        raise GuardrailError("draft is too short")
    if "BookNook" not in body:
        raise GuardrailError("draft must name BookNook")
    lowered = body.lower()
    for phrase in BANNED:
        if phrase in lowered:
            raise GuardrailError("draft tripped a guardrail")
    if not isinstance(payload["sources"], list):
        raise GuardrailError("draft sources must be a list")
    return {"title": title, "body": body, "sources": payload["sources"]}


def check_review(payload: dict) -> dict:
    if payload["verdict"] not in ALLOWED_VERDICTS:
        raise GuardrailError("verdict must be approve or revise")
    if not isinstance(payload["notes"], list):
        raise GuardrailError("review notes must be a list")
    return payload
