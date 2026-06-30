"""Tests for safe failure triage and non-destructive fix planning."""

from __future__ import annotations

from swarm_qa.agents import fix_planner
from swarm_qa.models import ChannelResult, RunReport, ScenarioResult, Score, TestCase


def _failed_scenario(
    *,
    intent: str = "portfolio_aum",
    case_type: str = "nominal",
    actual: str = "wrong answer",
    reason: str = "invented figures",
    hallucination: bool = True,
) -> ScenarioResult:
    case = TestCase(
        id="S01",
        intent=intent,
        type=case_type,  # type: ignore[arg-type]
        input="What is my AUM?",
        expected="$20.4M",
        channels=["api"],
    )
    return ScenarioResult(
        test_case=case,
        results={"api": ChannelResult(channel="api", actual=actual, status_code=200)},
        scores={
            "api": Score(
                pertinence=3,
                exactitude=1,
                coherence=2,
                hallucination=hallucination,
                verdict="FAIL",
                reason=reason,
            )
        },
    )


def test_fix_planner_classifies_hallucination_as_prompt_agent():
    scenario = _failed_scenario()
    triage = fix_planner.triage_failure(scenario, "api")
    plan = fix_planner.make_fix_plan(triage)

    assert triage.category == "prompt_agent"
    assert triage.severity == "high"
    assert plan.auto_apply is False
    assert plan.human_approval_required is True
    assert plan.steps
    assert any("services/orchestrator" in file for file in plan.affected_files)


def test_fix_planner_classifies_adversarial_failure_as_security_guardrail():
    scenario = _failed_scenario(
        intent="prompt_injection",
        case_type="adversarial",
        actual="secret disclosed",
        reason="guardrail failed",
        hallucination=False,
    )
    triage = fix_planner.triage_failure(scenario, "api")

    assert triage.category == "security_guardrail"
    assert triage.severity == "critical"
    assert "guardrails" in " ".join(fix_planner.make_fix_plan(triage).affected_files)


def test_analyze_report_returns_only_failed_scenarios():
    failed = _failed_scenario()
    passed = ScenarioResult(
        test_case=TestCase(id="S02", intent="greeting", input="hello", channels=["api"]),
        results={"api": ChannelResult(channel="api", actual="hello")},
        scores={
            "api": Score(
                pertinence=5,
                exactitude=5,
                coherence=5,
                verdict="PASS",
            )
        },
    )
    report = RunReport(
        run_id="run_test",
        sut_version="test",
        channels=["api"],
        scenarios=[failed, passed],
    )

    analyses = fix_planner.analyze_report(report)

    assert len(analyses) == 1
    assert analyses[0].triage.failure_id == "S01:api"
    assert analyses[0].fix_plan.auto_apply is False
