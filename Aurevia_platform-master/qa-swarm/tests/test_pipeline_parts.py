from __future__ import annotations

from qa_swarm.evaluator import EvaluatorAgent
from qa_swarm.generator import generate_cases
from qa_swarm.models import ExecutionResult, ScenarioCase
from qa_swarm.reporter import ReporterAgent


def test_generator_creates_api_and_web_cases() -> None:
    cases = generate_cases()
    channels = {case.channel for case in cases}
    assert "api" in channels
    assert "web" in channels
    assert all(case.expected_keywords for case in cases)


def test_evaluator_passes_when_keywords_match() -> None:
    case = ScenarioCase(
        id="api-aum",
        channel="api",
        input="What is my AUM?",
        expected_keywords=["20.4", "AUM"],
        intent="financial_aum",
    )
    execution = ExecutionResult(
        id=case.id,
        channel="api",
        status="200",
        actual="Your portfolio AUM is $20.4M.",
        latency_s=0.5,
    )
    result = EvaluatorAgent().evaluate(case, execution)
    assert result.verdict == "PASS"
    assert result.score == 1.0


def test_evaluator_fails_missing_playwright() -> None:
    case = ScenarioCase(
        id="web-chat",
        channel="web",
        input="Hello",
        expected_keywords=["Hello"],
        intent="web_chat",
    )
    execution = ExecutionResult(
        id=case.id,
        channel="web",
        status="missing-playwright",
        actual="",
        latency_s=0.1,
        error="Playwright is not installed",
    )
    result = EvaluatorAgent().evaluate(case, execution)
    assert result.verdict == "FAIL"
    assert "Playwright" in result.reason


def test_reporter_writes_markdown_json_and_csv(tmp_path) -> None:
    case = ScenarioCase(
        id="api-aum",
        channel="api",
        input="What is my AUM?",
        expected_keywords=["20.4"],
        intent="financial_aum",
    )
    execution = ExecutionResult(
        id=case.id,
        channel="api",
        status="200",
        actual="AUM is 20.4M",
        latency_s=0.5,
    )
    result = EvaluatorAgent().evaluate(case, execution)
    report_path = ReporterAgent(tmp_path).write([result])

    assert report_path.exists()
    assert (tmp_path / "results.json").exists()
    assert (tmp_path / "results.csv").exists()
    assert "Success rate" in report_path.read_text(encoding="utf-8")


