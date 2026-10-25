
from collections import defaultdict
from typing import Any
from uuid import uuid4

from app.tracing.models import TraceEvent


class TraceCollector:
    def __init__(self):
        self.events: dict[str, list[TraceEvent]] = defaultdict(list)

    def start_run(self) -> str:
        run_id = str(uuid4())
        self.events[run_id] = []
        return run_id

    def record(
        self,
        run_id: str,
        event_type: str,
        name: str,
        input_data: dict[str, Any] | None = None,
        output_data: dict[str, Any] | None = None,
        status: str = "success",
        duration_ms: float | None = None,
    ) -> TraceEvent:
        event = TraceEvent(
            run_id=run_id,
            sequence=len(self.events[run_id]) + 1,
            event_type=event_type,
            name=name,
            input_data=input_data or {},
            output_data=output_data or {},
            status=status,
            duration_ms=duration_ms,
        )

        self.events[run_id].append(event)
        return event

    def get_events(self, run_id: str) -> list[TraceEvent]:
        return self.events.get(run_id, [])


collector = TraceCollector()
