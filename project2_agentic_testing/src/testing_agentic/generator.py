from __future__ import annotations

from .models import TestCase


def generate_cases(spec: dict) -> list[TestCase]:
    """Génère des cas de test à partir d'une spec simple."""
    channel = spec.get("canal", "api")
    base_input = spec.get("input", "Bonjour")
    return [
        TestCase(id="tc-1", canal=channel, input=base_input, expected=spec.get("expected")),
        TestCase(id="tc-2", canal=channel, input=base_input + " ?", expected=spec.get("expected")),
    ]
