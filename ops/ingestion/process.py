from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from chunker import chunk_pages


def process_pdf(path: Path, output_dir: Path) -> dict:
    from extractor import extract_pdf_text

    result = extract_pdf_text(path)

    page_payload = [
        {"page_no": page.page_no, "text": page.text}
        for page in result.pages
    ]

    chunks = chunk_pages([(p.page_no, p.text) for p in result.pages])
    chunk_payload = [asdict(chunk) for chunk in chunks]

    text_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    output_dir.mkdir(parents=True, exist_ok=True)

    out = {
        "file_sha256": text_hash,
        "page_count": result.page_count,
        "pages": page_payload,
        "chunks": chunk_payload,
    }

    out_path = output_dir / f"{text_hash}.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    return {"output": str(out_path), "chunks": len(chunks)}
