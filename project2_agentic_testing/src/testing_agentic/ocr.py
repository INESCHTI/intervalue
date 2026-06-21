from __future__ import annotations

from pathlib import Path


def read_text_from_image(image_path: str) -> str:
    from PIL import Image
    import pytesseract

    image = Image.open(Path(image_path))
    return pytesseract.image_to_string(image)
