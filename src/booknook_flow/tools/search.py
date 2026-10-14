from __future__ import annotations

import re


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def search_catalog(rows: list[dict], query: str, limit: int = 3) -> list[dict]:
    """Rank the canned BookNook catalog. This is a stub, not a live web search."""
    wanted = tokenize(query)
    scored: list[dict] = []
    for row in rows:
        haystack = tokenize(f"{row.get('title', '')} {row.get('snippet', '')}")
        overlap = len(wanted & haystack)
        if overlap:
            scored.append({**row, "score": overlap})
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:limit]
