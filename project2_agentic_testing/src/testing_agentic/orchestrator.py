from __future__ import annotations

from .evaluator import evaluate
from .executors.api_executor import execute_api
from .executors.mobile_executor import execute_mobile
from .executors.web_executor import execute_web
from .generator import generate_cases
from .models import TestCase
from .reporter import write_report


def run_pipeline(spec: dict) -> list:
    cases = generate_cases(spec)
    results = []

    for case in cases:
        if case.canal == "web":
            execution = execute_web(case)
        elif case.canal == "mobile":
            execution = execute_mobile(case)
        else:
            execution = execute_api(case)

        results.append(evaluate(case, execution))

    write_report(results)
    return results


def main() -> None:
    spec = {"canal": "api", "input": "Bonjour", "expected": "salutation"}
    results = run_pipeline(spec)
    print(f"{len(results)} test(s) exécuté(s)")


if __name__ == "__main__":
    main()
