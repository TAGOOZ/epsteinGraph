# Project Plan

## 1) Tech stack

### Frontend + thin API
- Vercel (recommended for Next.js) or Netlify
- Next.js (App Router)
- API routes are read-only: query search + Postgres

### Ops / workers
- Microsoft Azure free Linux VM for 12 months
- Worker runtime: Python (fast to implement OCR/NLP) or Node.js (if you prefer)
- Scheduler on VM: systemd timers or cron (simple, reliable)

### Search engine (on the VM)
Pick ONE:
- Meilisearch (simpler, lighter, good UX, best for small VM)
- OpenSearch (more powerful; heavier; more ops)

Recommendation: start with Meilisearch. If you outgrow it, migrate later.

### Database
- PostgreSQL on the VM (free, you maintain it)
- Optional later: managed Postgres (if you want reliability and don’t mind paying)

### Storage
Don’t mirror PDFs initially.
Store only:
- text chunks
- metadata
- extracted entity mentions
- graph edges

Keep source_url to the DOJ original file.

## 2) System architecture

### Data flow
- Worker VM ingests DOJ documents (from stable “file list / dataset pages”, not the interactive search UI).
- Downloads PDF temporarily → extracts text (or OCR) → chunks → entities → edges.
- Writes to:
  - Postgres (metadata + entities + graph + provenance)
  - Search index (chunks + highlights fields)
- Frontend queries:
  - Search index for search/claim results
  - Postgres for doc/entity/graph pages
- “Open original” links to DOJ source_url.

Key principle: provenance everywhere
- Every entity mention and every graph edge must point back to:
  - doc_id
  - page
  - chunk_id
  - start_char, end_char (or snippet hash)
So every UI element has “Show evidence”.

## 3) Data model (Postgres)

Tables (minimum)

### documents
- id (uuid)
- source_url (text, unique)
- source_host (text) = “justice.gov”
- dataset (int) (if applicable)
- title (text)
- published_date (date nullable)
- file_sha256 (text)
- mime_type (text)
- page_count (int)
- ocr_quality (float 0..1)
- ingested_at, updated_at

### doc_pages (optional, but useful)
- doc_id
- page_no
- text (optional if you store only in search)
- page_sha256 (optional)

### chunks
- id (uuid)
- doc_id
- page_no
- chunk_no
- text (or omit if only in search)
- start_char, end_char
- chunk_sha256

### entities
- id (uuid)
- canonical_text (text) ← keep it as-is initially
- type (enum: person/org/place/other)
- created_at

### entity_mentions
- id
- entity_id
- doc_id
- page_no
- chunk_id
- mention_text (text)
- start_char, end_char
- confidence (float)
- context_window (text small) (optional)

### edges (graph)
- id
- entity_a_id
- entity_b_id
- edge_type (enum: co_doc / co_paragraph / near)
- weight (float)
- first_seen_at, last_seen_at

### edge_evidence
- edge_id
- doc_id
- page_no
- chunk_id
- start_char, end_char
- evidence_score

### jobs
- id
- job_type (crawl/extract/ner/index/graph)
- status (queued/running/done/failed)
- started_at, ended_at
- error (text)
- stats (jsonb)

This is enough to power everything.

## 4) Search index design (Meilisearch or OpenSearch)

Index at the “chunk” level (not whole docs)

Each indexed record = one chunk (paragraph or ~500–1500 chars)

Fields:
- chunk_id
- doc_id
- page_no
- text
- dataset
- published_date
- entities (array of strings) and/or entity_ids (array)
- source_url
- title

Filters you’ll want:
- dataset
- date range
- doc type/category (if you have it)
- entity filter (later)

Ranking signals (simple but effective):
- BM25 text relevance
- boost exact phrase matches
- boost chunks with better OCR quality
- boost chunks where query terms appear close together

Highlights:
- Use built-in highlighting for the text field.

## Ops scripts
- ops/search/bootstrap_meili.sh initializes the Meilisearch index and settings.

## 5) Ingestion pipeline (ops tasks)

Worker jobs (in order)

### Job A — Crawl index pages
Input: seed URLs (DOJ dataset pages / file listing pages)

Output:
- list of file URLs + metadata
- store/update documents rows

Anti-block:
- low concurrency (1–2)
- caching (ETag/Last-Modified)
- exponential backoff

### Job B — Download + hash
- Download file to temp disk
- Compute SHA256
- If same as existing hash → skip processing
- Extract PDF metadata (page count)

### Job C — Text extraction
- Try PDF text layer first
- If low text yield → OCR pages
- Save:
  - per page text (optional)
  - chunked text
  - ocr_quality score

OCR quality heuristic:
- ratio of alphabetic tokens
- ratio of dictionary-like words
- average token length
- garbage character rate

### Job D — Chunking
- Convert per-page text into chunks:
  - paragraph split
  - fallback to sentence grouping if no paragraphs
- Assign stable chunk_sha256 for dedupe

### Job E — Entity extraction (NER)
- Extract entities per chunk
- Store mentions + confidence
- Types: PERSON/ORG/GPE (place)
- Keep the raw string (no identity resolution)

### Job F — Graph generation
- For each chunk:
  - take its entities
  - create pairwise edges with evidence rows
- Aggregate to edges.weight

Edge types:
- co_paragraph (strong)
- co_doc (weak)
- near (optional; within N words)

### Job G — Indexing
- Upsert chunk records into search index
- Include metadata + entity list

