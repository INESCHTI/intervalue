from __future__ import annotations

from pathlib import Path

from ..config import settings
from ..models import TestCase


def execute_web(test_case: TestCase) -> dict:
    from selenium import webdriver
    from selenium.webdriver.common.by import By

    driver = webdriver.Chrome()
    try:
        driver.get(settings.web_base_url)
        # DOM = accès aux éléments HTML pour les interactions et les assertions.
        input_el = driver.find_element(By.CSS_SELECTOR, "#chat-input")
        input_el.send_keys(test_case.input)
        submit_btn = driver.find_element(By.CSS_SELECTOR, "#send-button")
        submit_btn.click()
        driver.implicitly_wait(5)
        screenshot = Path(settings.screenshot_dir) / f"{test_case.id}.png"
        screenshot.parent.mkdir(parents=True, exist_ok=True)
        driver.save_screenshot(str(screenshot))
        actual_text = driver.page_source
        return {
            "id": test_case.id,
            "canal": "web",
            "status": "ok",
            "actual": actual_text,
            "screenshot": str(screenshot),
        }
    finally:
        driver.quit()
