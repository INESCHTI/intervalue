from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Settings:
    api_base_url: str
    web_base_url: str
    output_dir: Path
    headless: bool
    ocr_enabled: bool
    browser_timeout_s: int


def load_settings() -> Settings:
    target = os.getenv("AUREVIA_TARGET", "local").lower()

    if target == "minikube":
        default_api = "http://wealthmesh.local"
        default_web = "http://wealthmesh.local"
    else:
        default_api = "http://127.0.0.1:8000"
        default_web = "http://127.0.0.1:5173"

    return Settings(
        api_base_url=os.getenv("AUREVIA_API_URL", default_api).rstrip("/"),
        web_base_url=os.getenv("AUREVIA_WEB_URL", default_web).rstrip("/"),
        output_dir=Path(os.getenv("AUREVIA_QA_OUTPUT", "reports/qa-swarm")),
        headless=os.getenv("AUREVIA_BROWSER_HEADLESS", "true").lower() != "false",
        ocr_enabled=os.getenv("AUREVIA_OCR", "true").lower() != "false",
        browser_timeout_s=int(os.getenv("AUREVIA_BROWSER_TIMEOUT", "30")),
    )


