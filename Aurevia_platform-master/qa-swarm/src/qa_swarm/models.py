from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


Channel = Literal["api", "web", "mobile"]
Verdict = Literal["PASS", "FAIL", "WARN"]


@dataclass(slots=True)
class ScenarioCase:
    id: str
    channel: Channel
    input: str
    expected_keywords: list[str]
    intent: str
    path: str = "/chat"
    method: str = "chat"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ExecutionResult:
    id: str
    channel: Channel
    status: str
    actual: str
    latency_s: float
    screenshot: str | None = None
    ocr_text: str | None = None
    error: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class EvaluationResult:
    id: str
    channel: Channel
    intent: str
    status: str
    latency_s: float
    score: float
    hallucination: bool
    verdict: Verdict
    reason: str
    actual: str
    expected_keywords: list[str]
    screenshot: str | None = None
    ocr_text: str | None = None
    error: str | None = None


