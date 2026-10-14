from __future__ import annotations

from booknook_flow.config import Settings
from booknook_flow.llm import LLMProvider, MockLLM, OpenAICompatibleLLM


def build_llm(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "mock":
        return MockLLM()
    if settings.llm_provider == "openai":
        return OpenAICompatibleLLM(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=settings.openai_model,
        )
    raise RuntimeError(f"unknown LLM_PROVIDER: {settings.llm_provider}")
