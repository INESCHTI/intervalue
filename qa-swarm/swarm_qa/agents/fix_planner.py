"""Failure triage and non-destructive fix-plan agent.

The planner sits after the Reporter in the QA chain. It never edits files. Its job is to
classify failures, point to likely ownership, and produce a practical plan a developer or
separate coding agent can review before touching the codebase.
"""

from __future__ import annotations

from swarm import Agent

from swarm_qa.config import settings
from swarm_qa.models import (
    FailureAnalysis,
    FailureCategory,
    FailureTriage,
    FixPlan,
    FixStep,
    RunReport,
    ScenarioResult,
    Severity,
)

FIX_PLANNER_INSTRUCTIONS = (
    "You are a safe QA fix planner. Given failed test results, classify the failure and "
    "produce a human-reviewable fix plan. Never modify code, never apply patches, and never "
    "claim a fix was completed. Output should describe likely files, steps, verification "
    "commands, risks, and rollback notes."
)


def build_fix_planner_agent() -> Agent:
    return Agent(
        name="FixPlanner",
        model=settings.model_reporter,
        instructions=FIX_PLANNER_INSTRUCTIONS,
    )


def _failure_id(scenario: ScenarioResult, channel: str) -> str:
    return f"{scenario.test_case.id}:{channel}"


def _category_and_owner(scenario: ScenarioResult, channel: str) -> tuple[FailureCategory, str]:
    score = scenario.scores[channel]
    result = scenario.results.get(channel)
    intent = scenario.test_case.intent.lower()
    reason = score.reason.lower()
    actual = (result.actual if result else "").lower()
    error = (result.error if result else "").lower()

    if result and result.timed_out:
        return "performance", "platform/runtime"
    if result and result.crashed:
        if "401" in reason or "unauthorized" in actual or "unauthorized" in error:
            return "auth_session", "frontend/auth + orchestrator"
        return "infra_unavailable", "platform/runtime"
    if channel == "web" and ("selector" in error or "web error" in actual or "spinner" in error):
        return "ui_selector", "frontend"
    if "401" in reason or "unauthorized" in actual or "sign in" in actual:
        return "auth_session", "frontend/auth + orchestrator"
    if score.hallucination or "hallucination" in reason or "invented" in reason:
        return "prompt_agent", "orchestrator/agents"
    if scenario.test_case.type == "adversarial":
        return "security_guardrail", "orchestrator/guardrails"
    if "latency" in reason or "timeout" in reason:
        return "performance", "platform/runtime"
    if "expected" in reason and "actual" in reason:
        return "expected_outdated", "qa-swarm/corpus"
    if any(token in intent for token in ("portfolio", "aum", "irr", "twr", "sharpe", "allocation")):
        return "product_bug", "financial agent/orchestrator"
    if any(token in intent for token in ("market", "quote", "macro")):
        return "product_bug", "market agent/orchestrator"
    if any(token in intent for token in ("doc", "upload", "ocr", "rag")):
        return "product_bug", "docs agent/orchestrator"
    return "unknown", "unassigned"


def _severity(scenario: ScenarioResult, channel: str) -> Severity:
    score = scenario.scores[channel]
    result = scenario.results.get(channel)
    if scenario.test_case.type == "adversarial" and score.verdict == "FAIL":
        return "critical"
    if result and (result.crashed or result.timed_out):
        return "high"
    if score.hallucination:
        return "high"
    if score.mean < 2.0:
        return "high"
    if scenario.test_case.type == "nominal":
        return "medium"
    return "low"


def _confidence(category: FailureCategory, scenario: ScenarioResult, channel: str) -> float:
    result = scenario.results.get(channel)
    if result and (result.crashed or result.timed_out):
        return 0.9
    if category in {"auth_session", "security_guardrail", "prompt_agent"}:
        return 0.82
    if category == "unknown":
        return 0.45
    return 0.7


def _evidence(scenario: ScenarioResult, channel: str) -> list[str]:
    score = scenario.scores[channel]
    result = scenario.results.get(channel)
    evidence = [
        f"Expected: {scenario.test_case.expected or '(no explicit expected text)'}",
        f"Score: {score.mean}/5, verdict={score.verdict}, reason={score.reason or 'n/a'}",
    ]
    if result:
        evidence.append(f"Actual: {(result.actual or result.error or '(empty)')[:500]}")
        evidence.append(
            f"Runtime: status={result.status_code}, latency={result.latency_ms}ms, "
            f"timeout={result.timed_out}, crashed={result.crashed}"
        )
        if result.screenshot:
            evidence.append(f"Screenshot: {result.screenshot}")
    return evidence


def triage_failure(scenario: ScenarioResult, channel: str) -> FailureTriage:
    category, owner = _category_and_owner(scenario, channel)
    sev = _severity(scenario, channel)
    fid = _failure_id(scenario, channel)
    return FailureTriage(
        failure_id=fid,
        scenario_id=scenario.test_case.id,
        intent=scenario.test_case.intent,
        channel=channel,  # type: ignore[arg-type]
        category=category,
        severity=sev,
        confidence=_confidence(category, scenario, channel),
        summary=(
            f"{scenario.test_case.intent} failed on {channel}; classified as "
            f"{category.replace('_', ' ')}."
        ),
        evidence=_evidence(scenario, channel),
        likely_owner=owner,
        recommended_action="Review the proposed fix plan, apply manually, then rerun the focused QA scenario.",
    )


