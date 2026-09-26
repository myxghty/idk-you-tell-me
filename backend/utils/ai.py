import os
import json
import requests

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

# Maps the frontend's level chips to instructions for the prompt.
LEVEL_INSTRUCTIONS = {
    "beginner": "Use very simple vocabulary and short sentences, as if explaining to someone new to the subject entirely.",
    "intermediate": "Use standard academic language appropriate for a typical secondary-school student.",
    "advanced": "Use more precise, technical language appropriate for an advanced high-school or early college student.",
    "undergrad": "Use rigorous, discipline-appropriate academic language appropriate for an undergraduate course.",
    "simple": "Use short sentences, simple vocabulary, and avoid jargon. This version is for accessibility (e.g. dyslexia-friendly, ESL learners, younger students).",
}


def build_prompt(text, language=None, level=None):
    if language and language.lower() != "english":
        language_line = (
            f"Write ALL output fields (summary, glossary, quiz, flashcards, "
            f"outdated_flags) in {language}, not English."
        )
    else:
        language_line = "Write all output in English."

    level_key = (level or "intermediate").lower()
    level_line = LEVEL_INSTRUCTIONS.get(level_key, LEVEL_INSTRUCTIONS["intermediate"])

    return f"""You are an assistant that converts raw educational text into structured, reusable learning materials for an Open Educational Resources (OER) platform.

{language_line}
{level_line}

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


def run_generation(text, language=None, level=None):
    """
    Calls Gemini and returns (data, error). Exactly one of the two is None.
    error is a dict {"error": str, "status": int} ready to be returned to the client.
    """
    if not text or not isinstance(text, str) or len(text.strip()) < 20:
        return None, {
            "error": "Please provide 'text' (string, at least ~20 characters).",
            "status": 400,
        }

    if not GEMINI_API_KEY:
        return None, {
            "error": "Server misconfigured: GEMINI_API_KEY is not set. Add it to your .env file.",
            "status": 500,
        }

    prompt = build_prompt(text, language, level)

    try:
        response = requests.post(
            GEMINI_URL,
            params={"key": GEMINI_API_KEY},
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"response_mime_type": "application/json"},
            },
            timeout=60,
        )
    except requests.RequestException as err:
        return None, {"error": f"Could not reach Gemini API: {err}", "status": 502}

    if not response.ok:
        print("Gemini API error:", response.status_code, response.text)
        return None, {
            "error": "Upstream AI API error",
            "detail": response.text,
            "status": 502,
        }

    data = response.json()
    candidates = data.get("candidates") or []
    candidate = candidates[0] if candidates else None
    parts = (candidate or {}).get("content", {}).get("parts", [])
    raw_text = "\n".join(p.get("text", "") for p in parts)

    if not raw_text:
        print("Unexpected Gemini response shape:", json.dumps(data))
        return None, {
            "error": "Model returned no content. It may have blocked the input — check server logs.",
            "status": 502,
        }

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        print("JSON parse failed. Raw model output:\n", raw_text)
        return None, {
            "error": "Model did not return valid JSON. See server logs for raw output.",
            "status": 502,
        }

    return parsed, None


def translate_text(text, target_language):
    """
    Plain-text translation (used by the Translate tab). Returns (translation, error).
    Unlike run_generation, this does NOT use JSON mode — we just want the
    translated text back, not a structured object.
    """
    if not text or not isinstance(text, str) or len(text.strip()) < 1:
        return None, {"error": "Please provide 'text' to translate.", "status": 400}

    if not target_language or not isinstance(target_language, str):
        return None, {"error": "Please provide 'target_language'.", "status": 400}

    if not GEMINI_API_KEY:
        return None, {
            "error": "Server misconfigured: GEMINI_API_KEY is not set. Add it to your .env file.",
            "status": 500,
        }

    prompt = (
        f"Translate the following text into {target_language}. "
        f"Preserve the meaning and tone naturally rather than translating word-for-word. "
        f"Return ONLY the translated text, with no preamble, no explanation, and no quotation marks around it.\n\n"
        f"TEXT:\n\"\"\"\n{text}\n\"\"\""
    )

    try:
        response = requests.post(
            GEMINI_URL,
            params={"key": GEMINI_API_KEY},
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=60,
        )
    except requests.RequestException as err:
        return None, {"error": f"Could not reach Gemini API: {err}", "status": 502}

    if not response.ok:
        print("Gemini API error:", response.status_code, response.text)
        return None, {"error": "Upstream AI API error", "detail": response.text, "status": 502}

    data = response.json()
    candidates = data.get("candidates") or []
    candidate = candidates[0] if candidates else None
    parts = (candidate or {}).get("content", {}).get("parts", [])
    translation = "\n".join(p.get("text", "") for p in parts).strip()

    if not translation:
        return None, {
            "error": "Model returned no content. It may have blocked the input.",
            "status": 502,
        }

    return translation, None
