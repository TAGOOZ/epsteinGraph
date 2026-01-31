from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse


class MeiliIndexer:
    def __init__(self, host: str, master_key: str) -> None:
        self.host = host.rstrip("/")
        self.master_key = master_key

    def upsert_chunks(self, chunks: list[dict]) -> None:
        import urllib.request

        url = f"{self.host}/indexes/chunks/documents"
        payload = json.dumps(chunks).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.master_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp.read()


def load_processed_outputs(
    *,
    state_path: Path,
    max_docs: int | None = None,
) -> Iterable[tuple[str, dict]]:
    state = json.loads(state_path.read_text(encoding="utf-8"))
    url_meta = state.get("url_meta", {})

    processed_entries = [
        (url, meta)
        for url, meta in url_meta.items()
        if meta.get("processed_output")
    ]

    if max_docs is not None:
        processed_entries = processed_entries[:max_docs]

    for url, meta in processed_entries:
        processed_path = Path(meta["processed_output"])
        if not processed_path.exists():
            continue
        payload = json.loads(processed_path.read_text(encoding="utf-8"))
        yield url, payload


def build_chunk_records(
    *,
    url: str,
    meta: dict,
    payload: dict,
) -> list[dict]:
    source_url = meta.get("final_url") or url
    source_host = meta.get("source_host") or urlparse(source_url).netloc
    doc_id = meta.get("doc_id")

    chunks = []
    for chunk in payload.get("chunks", []):
        chunks.append(
            {
                "chunk_id": f"{payload.get('file_sha256')}:{chunk.get('page_no')}:{chunk.get('chunk_no')}",
                "doc_id": doc_id,
                "page_no": chunk.get("page_no"),
                "text": chunk.get("text"),
                "dataset": meta.get("dataset"),
                "published_date": meta.get("published_date"),
                "entities": [],
                "entity_ids": [],
                "source_url": source_url,
                "title": meta.get("title"),
                "source_host": source_host,
            }
        )
    return chunks
