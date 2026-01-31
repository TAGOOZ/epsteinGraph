# epsteinGraph

Repo scaffold for an evidence-first document explorer, entity graph, and claim-to-evidence system over DOJ Epstein data.

## Layout
- apps/web: Next.js app (UI + read-only API routes)
- ops/*: ingestion, NER, graph, indexing pipelines
- infra: local services (Postgres, Meilisearch)
- docs: specs and frozen decisions
