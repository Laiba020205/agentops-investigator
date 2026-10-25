from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class TraceEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str
    sequence: int
    event_type: Literal[
        "agent_start",
        "llm_call",
        "tool_call",
        "tool_result",
        "error",
        "agent_finish",
    ]
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    name: str
    input_data: dict[str, Any] = Field(default_factory=dict)
    output_data: dict[str, Any] = Field(default_factory=dict)
    status: Literal["success", "failure", "running"] = "success"
    duration_ms: float | None = None