### Job H — QA + reporting
- Count docs processed, OCR rate, failures
- Emit a daily “ingestion report” (stored in DB + logs)

Scheduling
- Hourly: crawl + process new/changed docs
- Nightly: rebuild graph weights (optional) + run quality checks

## 6) Backend API (thin, stable)

These endpoints can live as:
- Next.js Route Handlers on Vercel (read-only), or
- a small API service on the Azure VM (also fine)

Required endpoints

### GET /api/search
- params: q, filters, pagination
- returns: chunk hits with highlights + doc metadata

### GET /api/docs/:docId
- returns: doc metadata + pages/chunks (or chunk ids)
- supports q to fetch “hits inside this doc”

### GET /api/entities/:entityId
- returns: entity summary, mentions, top co-mentions, evidence pointers

### GET /api/entities/:entityId/graph
- returns: neighbor nodes + edges + top evidence snippets per edge

### POST /api/claims/evaluate
Input:
- free text claim OR structured (subject/predicate/object)
- filters

Output:
- supporting evidence hits
- context/caveats hits
- status: supported/mixed/not_supported/insufficient
- all with citations

## 7) UI/UX design ideas

### A) Search page that feels powerful
Query bar supports:
- quotes for phrases
- AND/OR/-term

Filter panel:
- dataset
- date range
- doc type
- OCR quality slider (optional)

Results show:
- strongest snippet
- chips of matched entities in that snippet
- quick actions: “Open in doc”, “Open original”

### B) Doc viewer that beats PDFs
- Left: page/chunk navigation
- Center: text with highlights
- Right: “entities in this doc” + “related docs”
- Hit navigation: Next/Prev match
- “Open original” button (source_url)

### C) Entity page that’s evidence-first
Top: entity string + type + “possible duplicates” section

Tabs:
- Mentions (chronological)
- Neighbors (graph list view)
- Graph (visual)

Every neighbor entry has:
- why connected
- top 3 evidence snippets

### D) Graph that doesn’t become a conspiracy map
- Default to a small subgraph (10–30 neighbors)

Sliders:
- minimum edge weight
- edge type (paragraph vs doc)

Every edge click opens “evidence drawer” with snippets

### E) Claim checker experience
Two modes:
- “Simple”: paste claim
- “Structured”: subject + verb + object + filters

Output buckets:
- Supporting evidence
- Context / caveats
- Neutral mentions

Always show “insufficient evidence” aggressively when needed

## 8) Safety + credibility controls (must-have)
- “Evidence only” language everywhere.
- No “guilt labels”.
- Store and display the exact citation snippet for any claim/edge.
- Disambiguation UI: “This name may refer to multiple people.”
- Rate limit public API (avoid scraping your site).
- Audit logs for ingestion and updates.

## 9) Security and ops

### VM hardening
Firewall: allow only:
- SSH (restricted IP if possible)
- Search port (only from your frontend/API or behind a reverse proxy)
- DB port (localhost only)

Use Caddy/Nginx reverse proxy with TLS

### Secrets
- .env on VM only
- never in repo

### Backups
- Nightly Postgres dump to a safe location (even a second cheap storage later)
- Snapshot the search index periodically (or rebuildable from Postgres chunks)

### Observability
Basic metrics:
- docs ingested/day
- OCR failure rate
- average search latency
- API error rate

## 10) Task plan (work breakdown)

### Phase 1 — Foundation
- Repo + monorepo layout
- Deploy frontend skeleton to Vercel/Netlify
- Provision Azure VM + firewall + docker
- Spin up Postgres + Meilisearch/OpenSearch in docker-compose
- Define schemas + migrations
- Implement minimal search API (mocked first)

Deliverable: site deploys, infra runs, empty search works.

### Phase 2 — Ingestion v1 (documents → chunks → search)
- Crawler for dataset pages
- Downloader + hash + dedupe
- Text extraction (PDF text layer only first)
- Chunking
- Index chunks into search
- Search UI shows real hits + doc viewer renders chunk text
- Store source_url and link out

Deliverable: doc explorer works end-to-end on real data.

### Phase 3 — OCR + quality
- OCR pipeline for scanned docs
- OCR quality scoring
- UI filter: “OCR quality”
- Reprocessing job for low-quality docs

Deliverable: coverage improves; search works on scanned PDFs.

### Phase 4 — Entities + entity pages
- NER per chunk
- Entity + mention tables
- Entity page: mentions list
- “Related entities” computed by co-mention

Deliverable: entity browsing is real and useful.

### Phase 5 — Graph + evidence-backed edges
- Build edge generation per chunk
- Aggregate weights + store evidence pointers
- Graph API
- Graph UI (start list view, add visualization after)

Deliverable: graph exploration with proof.

### Phase 6 — Claim → evidence engine
- Claim parser (simple first; structured second)
- Evidence pack generator (search + ranking)
- Context/caveats heuristic searches
- Output status classifier (supported/mixed/insufficient)
- Claim UI

Deliverable: claim checker that doesn’t lie.

### Phase 7 — Polish + scale
- Better relevance tuning
- Faster doc viewer (server-side caching)
- Dedupe near-identical docs
- Admin dashboard for ingestion health
- Backup/restore tested

Deliverable: production-grade stability.

## 11) One decision you should lock now
For your Azure free VM reality, pick:
- Meilisearch if you want it to run comfortably and focus on product.
- OpenSearch if you want max filtering/query power and accept heavier ops.
