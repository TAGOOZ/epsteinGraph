from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse


def load_processed_into_db(
    *,
    database_url: str,
    state_path: Path,
    max_docs: int | None = None,
) -> int:
    state = json.loads(state_path.read_text(encoding="utf-8"))
    url_meta = state.get("url_meta", {})

    processed_entries = [
        (url, meta)
        for url, meta in url_meta.items()
        if meta.get("processed_output")
    ]

    if max_docs is not None:
        processed_entries = processed_entries[:max_docs]

    if not processed_entries:
        return 0

    try:
        import psycopg
    except ModuleNotFoundError as exc:  # pragma: no cover - runtime dependency
        raise ModuleNotFoundError(
            "psycopg is required. Install with: pip install -r ops/requirements.txt"
        ) from exc

    inserted_docs = 0

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            for url, meta in processed_entries:
                processed_path = Path(meta["processed_output"])
                if not processed_path.exists():
                    continue

                payload = json.loads(processed_path.read_text(encoding="utf-8"))
                file_sha256 = payload.get("file_sha256")
                page_count = payload.get("page_count")
                source_url = meta.get("final_url") or url
                source_host = meta.get("source_host") or urlparse(source_url).netloc

                cur.execute(
                    """
                    INSERT INTO documents (source_url, source_host, file_sha256, page_count)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (source_url)
                    DO UPDATE SET
                      file_sha256 = EXCLUDED.file_sha256,
                      page_count = EXCLUDED.page_count,
                      updated_at = now()
                    RETURNING id
                    """,
                    (source_url, source_host, file_sha256, page_count),
                )
                row = cur.fetchone()
                if not row:
                    continue
                doc_id = row[0]
                meta["doc_id"] = str(doc_id)

                chunks = payload.get("chunks", [])
                write_chunks(cur, doc_id, chunks)

                inserted_docs += 1
            conn.commit()

    save_state(state_path, state)

    return inserted_docs


def write_chunks(cur, doc_id, chunks: Iterable[dict]) -> None:
    for chunk in chunks:
        text = chunk.get("text", "")
        chunk_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
        cur.execute(
            """
            INSERT INTO chunks (doc_id, page_no, chunk_no, text, start_char, end_char, chunk_sha256)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (doc_id, page_no, chunk_no)
            DO UPDATE SET
              text = EXCLUDED.text,
              start_char = EXCLUDED.start_char,
              end_char = EXCLUDED.end_char,
              chunk_sha256 = EXCLUDED.chunk_sha256
            """,
            (
                doc_id,
                chunk.get("page_no"),
                chunk.get("chunk_no"),
                text,
                chunk.get("start_char"),
                chunk.get("end_char"),
                chunk_sha256,
            ),
        )
