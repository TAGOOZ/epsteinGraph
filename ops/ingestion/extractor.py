from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ModuleNotFoundError as exc:  # pragma: no cover - runtime dependency
    raise ModuleNotFoundError(
        "PyMuPDF is required. Install with: pip install -r ops/requirements.txt"
    ) from exc


@dataclass
class PageText:
    page_no: int
    text: str


@dataclass
class ExtractResult:
    pages: list[PageText]
    page_count: int


def extract_pdf_text(path: Path) -> ExtractResult:
    doc = fitz.open(path)
    pages: list[PageText] = []
    for i in range(len(doc)):
        page = doc.load_page(i)
        text = page.get_text("text")
        pages.append(PageText(page_no=i + 1, text=text))
    return ExtractResult(pages=pages, page_count=len(doc))
