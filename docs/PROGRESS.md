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
- Azure VM: Python venv + ops dependencies installed at /opt/epsteinGraph/.venv
- Azure VM: Docker + docker-compose installed; Postgres + Meilisearch running
- Azure VM: .env created at /opt/epsteinGraph/.env
- Azure VM: Postgres schema migration applied
- Azure VM: Meilisearch index bootstrapped

## In progress
- None

## Next
- Graph building (edges + evidence)
- Claim → evidence evaluation stub
- UI pages (search + doc viewer shell)
