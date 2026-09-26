# OER Refresh & Reuse — Backend (Python)

Converts raw educational text (textbook excerpts, lecture notes) into a
summary, glossary, quiz, flashcards, and flags for likely-outdated content —
optionally in another language or a simplified/accessible form.

## Setup

```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

pip install -r requirements.txt
copy .env.example .env       # Windows (use `cp` on Mac/Linux)
```

Edit `.env` and add your `GEMINI_API_KEY`. Get a free key (no card required)
at https://aistudio.google.com/apikey

```bash
python app.py
```

Server runs on `http://localhost:3001` by default.

## Endpoints

Same API contract as the Node version — see
[API_CONTRACT.md](./API_CONTRACT.md) for full request/response shapes.

- `POST /api/generate` — main endpoint, takes text, returns structured learning materials
- `POST /api/library` — save a generated module
- `GET /api/library` — list saved modules
- `GET /api/library/<id>` — get one saved module in full
- `GET /api/health` — health check

## Testing without a frontend

```bash
curl -X POST http://localhost:3001/api/generate ^
  -H "Content-Type: application/json" ^
  -d "{\"text\": \"Paste at least a paragraph of educational text here for it to work.\"}"
```

(On Mac/Linux, use `\` instead of `^` for line continuation and single quotes
instead of escaped double quotes.)

## Before the demo

Pre-test your `/api/generate` prompt against the actual sample text you'll
use on stage, especially for `outdated_flags` — LLMs won't always flag
something unless the source text has a clear, genuine candidate (an old
statistic, a dead technology reference, a superseded date). Bake one
obvious outdated fact into your demo sample so the feature reliably fires
live.
