from __future__ import annotations

from ..models import TestCase


def execute_mobile(test_case: TestCase) -> dict:
    """Skeleton mobile executor. Brancher Appium quand l'émulateur sera prêt."""
    return {
        "id": test_case.id,
        "canal": "mobile",
        "status": "stub",
        "actual": None,
    }
