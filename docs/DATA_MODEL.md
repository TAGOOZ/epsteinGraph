# Data Model

## documents
- id (uuid)
- source_url (text, unique)
- source_host (text)
- dataset (int)
- title (text)
- published_date (date)
- file_sha256 (text)
- mime_type (text)
- page_count (int)
- ocr_quality (float 0..1)
- ingested_at, updated_at

## doc_pages (optional)
- doc_id (uuid)
- page_no (int)
- text (text, optional)
- page_sha256 (text, optional)

## chunks
- id (uuid)
- doc_id (uuid)
- page_no (int)
- chunk_no (int)
- text (text, optional)
- start_char, end_char (int)
- chunk_sha256 (text)

## entities
- id (uuid)
- canonical_text (text)
- type (person/org/place/other)
- created_at

## entity_mentions
- id (uuid)
- entity_id (uuid)
- doc_id (uuid)
- page_no (int)
- chunk_id (uuid)
- mention_text (text)
- start_char, end_char (int)
- confidence (float)
- context_window (text, optional)

## edges
- id (uuid)
- entity_a_id (uuid)
- entity_b_id (uuid)
- edge_type (co_doc/co_paragraph/near)
- weight (float)
- first_seen_at, last_seen_at

## edge_evidence
- id (uuid)
- edge_id (uuid)
- doc_id (uuid)
- page_no (int)
- chunk_id (uuid)
- start_char, end_char (int)
- evidence_score (float)

## jobs
- id (uuid)
- job_type (crawl/extract/ner/index/graph)
- status (queued/running/done/failed)
- started_at, ended_at
- error (text)
- stats (jsonb)
