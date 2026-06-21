from __future__ import annotations

import requests

from ..config import settings
from ..models import TestCase


def execute_api(test_case: TestCase) -> dict:
    response = requests.post(
        f"{settings.api_base_url}/nlp/process",
        json={"text": test_case.input, "task": "summarize", "model": "mistral"},
        timeout=30,
    )
    return {
        "id": test_case.id,
        "canal": "api",
        "status": str(response.status_code),
        "actual": response.text,
    }
