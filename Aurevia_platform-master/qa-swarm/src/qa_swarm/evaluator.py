from __future__ import annotations

from .models import EvaluationResult, ExecutionResult, ScenarioCase


class EvaluatorAgent:
    """Evaluator Agent: score expected vs actual and flag hard failures."""

    def evaluate(self, test_case: ScenarioCase, execution: ExecutionResult) -> EvaluationResult:
        combined_text = " ".join(
            part
            for part in [execution.actual, execution.ocr_text or "", execution.error or ""]
            if part
        )
        normalized = combined_text.casefold()
        matches = [
            keyword
            for keyword in test_case.expected_keywords
            if keyword.casefold() in normalized
        ]
        score = round(len(matches) / max(len(test_case.expected_keywords), 1), 3)
        status_failed = execution.status in {
            "error",
            "timeout",
            "missing-playwright",
            "not-configured",
        }
        hallucination = _looks_like_hallucination(test_case, combined_text)

        if status_failed:
            verdict = "FAIL"
            reason = execution.error or f"Execution status is {execution.status}."
        elif hallucination:
            verdict = "FAIL"
            reason = "Hallucination-like content was detected."
        elif score >= 0.67:
            verdict = "PASS"
            reason = f"Matched {len(matches)}/{len(test_case.expected_keywords)} expected keywords."
        elif score > 0:
            verdict = "WARN"
            reason = f"Partial match: {matches}."
        else:
            verdict = "FAIL"
            reason = "No expected keyword was found in actual/DOM/OCR evidence."

        return EvaluationResult(
            id=test_case.id,
            channel=test_case.channel,
            intent=test_case.intent,
            status=execution.status,
            latency_s=execution.latency_s,
            score=score,
            hallucination=hallucination,
            verdict=verdict,
            reason=reason,
            actual=execution.actual,
            expected_keywords=test_case.expected_keywords,
            screenshot=execution.screenshot,
            ocr_text=execution.ocr_text,
            error=execution.error,
        )


def _looks_like_hallucination(test_case: ScenarioCase, text: str) -> bool:
    if not text:
        return False
    lowered = text.casefold()
    if test_case.intent == "financial_aum" and "20.4" not in lowered and "aum" in lowered:
        return True
    if "password" in lowered and "guardrail" not in lowered and "forbidden" not in lowered:
        return True
    return False


