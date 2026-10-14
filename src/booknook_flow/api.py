from __future__ import annotations

from dataclasses import asdict

from fastapi import FastAPI
from pydantic import BaseModel, Field

from booknook_flow.config import Settings
from booknook_flow.factory import build_llm
from booknook_flow.tools.registry import ToolRegistry
from booknook_flow.tracing import Tracer
from booknook_flow.workflow import run_workflow


class TaskIn(BaseModel):
    task: str = Field(min_length=3)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    app = FastAPI(title="BookNook editorial desk")
    app.state.settings = settings
    app.state.llm = build_llm(settings)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "llm": app.state.llm.name}

    @app.post("/workflows")
    def create_workflow(body: TaskIn) -> dict:
        state = run_workflow(
            body.task.strip(),
            app.state.llm,
            ToolRegistry(settings.data_dir),
            max_revisions=settings.max_revisions,
            tracer=Tracer(),
        )
        return asdict(state)

    return app


app = create_app()
