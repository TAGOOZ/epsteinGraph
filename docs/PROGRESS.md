# Progress

Last updated: 2026-01-31

## Completed
- Repo scaffold + docs structure
- Local infra: docker-compose (Postgres + Meilisearch)
- Next.js App Router skeleton + /api/search
- Postgres schema migration (0001_init.sql)
- Meilisearch bootstrap script + index settings
- Ingestion: crawl + download skeleton
- Extraction + chunking (PDF text layer only)
- Load processed outputs into Postgres (documents + chunks)
- Index processed chunks into Meilisearch
- NER pipeline (spaCy) to entities + mentions
- Azure VM hardening (UFW + fail2ban + SSH hardening)
- Repo synced to Azure VM at /opt/epsteinGraph

## In progress
- None

## Next
- Graph building (edges + evidence)
- Claim → evidence evaluation stub
- UI pages (search + doc viewer shell)
