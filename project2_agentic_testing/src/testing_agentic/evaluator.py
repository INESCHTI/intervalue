from __future__ import annotations

from .models import TestCase, TestResult


def evaluate(test_case: TestCase, execution: dict) -> TestResult:
    actual = execution.get("actual")
    expected = test_case.expected
    score = 1.0 if actual and expected is not None else 0.5
    verdict = "PASS" if score >= 1.0 else "FAIL"
    return TestResult(
        id=test_case.id,
        canal=test_case.canal,
        actual=actual,
        expected=expected,
        status=execution.get("status", "unknown"),
        score=score,
        verdict=verdict,
        evidence={k: v for k, v in execution.items() if k not in {"actual"}},
    )
