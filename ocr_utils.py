import re
import shutil
import unicodedata
from pathlib import Path

import pytesseract
from PIL import Image
from pytesseract.pytesseract import TesseractNotFoundError

COMMON_TESSERACT_PATHS = (
    "/opt/homebrew/bin/tesseract",
    "/usr/local/bin/tesseract",
)

TESSERACT_INSTALL_HINT = (
    "Install: brew install tesseract tesseract-lang\n"
    "  (tesseract-lang provides Vietnamese OCR data)"
)


def configure_tesseract() -> bool:
    if shutil.which("tesseract"):
        return True

    for path in COMMON_TESSERACT_PATHS:
        if Path(path).is_file():
            pytesseract.pytesseract.tesseract_cmd = path
            return True

    return False


def require_tesseract() -> None:
    if not configure_tesseract():
        raise SystemExit(
            "ERROR: tesseract not found or not in PATH.\n" + TESSERACT_INSTALL_HINT
        )


DESCRIPTION_REGION_FRACTION = 0.35


def ocr_image(path: Path, *, lang: str = "vie+eng", config: str = "") -> str:
    require_tesseract()
    with Image.open(path) as img:
        try:
            return pytesseract.image_to_string(
                img,
                lang=lang,
                config=config,
            )
        except TesseractNotFoundError as exc:
            raise SystemExit(
                "ERROR: tesseract not found or not in PATH.\n" + TESSERACT_INSTALL_HINT
            ) from exc


def ocr_description_region(path: Path, *, lang: str = "vie+eng") -> str:
    """OCR the top band where puzzle descriptions usually appear."""
    require_tesseract()
    with Image.open(path) as img:
        width, height = img.size
        crop = img.crop((0, 0, width, int(height * DESCRIPTION_REGION_FRACTION)))
        try:
            return pytesseract.image_to_string(
                crop,
                lang=lang,
                config="--psm 6",
            )
        except TesseractNotFoundError as exc:
            raise SystemExit(
                "ERROR: tesseract not found or not in PATH.\n" + TESSERACT_INSTALL_HINT
            ) from exc


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text.lower())
    without_marks = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", without_marks).strip()


def contains_keyword(text: str, keywords: tuple[str, ...]) -> bool:
    normalized = normalize_text(text)
    return any(keyword in normalized for keyword in keywords)


def line_contains_keyword(line: str, keywords: tuple[str, ...]) -> bool:
    return contains_keyword(line, keywords)
