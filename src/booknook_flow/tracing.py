from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger("booknook.flow")


@dataclass
class Tracer:
    events: list[dict] = field(default_factory=list)

    def record(self, agent: str, detail: dict) -> None:
        event = {
            "agent": agent,
            "at": datetime.now(timezone.utc).isoformat(),
            "detail": detail,
        }
        self.events.append(event)
        logger.info("%s %s", agent, json.dumps(detail, default=str)[:500])
