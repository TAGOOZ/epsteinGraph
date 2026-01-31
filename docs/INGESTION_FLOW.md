# Ingestion Flow (Boundaries)

## Allowed
- Use only DOJ dataset listing pages and direct file URLs
- Rate limit crawling
- Cache and dedupe downloads
- Store DOJ URLs as canonical sources

## Not allowed
- No bypassing bot protections
- No scraping interactive search UI

## Operational Limits
- Max concurrency: 2
- Crawl rate: 1 request/second
- Retry policy: exponential backoff (2s, 4s, 8s, max 5 attempts)
- User agent: "epsteinGraph/0.1 (contact: TBD)"
- Dedupe key: SHA-256 of file bytes
- Cache: re-use files by hash; no re-download if unchanged
- ZIPs are downloaded but not unpacked or processed yet
- Age verification responses are treated as blocked; do not bypass

## Local tooling
- ops/ingestion/cli.py provides crawl + download with rate limiting and caching
- ops/ingestion/seeds.example.txt lists DOJ dataset listing page seeds
- ops/ingestion/process.py extracts PDF text and produces chunked JSON outputs
- ops/ingestion/cli.py load-db loads processed outputs into Postgres (documents + chunks)
- ops/ingestion/cli.py index sends processed chunks to Meilisearch
- ops/ner/cli.py runs NER on chunks and writes entity mentions to Postgres
