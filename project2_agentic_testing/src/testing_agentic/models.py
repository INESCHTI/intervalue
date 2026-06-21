from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class TestCase:
    id: str
    canal: str
    input: str
    expected: str | dict | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TestResult:
    id: str
    canal: str
    actual: str | dict | None
    expected: str | dict | None
    status: str
    score: float
    verdict: str
    evidence: dict[str, Any] = field(default_factory=dict)
