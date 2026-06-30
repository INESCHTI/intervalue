from __future__ import annotations

import json
import time
from pathlib import Path

import httpx

from .config import Settings
from .models import ExecutionResult, ScenarioCase
from .ocr import read_screenshot_text


class ExecutorAgent:
    """Executor Agent: run each test through API, Web/Playwright, or Mobile stub."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def execute(self, test_case: ScenarioCase) -> ExecutionResult:
        if test_case.channel == "api":
            return self.execute_api(test_case)
        if test_case.channel == "web":
            return self.execute_web(test_case)
        return self.execute_mobile(test_case)

    def execute_api(self, test_case: ScenarioCase) -> ExecutionResult:
        started = time.perf_counter()
        try:
            with httpx.Client(timeout=45.0) as client:
                if test_case.method == "get":
                    response = client.get(
                        f"{self.settings.api_base_url}{test_case.path}",
                        headers={"Authorization": "Bearer dev-token"},
                    )
                else:
                    response = client.post(
                        f"{self.settings.api_base_url}/api/chat",
                        headers={"Authorization": "Bearer dev-token"},
                        json={
                            "message": test_case.input,
                            "display_message": test_case.input,
                            "conversation_id": f"qa-{test_case.id}",
                            "mode": "instant",
                        },
                    )
                body = response.text
                if response.status_code == 400:
                    body = f"400 guardrail forbidden: {body}"
                return ExecutionResult(
                    id=test_case.id,
                    channel=test_case.channel,
                    status=str(response.status_code),
                    actual=body if test_case.method == "get" else _read_sse_text(body),
                    latency_s=round(time.perf_counter() - started, 3),
                    evidence={"raw_response": body[:4000]},
                )
        except Exception as exc:
            return ExecutionResult(
                id=test_case.id,
                channel=test_case.channel,
                status="error",
                actual="",
                latency_s=round(time.perf_counter() - started, 3),
                error=str(exc),
            )

    def execute_web(self, test_case: ScenarioCase) -> ExecutionResult:
        started = time.perf_counter()
        screenshot = self.settings.output_dir / "screenshots" / f"{test_case.id}.png"
        screenshot.parent.mkdir(parents=True, exist_ok=True)

        try:
            from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            return ExecutionResult(
                id=test_case.id,
                channel=test_case.channel,
                status="missing-playwright",
                actual="",
                latency_s=round(time.perf_counter() - started, 3),
                error=f"Playwright is not installed: {exc}",
            )

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=self.settings.headless)
                page = browser.new_page(viewport={"width": 1440, "height": 1000})
                page.set_default_timeout(self.settings.browser_timeout_s * 1000)
                page.goto(f"{self.settings.web_base_url}{test_case.path}", wait_until="networkidle")
                page.locator("body").wait_for()

                if test_case.path == "/chat" and test_case.input:
                    input_el = page.locator("input.composer-input")
                    input_el.wait_for(state="visible")
                    input_el.fill(test_case.input)
                    page.locator("button[aria-label='Send message']").click()
                    page.wait_for_function(
                        "() => document.body.innerText.includes('Thinking...') === false"
                    )
                    time.sleep(0.5)
                elif test_case.path == "/":
                    page.wait_for_function(
                        "() => document.body.innerText.includes('Portfolio Overview')"
                    )
                    page.wait_for_function("() => document.body.innerText.includes('$20.4M')")

                actual = page.locator("body").inner_text()
                page.screenshot(path=str(screenshot), full_page=True)
                current_url = page.url
                title = page.title()
                browser.close()

                ocr_text = read_screenshot_text(screenshot) if self.settings.ocr_enabled else None
                return ExecutionResult(
                    id=test_case.id,
                    channel=test_case.channel,
                    status="ok",
                    actual=actual,
                    latency_s=round(time.perf_counter() - started, 3),
                    screenshot=str(screenshot),
                    ocr_text=ocr_text,
                    evidence={"url": current_url, "title": title},
                )
        except PlaywrightTimeoutError as exc:
            return ExecutionResult(
                id=test_case.id,
                channel=test_case.channel,
                status="timeout",
                actual="",
                latency_s=round(time.perf_counter() - started, 3),
                screenshot=str(screenshot) if screenshot.exists() else None,
                error=str(exc),
            )
        except Exception as exc:
            return ExecutionResult(
                id=test_case.id,
                channel=test_case.channel,
                status="error",
                actual="",
                latency_s=round(time.perf_counter() - started, 3),
                screenshot=str(screenshot) if screenshot.exists() else None,
                error=str(exc),
            )

    def execute_mobile(self, test_case: ScenarioCase) -> ExecutionResult:
        return ExecutionResult(
            id=test_case.id,
            channel=test_case.channel,
            status="not-configured",
            actual="",
            latency_s=0.0,
            error="Mobile Appium execution is reserved for an emulator/device configuration.",
        )


def _read_sse_text(raw: str) -> str:
    chunks: list[str] = []
    for line in raw.splitlines():
        if not line.startswith("data: ") or line.strip() == "data: [DONE]":
            continue
        try:
            payload = json.loads(line[6:])
            token = payload.get("token") or payload.get("reasoning") or ""
            chunks.append(str(token))
        except json.JSONDecodeError:
            chunks.append(line[6:])
    return "".join(chunks).strip() or raw[:2000]


