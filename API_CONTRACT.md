# API Contract — OER Refresh & Reuse

Base URL (local dev): `http://localhost:3001`

---

## POST /api/generate

Converts raw educational text into structured learning materials.

### Request
```json
{
  "text": "Paste of textbook chapter or lecture notes...",
  "options": {
    "language": "English",      // optional, e.g. "Hindi", "Tamil". Defaults to English.
    "mode": "standard"          // optional: "standard" | "simplified". Defaults to "standard".
  }
}
```

- `text` is required, minimum ~20 characters.
- `options` is optional entirely; omit it for defaults.

### Response `200 OK`
```json
{
  "summary": "string",
  "glossary": [
    { "term": "string", "definition": "string" }
  ],
  "quiz": [
    {
      "question": "string",
      "options": ["string", "string", "string", "string"],
      "answer": "string (matches one of the options exactly)"
    }
  ],
  "flashcards": [
    { "front": "string", "back": "string" }
  ],
  "outdated_flags": [
    {
      "excerpt": "string, exact quote from the source",
      "reason": "string",
      "suggested_update": "string"
    }
  ]
}
```

Notes for frontend:
- `outdated_flags` can be an **empty array** — always handle that case in the UI (e.g. show "No outdated content detected" rather than a blank section).
- `quiz` normally has 5 items, `flashcards` normally has 4, but both can be shorter if the source text is short. Don't hardcode array lengths.

### Error responses
```json
{ "error": "human-readable message" }
```
- `400` — missing/too-short `text`
- `500` — server misconfigured (missing API key) or unexpected error
- `502` — upstream AI API failed, or returned unparseable output

---

## POST /api/library

Saves a generated module so it shows up in a shared "library" list.

### Request
```json
{
  "title": "string, e.g. chapter name",
  "source_text": "string, optional, original pasted text",
  "data": { ...the full /api/generate response... }
}
```

### Response `201 Created`
```json
{
  "id": 1,
  "title": "string",
  "source_text": "string",
  "data": { ... },
  "created_at": "ISO timestamp"
}
```

## GET /api/library

Returns a list of saved modules (summary only, no full content).

### Response `200 OK`
```json
[
  { "id": 1, "title": "string", "created_at": "ISO timestamp" }
]
```

## GET /api/library/:id

Returns full detail for one saved module (same shape as the POST response).

---

## GET /api/health

Quick check that the server is up. Returns `{ "status": "ok" }`.

---

## Notes / gotchas for integration
- Backend is in-memory only — the library resets if the server restarts. That's expected for the hackathon; don't rely on persistence across a demo restart.
- CORS is wide open (`cors()` with no config), so frontend can call from any origin/port during dev.
- `/api/generate` typically takes a few seconds (LLM call) — frontend should show a loading state.
