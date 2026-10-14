from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def default_data_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "sample_data"


@dataclass(frozen=True)
class Settings:
    llm_provider: str = "mock"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    data_dir: Path = Path("sample_data")
    max_revisions: int = 2

    @classmethod
    def from_env(cls) -> Settings:
        raw_dir = os.environ.get("DATA_DIR", "")
        return cls(
            llm_provider=os.environ.get("LLM_PROVIDER", "mock"),
            openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
            openai_base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            openai_model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            data_dir=Path(raw_dir) if raw_dir else default_data_dir(),
            max_revisions=int(os.environ.get("MAX_REVISIONS", "2")),
        )
