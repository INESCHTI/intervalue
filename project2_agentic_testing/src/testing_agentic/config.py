from dataclasses import dataclass


@dataclass(slots=True)
class Settings:
    api_base_url: str = "http://127.0.0.1:8000"
    web_base_url: str = "http://127.0.0.1:3000"
    screenshot_dir: str = "reports/screenshots"
    headless: bool = True
    ocr_enabled: bool = False


settings = Settings()
