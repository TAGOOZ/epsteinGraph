# API Contracts

## GET /api/search

### Params
- q (string, required)
- limit (number, optional, default 20)
- offset (number, optional, default 0)

### Response (200)
```json
{
  "query": "string",
  "hits": [],
  "offset": 0,
  "limit": 20,
  "total": 0
}
```

### Errors
- 400: missing q
- 500: missing MEILI_HOST/MEILI_MASTER_KEY
- 502: meilisearch error
