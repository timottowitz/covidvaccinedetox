# Here are your Instructions

## Operations

### Periodic Knowledge Reconcile (cron)
A helper script triggers a backend reconcile so that generated knowledge (markdown files in `frontend/public/knowledge`) gets linked back to uploaded resources automatically.

- Script:
  - `scripts/reconcile_knowledge.sh`
  - Reads backend `.env` from repo root if present (`/app/.env`)
  - Calls `POST $BACKEND_URL/api/knowledge/reconcile`

- Configure backend URL:
  - Copy `.env.example` to `.env` at repo root and set `BACKEND_URL` (e.g., `http://localhost:8001`), or pass it inline/arg.

- Example crontab (every 10 minutes):
```
*/10 * * * * BACKEND_URL=https://your-backend.example.com /bin/bash /app/scripts/reconcile_knowledge.sh >> /var/log/knowledge_reconcile.log 2>&1
```
Or with repo root .env:
```
*/10 * * * * /bin/bash /app/scripts/reconcile_knowledge.sh >> /var/log/knowledge_reconcile.log 2>&1
```

- Verify:
```
tail -n 100 /var/log/knowledge_reconcile.log
```

### Knowledge Generation Pipeline (PDF/Video)
- PDF upload → Chunkr.ai ingestion → markdown saved to `frontend/public/knowledge/*.md` → metadata updated with `knowledge_url`.
- Video upload → Gemini Files API summarization → markdown saved to `frontend/public/knowledge/*.md` → metadata updated with `knowledge_url`.

### Keys (backend only)
Set these in `backend/.env` and restart backend:
```
CHUNKR_API_KEY=...
GEMINI_API_KEY=...
```

### Thumbnails
The backend generates PDF/video thumbnails at:
```
frontend/public/resources/bioweapons/thumbnails/{slug}.jpg
```

### API Endpoints
- `GET /api/resources` – returns resources, now auto‑reconciling knowledge links.
- `POST /api/resources/upload` – upload PDF/video; enqueues background ingestion.
- `GET /api/knowledge/status` – list knowledge markdown files.
- `POST /api/knowledge/reconcile` – map knowledge files to resources (idempotent).

### Frontend
- Resources page shows “Open Knowledge” button when available and “Processing…” badge otherwise.
- Knowledge page (`/knowledge`) lists generated markdown and shows a preview with:
  - Parsed YAML frontmatter (title/date/type/tags/summary)
  - Quick chunk anchors
  - Copy Summary and Copy Citation buttons


