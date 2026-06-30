from __future__ import annotations

from .config import Settings
from .evaluator import EvaluatorAgent
from .executor import ExecutorAgent
from .generator import generate_cases
from .models import EvaluationResult
from .reporter import ReporterAgent


def run_pipeline(settings: Settings, channels: set[str] | None = None) -> tuple[list[EvaluationResult], str]:
    cases = generate_cases()
    if channels:
        cases = [case for case in cases if case.channel in channels]

    executor = ExecutorAgent(settings)
    evaluator = EvaluatorAgent()
    results: list[EvaluationResult] = []

    for test_case in cases:
        execution = executor.execute(test_case)
        results.append(evaluator.evaluate(test_case, execution))

    report_path = ReporterAgent(settings.output_dir).write(results)
    return results, str(report_path)