def _likely_files(category: FailureCategory, intent: str, channel: str) -> list[str]:
    intent = intent.lower()
    files: list[str] = []
    if category == "auth_session":
        files += [
            "frontend/src/auth/AuthContext.tsx",
            "frontend/src/api/client.ts",
            "services/orchestrator/src/orchestrator/main.py",
        ]
    elif category == "ui_selector" or channel == "web":
        files += [
            "frontend/src/pages/Chat.tsx",
            "frontend/src/index.css",
            "qa-swarm/swarm_qa/channels/web_channel.py",
        ]
    elif category == "security_guardrail":
        files += [
            "services/orchestrator/src/orchestrator/guardrails.py",
            "services/orchestrator/src/orchestrator/graph.py",
            "qa-swarm/swarm_qa/corpus/scenarios.json",
        ]
    elif category == "prompt_agent":
        files += [
            "services/orchestrator/src/orchestrator/graph.py",
            "services/agent-financial/src/agent_financial/agent.py",
            "services/agent-docs/src/agent_docs/main.py",
        ]
    elif category == "performance":
        files += [
            "services/orchestrator/src/orchestrator/main.py",
            "services/orchestrator/src/orchestrator/graph.py",
            "qa-swarm/swarm_qa/config.py",
        ]
    elif category == "expected_outdated":
        files += ["qa-swarm/swarm_qa/corpus/scenarios.json"]
    elif "market" in intent:
        files += ["services/agent-market/src/agent_market/main.py"]
    elif any(token in intent for token in ("doc", "upload", "ocr", "rag")):
        files += ["services/agent-docs/src/agent_docs/main.py"]
    elif any(token in intent for token in ("portfolio", "aum", "irr", "twr", "sharpe", "allocation")):
        files += [
            "services/agent-financial/src/agent_financial/agent.py",
            "services/orchestrator/src/orchestrator/graph.py",
        ]
    else:
        files += [
            "services/orchestrator/src/orchestrator/graph.py",
            "qa-swarm/swarm_qa/corpus/scenarios.json",
        ]
    return list(dict.fromkeys(files))


def make_fix_plan(triage: FailureTriage) -> FixPlan:
    files = _likely_files(triage.category, triage.intent, triage.channel)
    steps = [
        FixStep(
            title="Reproduce the failure",
            detail=(
                "Run the single failing scenario on the same channel and capture response text, "
                "status code, latency, and screenshot if available."
            ),
            files=["qa-swarm/swarm_qa/corpus/scenarios.json"],
            commands=[
                f"uv run python -m swarm_qa.pipeline --channel {triage.channel} --limit 1 --version repro"
            ],
            risk="low",
        ),
        FixStep(
            title="Inspect likely owner files",
            detail=(
                "Check the listed files for the routing, prompt, selector, auth, or service behavior "
                "suggested by the triage category. Confirm with logs before editing."
            ),
            files=files,
            commands=["rg -n \"TODO|FIXME|unauthorized|selector|hallucination|timeout\" ."],
            risk="low",
        ),
        FixStep(
            title="Apply a focused manual fix",
            detail=(
                "Make the smallest code or corpus change that explains the observed failure. "
                "Do not broaden prompts or test expectations unless the evidence shows the expected "
                "answer is stale."
            ),
            files=files,
            commands=[],
            risk="medium",
        ),
        FixStep(
            title="Verify locally",
            detail=(
                "Rerun the focused QA scenario first, then the qa-swarm unit tests. If the fix touches "
                "frontend or orchestrator code, also run that surface's build/test command."
            ),
            files=[],
            commands=[
                "uv run pytest tests -q",
                f"uv run python -m swarm_qa.pipeline --channel {triage.channel} --limit 1 --version fixed-candidate",
            ],
            risk="low",
        ),
    ]
    return FixPlan(
        failure_id=triage.failure_id,
        title=f"Plan to fix {triage.intent} on {triage.channel}",
        root_cause_hypothesis=(
            f"Likely {triage.category.replace('_', ' ')} owned by {triage.likely_owner}. "
            "This is a hypothesis only; confirm with logs and a focused reproduction before editing."
        ),
        affected_files=files,
        steps=steps,
        verification_commands=[
            "uv run pytest tests -q",
            f"uv run python -m swarm_qa.pipeline --channel {triage.channel} --limit 1 --version verify",
        ],
        rollback_notes=(
            "Revert only the focused manual change if verification regresses. Keep the QA evidence and "
            "fix plan for comparison."
        ),
        human_approval_required=True,
        auto_apply=False,
    )


def analyze_report(report: RunReport) -> list[FailureAnalysis]:
    analyses: list[FailureAnalysis] = []
    for scenario in report.scenarios:
        for channel, score in scenario.scores.items():
            if score.verdict != "FAIL":
                continue
            triage = triage_failure(scenario, channel)
            analyses.append(FailureAnalysis(triage=triage, fix_plan=make_fix_plan(triage)))
    return analyses
