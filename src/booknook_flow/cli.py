from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from booknook_flow.config import Settings
from booknook_flow.factory import build_llm
from booknook_flow.tools.registry import ToolRegistry
from booknook_flow.workflow import run_workflow


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the BookNook editorial desk")
    parser.add_argument("task", help="What the desk should write")
    parser.add_argument("--json", action="store_true", help="Print the full workflow state")
    args = parser.parse_args(argv)
    settings = Settings.from_env()
    state = run_workflow(
        args.task,
        build_llm(settings),
        ToolRegistry(settings.data_dir),
        max_revisions=settings.max_revisions,
    )
    if args.json:
        print(json.dumps(asdict(state), indent=2))
    elif state.draft:
        print(state.draft["title"])
        print(state.draft["body"])
    return 0 if state.status == "approved" else 1


if __name__ == "__main__":
    raise SystemExit(main())
