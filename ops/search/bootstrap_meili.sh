#!/usr/bin/env bash
set -euo pipefail

MEILI_HOST="${MEILI_HOST:-http://localhost:7700}"
MEILI_MASTER_KEY="${MEILI_MASTER_KEY:-changeme}"

curl -sS -H "Authorization: Bearer ${MEILI_MASTER_KEY}" \
  -X POST "${MEILI_HOST}/indexes" \
  -H 'Content-Type: application/json' \
  --data '{"uid":"chunks","primaryKey":"chunk_id"}'

curl -sS -H "Authorization: Bearer ${MEILI_MASTER_KEY}" \
  -X PUT "${MEILI_HOST}/indexes/chunks/settings" \
  -H 'Content-Type: application/json' \
  --data '{
    "searchableAttributes":["text","title","entities"],
    "filterableAttributes":["dataset","published_date","doc_id","entity_ids"],
    "sortableAttributes":["published_date"],
    "displayedAttributes":["chunk_id","doc_id","page_no","text","dataset","published_date","entities","entity_ids","source_url","title"],
    "rankingRules":["words","typo","proximity","attribute","sort","exactness"],
    "stopWords":[],
    "distinctAttribute":null
  }'

echo "Meilisearch index 'chunks' initialized."
