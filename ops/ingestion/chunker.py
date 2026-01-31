from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass
class Chunk:
    page_no: int
    chunk_no: int
    text: str
    start_char: int
    end_char: int


def chunk_page_text(page_no: int, text: str) -> list[Chunk]:
    chunks: list[Chunk] = []
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        return chunks

    cursor = 0
    chunk_no = 0
    for para in paragraphs:
        chunk_no += 1
        start = cursor
        end = start + len(para)
        chunks.append(
            Chunk(
                page_no=page_no,
                chunk_no=chunk_no,
                text=para,
                start_char=start,
                end_char=end,
            )
        )
        cursor = end + 2

    return chunks


def chunk_pages(pages: Iterable[tuple[int, str]]) -> list[Chunk]:
    all_chunks: list[Chunk] = []
    for page_no, text in pages:
        all_chunks.extend(chunk_page_text(page_no, text))
    return all_chunks
