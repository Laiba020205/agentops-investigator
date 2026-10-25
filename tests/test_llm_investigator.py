
import json

import pytest

from app.agents.llm_investigator import (
    Diagnosis,
    investigate_with_gemini,
)


def test_diagnosis_schema_accepts_valid_result():
    result = Diagnosis(
        root_cause="missing_required_argument",
        confidence=0.95,
        evidence=[
            {
                "sequence": 3,
                "explanation": (
                    "The tool call failed because order_id was missing."
                ),
            }
        ],
        recommendation="Validate required tool arguments.",
    )

    assert result.root_cause == "missing_required_argument"
    assert result.evidence[0].sequence == 3


def test_diagnosis_rejects_invalid_confidence():
    with pytest.raises(ValueError):
        Diagnosis(
            root_cause="unknown_failure",
            confidence=1.5,
            evidence=[],
            recommendation="Investigate further.",
        )


def test_diagnosis_rejects_invalid_root_cause():
    with pytest.raises(ValueError):
        Diagnosis(
            root_cause="made_up_category",
            confidence=0.5,
            evidence=[],
            recommendation="Investigate further.",
        )


def test_gemini_rejects_nonexistent_evidence_sequence(monkeypatch):
    from google.genai import types

    class FakeResponse:
        text = json.dumps({
            "root_cause": "tool_timeout",
            "confidence": 0.9,
            "evidence": [
                {
                    "sequence": 999,
                    "explanation": "The tool timed out.",
                }
            ],
            "recommendation": "Add a timeout policy.",
        })

    class FakeModels:
        def generate_content(self, **kwargs):
            return FakeResponse()

    class FakeClient:
        def __init__(self, **kwargs):
            self.models = FakeModels()

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        "google.genai.Client",
        FakeClient,
    )

    trace = [
        {
            "sequence": 1,
            "event_type": "error",
            "status": "failure",
            "output_data": {"error": "Tool timed out"},
        }
    ]

    with pytest.raises(
        ValueError,
        match="Gemini cited nonexistent event 999",
    ):
        investigate_with_gemini(trace)


def test_gemini_accepts_valid_evidence_sequence(monkeypatch):
    import google.genai

    class FakeResponse:
        text = json.dumps({
            "root_cause": "tool_timeout",
            "confidence": 0.9,
            "evidence": [
                {
                    "sequence": 1,
                    "explanation": "The tool timed out.",
                }
            ],
            "recommendation": "Add a timeout policy.",
        })

    class FakeModels:
        def generate_content(self, **kwargs):
            return FakeResponse()

    class FakeClient:
        def __init__(self, **kwargs):
            self.models = FakeModels()

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        google.genai,
        "Client",
        FakeClient,
    )

    trace = [
        {
            "sequence": 1,
            "event_type": "error",
            "status": "failure",
            "output_data": {"error": "Tool timed out"},
        }
    ]

    result = investigate_with_gemini(trace)

    assert result["root_cause"] == "tool_timeout"
    assert result["evidence"][0]["sequence"] == 1


def test_gemini_rejects_empty_response(monkeypatch):
    import google.genai

    class FakeResponse:
        text = None

    class FakeModels:
        def generate_content(self, **kwargs):
            return FakeResponse()

    class FakeClient:
        def __init__(self, **kwargs):
            self.models = FakeModels()

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        google.genai,
        "Client",
        FakeClient,
    )

    with pytest.raises(
        RuntimeError,
        match="Gemini returned an empty response",
    ):
        investigate_with_gemini([])



