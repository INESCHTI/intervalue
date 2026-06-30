from __future__ import annotations

from pathlib import Path


def read_screenshot_text(path: str | Path) -> str:
    """OCR helper: extract visible text from a screenshot when Tesseract is installed."""
    try:
        from PIL import Image
        import pytesseract
    except ImportError as exc:
        return f"[OCR unavailable: missing dependency {exc.name}]"

    try:
        image = Image.open(path)
        return pytesseract.image_to_string(image).strip()
    except Exception as exc:
        return f"[OCR unavailable: {exc}]"


