from __future__ import annotations

from typing import Iterable

from extract import EntityMention


def upsert_entity(cur, text: str, entity_type: str) -> str:
    cur.execute(
        """
        INSERT INTO entities (canonical_text, type)
        VALUES (%s, %s)
        ON CONFLICT (canonical_text, type)
        DO UPDATE SET canonical_text = EXCLUDED.canonical_text
        RETURNING id
        """,
        (text, entity_type),
    )
    row = cur.fetchone()
    return str(row[0]) if row else ""


def insert_mentions(
    cur,
    *,
    doc_id: str,
    page_no: int,
    chunk_id: str,
    mentions: Iterable[EntityMention],
) -> None:
    for mention in mentions:
        entity_id = upsert_entity(cur, mention.text, mention.entity_type)
        if not entity_id:
            continue
        cur.execute(
            """
            INSERT INTO entity_mentions
              (entity_id, doc_id, page_no, chunk_id, mention_text, start_char, end_char, confidence)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                entity_id,
                doc_id,
                page_no,
                chunk_id,
                mention.text,
                mention.start_char,
                mention.end_char,
                None,
            ),
        )
