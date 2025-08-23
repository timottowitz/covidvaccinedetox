# Here are your Instructions

## Operations

### Periodic Knowledge Reconcile (cron)
A helper script triggers a backend reconcile so that generated knowledge (markdown files in `frontend/public/knowledge`) gets linked back to uploaded resources automatically.

- Script:
  - `scripts/reconcile_knowledge.sh`
  - Reads `REACT_APP_BACKEND_URL` from `frontend/.env`
  - Calls `POST $REACT_APP_BACKEND_URL/api/knowledge/reconcile`

- Example crontab (every 10 minutes):
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


