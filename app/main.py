from typing import Literal
from pydantic import BaseModel
from app.agents.investigator import investigate_trace
from app.agents.replay import replay_with_order_id
from app.agents.llm_investigator import investigate_with_gemini
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.agents.execution_agent import run_demo_agent
from app.tracing.collector import collector

app = FastAPI(
    title="AgentOps Investigator",
    description="Trace and investigate AI agent failures.",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}
class DemoRunRequest(BaseModel):
    scenario: Literal[
        "success",
        "missing_order_id",
        "timeout",
        "repeated_tool_call",
        "malformed_tool_response",
        "unsupported_answer",
        "conflicting_evidence",
        "multiple_failures",
        "misleading_answer",
    ] = "success"


@app.post("/runs/demo")
def create_demo_run(request: DemoRunRequest | None = None):
    scenario = request.scenario if request else "success"

    if scenario == "success":
        return run_demo_agent(order_id="ORD-101")

    if scenario == "missing_order_id":
        return run_demo_agent()

    if scenario == "timeout":
        return run_demo_agent(
            order_id="ORD-101",
            simulate_timeout=True,
        )

    if scenario == "repeated_tool_call":
        return run_demo_agent(
            order_id="ORD-101",
            simulate_repeated_tool_call=True,
        )

    if scenario == "malformed_tool_response":
        return run_demo_agent(
            order_id="ORD-101",
            simulate_malformed_response=True,
        )

    if scenario == "unsupported_answer":
        return run_demo_agent(
            order_id="ORD-101",
            simulate_unsupported_answer=True,
        )

    if scenario == "conflicting_evidence":
        return run_demo_agent(
            order_id="ORD-101",
            simulate_conflicting_evidence=True,
        )

    if scenario == "multiple_failures":
        return run_demo_agent(
            order_id="ORD-101",
            simulate_multiple_failures=True,
        )

    if scenario == "misleading_answer":
        return run_demo_agent(
            order_id="ORD-101",
            simulate_misleading_answer=True,
        )

@app.post("/runs/demo")
def create_demo_run():
    return run_demo_agent()


@app.get("/runs/{run_id}")
def get_run(run_id: str):
    events = collector.get_events(run_id)

    if not events:
        raise HTTPException(
            status_code=404,
            detail="Run not found",
        )

    return {
        "run_id": run_id,
        "event_count": len(events),
        "trace": [
            event.model_dump(mode="json")
            for event in events
        ],
    }


@app.get("/runs/{run_id}/investigation")
def get_investigation(run_id: str):
    events = collector.get_events(run_id)

    if not events:
        raise HTTPException(
            status_code=404,
            detail="Run not found",
        )

    trace = [
        event.model_dump(mode="json")
        for event in events
    ]

    return {
        "run_id": run_id,
        "investigation": investigate_trace(trace),
    }


@app.post("/runs/{run_id}/replay")
def replay_run(run_id: str, order_id: str):
    events = collector.get_events(run_id)

    if not events:
        raise HTTPException(
            status_code=404,
            detail="Run not found",
        )

    baseline = {
        "run_id": run_id,
        "status": events[-1].output_data.get("status", "unknown"),
        "trace": [
            event.model_dump(mode="json")
            for event in events
        ],
    }

    return replay_with_order_id(
        order_id=order_id,
        baseline=baseline,
    )

@app.get("/runs/{run_id}/llm-investigation")
def get_llm_investigation(run_id: str):
    events = collector.get_events(run_id)

    if not events:
        raise HTTPException(
            status_code=404,
            detail="Run not found",
        )

    trace = [
        event.model_dump(mode="json")
        for event in events
    ]

    try:
        diagnosis = investigate_with_gemini(trace)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="LLM investigation failed. Check server logs.",
        ) from exc

    return {
        "run_id": run_id,
        "investigation": diagnosis,
    }
