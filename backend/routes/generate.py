import os
import json
import requests
from flask import Blueprint, request, jsonify

generate_bp = Blueprint("generate", __name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
# Flash models are fast and free-tier friendly — good fit for a live demo.
# Override via .env if your key has access to a different model.
MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"


# --- Prompt builder ---------------------------------------------------------
# One call returns everything the frontend needs. Keeping it to a single
# call reduces latency and integration surface for the hackathon timeframe.
def build_prompt(text, language, mode):
    if language and language.lower() != "english":
        language_line = (
            f"Write ALL output fields (summary, glossary, quiz, flashcards, "
            f"outdated_flags) in {language}, not English."
        )
    else:
        language_line = "Write all output in English."

    if mode == "simplified":
        mode_line = (
            "Use short sentences, simple vocabulary, and avoid jargon. "
            "This version is for accessibility (e.g. dyslexia-friendly, "
            "ESL learners, younger students)."
        )
    else:
        mode_line = "Use standard academic language appropriate for the source material's level."

    return f"""You are an assistant that converts raw educational text into structured, reusable learning materials for an Open Educational Resources (OER) platform.

{language_line}
{mode_line}

Given the SOURCE TEXT below, return a JSON object with exactly this shape:

{{
  "summary": "string, 3-5 sentences, plain-language overview of the source text",
  "glossary": [ {{ "term": "string", "definition": "string" }} ],
  "quiz": [ {{ "question": "string", "options": ["string","string","string","string"], "answer": "string (must exactly match one of the options)" }} ],
  "flashcards": [ {{ "front": "string", "back": "string" }} ],
  "outdated_flags": [ {{ "excerpt": "string, exact quote from the source text", "reason": "string, why this may be outdated as of 2026", "suggested_update": "string, what to check or how to update it" }} ]
}}

Rules:
- Produce exactly 5 quiz questions and exactly 4 flashcards, unless the source text is too short to support that — in that case produce as many as make sense.
- Produce 3-6 glossary terms drawn from actual terms in the text.
- For outdated_flags: only flag real candidates — stale statistics, superseded terminology, old dates/versions, dead technologies, or facts likely to have changed. If nothing is outdated, return an empty array. Do not force flags that aren't genuine.
- Never invent facts not supported by the source text.

SOURCE TEXT:
\"\"\"
{text}
\"\"\""""


@generate_bp.route("/", methods=["POST"], strict_slashes=False)
def generate():
    try:
        body = request.get_json(silent=True) or {}
        text = body.get("text")
        options = body.get("options") or {}
        language = options.get("language")
        mode = options.get("mode")

        if not text or not isinstance(text, str) or len(text.strip()) < 20:
            return jsonify({
                "error": "Please provide 'text' (string, at least ~20 characters) in the request body."
            }), 400

        if not GEMINI_API_KEY:
            return jsonify({
                "error": "Server misconfigured: GEMINI_API_KEY is not set. Add it to your .env file."
            }), 500

        prompt = build_prompt(text, language, mode)

        response = requests.post(
            GEMINI_URL,
            params={"key": GEMINI_API_KEY},
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    # Gemini's native JSON mode — much more reliable than
                    # asking nicely and hoping the model skips markdown fences.
                    "response_mime_type": "application/json",
                },
            },
            timeout=60,
        )

        if not response.ok:
            print("Gemini API error:", response.status_code, response.text)
            return jsonify({"error": "Upstream AI API error", "detail": response.text}), 502

        data = response.json()

        candidates = data.get("candidates") or []
        candidate = candidates[0] if candidates else None
        parts = (candidate or {}).get("content", {}).get("parts", [])
        raw_text = "\n".join(p.get("text", "") for p in parts)

        if not raw_text:
            print("Unexpected Gemini response shape:", json.dumps(data))
            return jsonify({
                "error": "Model returned no content. It may have blocked the input — check server logs."
            }), 502

        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError:
            print("JSON parse failed. Raw model output:\n", raw_text)
            return jsonify({
                "error": "Model did not return valid JSON. See server logs for raw output."
            }), 502

        return jsonify(parsed)

    except Exception as err:
        print("Unexpected error in /api/generate:", err)
        return jsonify({"error": "Internal server error"}), 500
