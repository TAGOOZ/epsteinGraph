#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="NER pipeline for chunks")
    parser.add_argument(
        "--database-url",
        default="",
        help="Postgres connection string (or set DATABASE_URL)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Max number of chunks to process",
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Offset for chunk selection",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    database_url = args.database_url or os.environ.get("DATABASE_URL", "")
    if not database_url:
        raise SystemExit("DATABASE_URL is required")

    try:
        import psycopg
    except ModuleNotFoundError as exc:  # pragma: no cover - runtime dependency
        raise ModuleNotFoundError(
            "psycopg is required. Install with: pip install -r ops/requirements.txt"
        ) from exc

    from db import insert_mentions
    from extract import extract_entities
    from model import load_model

    nlp = load_model()

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, doc_id, page_no, text
                FROM chunks
                WHERE text IS NOT NULL AND text <> ''
                ORDER BY id
                LIMIT %s OFFSET %s
                """,
                (args.limit, args.offset),
            )
            rows = cur.fetchall()

            for chunk_id, doc_id, page_no, text in rows:
                mentions = extract_entities(text, nlp)
                insert_mentions(
                    cur,
                    doc_id=str(doc_id),
                    page_no=int(page_no),
                    chunk_id=str(chunk_id),
                    mentions=mentions,
                )

            conn.commit()

    print(f"Processed {len(rows)} chunks")


if __name__ == "__main__":
    main()
