CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$ BEGIN
  CREATE TYPE entity_type AS ENUM ('person', 'org', 'place', 'other');
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
  CREATE TYPE edge_type AS ENUM ('co_doc', 'co_paragraph', 'near');
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
  CREATE TYPE job_type AS ENUM ('crawl', 'extract', 'ner', 'index', 'graph');
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
  CREATE TYPE job_status AS ENUM ('queued', 'running', 'done', 'failed');
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

CREATE TABLE IF NOT EXISTS documents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_url text NOT NULL UNIQUE,
  source_host text NOT NULL,
  dataset integer,
  title text,
  published_date date,
  file_sha256 text,
  mime_type text,
  page_count integer,
  ocr_quality real,
  ingested_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (ocr_quality IS NULL OR (ocr_quality >= 0 AND ocr_quality <= 1))
);

CREATE INDEX IF NOT EXISTS documents_dataset_idx ON documents (dataset);
CREATE INDEX IF NOT EXISTS documents_published_date_idx ON documents (published_date);
CREATE INDEX IF NOT EXISTS documents_file_sha256_idx ON documents (file_sha256);

CREATE TABLE IF NOT EXISTS doc_pages (
  doc_id uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  page_no integer NOT NULL,
  text text,
  page_sha256 text,
  PRIMARY KEY (doc_id, page_no)
);

CREATE TABLE IF NOT EXISTS chunks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  doc_id uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  page_no integer NOT NULL,
  chunk_no integer NOT NULL,
  text text,
  start_char integer,
  end_char integer,
  chunk_sha256 text,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (doc_id, page_no, chunk_no)
);

CREATE INDEX IF NOT EXISTS chunks_doc_id_idx ON chunks (doc_id);
CREATE INDEX IF NOT EXISTS chunks_chunk_sha256_idx ON chunks (chunk_sha256);

CREATE TABLE IF NOT EXISTS entities (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  canonical_text text NOT NULL,
  type entity_type NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (canonical_text, type)
);

CREATE INDEX IF NOT EXISTS entities_type_idx ON entities (type);

CREATE TABLE IF NOT EXISTS entity_mentions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_id uuid NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
  doc_id uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  page_no integer NOT NULL,
  chunk_id uuid NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
  mention_text text NOT NULL,
  start_char integer,
  end_char integer,
  confidence real,
  context_window text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS entity_mentions_entity_id_idx ON entity_mentions (entity_id);
CREATE INDEX IF NOT EXISTS entity_mentions_doc_id_idx ON entity_mentions (doc_id);
CREATE INDEX IF NOT EXISTS entity_mentions_chunk_id_idx ON entity_mentions (chunk_id);

CREATE TABLE IF NOT EXISTS edges (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_a_id uuid NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
  entity_b_id uuid NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
  edge_type edge_type NOT NULL,
  weight real NOT NULL DEFAULT 0,
  first_seen_at timestamptz,
  last_seen_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (entity_a_id <> entity_b_id),
  CHECK (entity_a_id < entity_b_id),
  UNIQUE (entity_a_id, entity_b_id, edge_type)
);

CREATE INDEX IF NOT EXISTS edges_entity_a_id_idx ON edges (entity_a_id);
CREATE INDEX IF NOT EXISTS edges_entity_b_id_idx ON edges (entity_b_id);
CREATE INDEX IF NOT EXISTS edges_edge_type_idx ON edges (edge_type);

CREATE TABLE IF NOT EXISTS edge_evidence (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  edge_id uuid NOT NULL REFERENCES edges(id) ON DELETE CASCADE,
  doc_id uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  page_no integer NOT NULL,
  chunk_id uuid NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
  start_char integer,
  end_char integer,
  evidence_score real,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS edge_evidence_edge_id_idx ON edge_evidence (edge_id);
CREATE INDEX IF NOT EXISTS edge_evidence_doc_id_idx ON edge_evidence (doc_id);
CREATE INDEX IF NOT EXISTS edge_evidence_chunk_id_idx ON edge_evidence (chunk_id);

CREATE TABLE IF NOT EXISTS jobs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  job_type job_type NOT NULL,
  status job_status NOT NULL DEFAULT 'queued',
  started_at timestamptz,
  ended_at timestamptz,
  error text,
  stats jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS jobs_job_type_idx ON jobs (job_type);
CREATE INDEX IF NOT EXISTS jobs_status_idx ON jobs (status);
