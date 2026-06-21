from project2_agentic_testing.src.testing_agentic.evaluator import evaluate
from project2_agentic_testing.src.testing_agentic.models import TestCase


def test_evaluate_returns_result() -> None:
    case = TestCase(id="tc-1", canal="api", input="Bonjour", expected="salutation")
    result = evaluate(case, {"actual": "salutation", "status": "ok"})
    assert result.id == "tc-1"
    assert result.verdict in {"PASS", "FAIL"}
