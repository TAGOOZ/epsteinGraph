# Project Decisions (Frozen)

## Goal
Evidence-first document explorer + entity graph + claim→evidence system over DOJ Epstein data.

## Non-goals
- No guilt labeling
- No identity resolution beyond text strings
- No PDF mirroring initially

## Frontend
- Platform: Vercel
- Framework: Next.js (App Router)
- Role: UI + read-only API routes

## Ops
- Platform: Azure free Linux VM (12 months)
- Role: ingestion, OCR, entity extraction, graph building, indexing
- Scheduler: cron or systemd timers

## Search
- Engine: Meilisearch (self-hosted on VM)

## Database
- PostgreSQL (initially on VM)

## Storage
- No long-term PDF storage
- Store extracted text + metadata only
- Canonical links to DOJ source URLs

## Data source
- DOJ Epstein dataset pages (file lists / ZIPs)
- No live querying of DOJ search UI

## Safety rules
- Evidence required for every entity mention and edge
- Disambiguation required for identical names
- Always show citations
