from __future__ import annotations

from dataclasses import dataclass, field

from booknook_flow.guardrails import (
    CALL_KEYS,
    DRAFT_KEYS,
    PLAN_KEYS,
    REVIEW_KEYS,
    SUMMARY_KEYS,
    check_calls,
    check_draft,
    check_plan,
    check_review,
    check_summary,
    parse_object,
)
from booknook_flow.llm import LLMProvider
from booknook_flow.tracing import Tracer
from booknook_flow.tools.registry import ToolRegistry

PLANNER = (
    "You plan a BookNook desk note. Return JSON with goal, steps, and tools. "
    "Tools may be file_reader, calculator, and web_search."
)
RESEARCHER = (
    "You gather BookNook shelf facts. Return JSON tool_calls. "
    "Read shelf_notes.md, compute 4 * 21, and search the catalog."
)
SUMMARY = "Summarize tool observations as JSON with findings and sources."
WRITER = (
    "Write a short BookNook desk note as JSON with title, body, and sources. "
    "Use only the findings. The body must mention BookNook."
)
REVIEWER = (
    "Review the draft. Return JSON with verdict approve or revise, plus notes. "
    "Approve only when the body is specific and names BookNook."
)


@dataclass
class WorkflowState:
    task: str
    plan: dict | None = None
    tool_calls: list[dict] = field(default_factory=list)
    observations: list[dict] = field(default_factory=list)
    findings: dict | None = None
    draft: dict | None = None
    review: dict | None = None
    status: str = "running"
    attempts: int = 0
    trace: list[dict] = field(default_factory=list)


def run_workflow(
    task: str,
    llm: LLMProvider,
    tools: ToolRegistry,
    *,
    max_revisions: int = 2,
    tracer: Tracer | None = None,
) -> WorkflowState:
    tracer = tracer or Tracer()
    state = WorkflowState(task=task)

    plan = check_plan(
        parse_object(
            llm.complete(role="planner", instructions=PLANNER, payload={"task": task}),
            PLAN_KEYS,
        )
    )
    state.plan = plan
    tracer.record("planner", plan)

    calls = check_calls(
        parse_object(
            llm.complete(
                role="researcher",
                instructions=RESEARCHER,
                payload={"task": task, "plan": plan},
            ),
            CALL_KEYS,
        )
    )
    state.tool_calls = calls["tool_calls"]
    for call in state.tool_calls:
        observation = tools.run(call["name"], call["arguments"])
        state.observations.append(observation)
    tracer.record("researcher", {"observations": state.observations})

    findings = check_summary(
        parse_object(
            llm.complete(
                role="researcher_summary",
                instructions=SUMMARY,
                payload={"observations": state.observations},
            ),
            SUMMARY_KEYS,
        )
    )
    state.findings = findings
    tracer.record("researcher_summary", findings)

    review_notes: list[str] = []
    for attempt in range(1, max_revisions + 1):
        state.attempts = attempt
        draft = check_draft(
            parse_object(
                llm.complete(
                    role="writer",
                    instructions=WRITER,
                    payload={"task": task, "findings": findings, "review_notes": review_notes},
                ),
                DRAFT_KEYS,
            )
        )
        state.draft = draft
        tracer.record("writer", {"attempt": attempt, "title": draft["title"]})
        review = check_review(
            parse_object(
                llm.complete(
                    role="reviewer",
                    instructions=REVIEWER,
                    payload={"draft": draft, "notes": review_notes},
                ),
                REVIEW_KEYS,
            )
        )
        state.review = review
        tracer.record("reviewer", review)
        if review["verdict"] == "approve":
            state.status = "approved"
            break
        review_notes = [str(note) for note in review["notes"]]
    else:
        state.status = "needs_attention"

    state.trace = tracer.events
    return state
