const express = require("express");
const router = express.Router();

const GEMINI_API_KEY = process.env.GEMINI_API_KEY;
// Flash models are fast and free-tier friendly — good fit for a live demo.
// Override via .env if your key has access to a different model.
const MODEL = process.env.GEMINI_MODEL || "gemini-2.5-flash";
const GEMINI_URL = `https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent`;

// --- Prompt builder -------------------------------------------------------
// One call returns everything the frontend needs. Keeping it to a single
// call reduces latency and integration surface for the hackathon timeframe.
function buildPrompt(text, language, mode) {
  const languageLine =
    language && language.toLowerCase() !== "english"
      ? `Write ALL output fields (summary, glossary, quiz, flashcards, outdated_flags) in ${language}, not English.`
      : "Write all output in English.";

  const modeLine =
    mode === "simplified"
      ? "Use short sentences, simple vocabulary, and avoid jargon. This version is for accessibility (e.g. dyslexia-friendly, ESL learners, younger students)."
      : "Use standard academic language appropriate for the source material's level.";

  return `You are an assistant that converts raw educational text into structured, reusable learning materials for an Open Educational Resources (OER) platform.

${languageLine}
${modeLine}

Given the SOURCE TEXT below, return a JSON object with exactly this shape:

{
  "summary": "string, 3-5 sentences, plain-language overview of the source text",
  "glossary": [ { "term": "string", "definition": "string" } ],
  "quiz": [ { "question": "string", "options": ["string","string","string","string"], "answer": "string (must exactly match one of the options)" } ],
  "flashcards": [ { "front": "string", "back": "string" } ],
  "outdated_flags": [ { "excerpt": "string, exact quote from the source text", "reason": "string, why this may be outdated as of 2026", "suggested_update": "string, what to check or how to update it" } ]
}

Rules:
- Produce exactly 5 quiz questions and exactly 4 flashcards, unless the source text is too short to support that — in that case produce as many as make sense.
- Produce 3-6 glossary terms drawn from actual terms in the text.
- For outdated_flags: only flag real candidates — stale statistics, superseded terminology, old dates/versions, dead technologies, or facts likely to have changed. If nothing is outdated, return an empty array. Do not force flags that aren't genuine.
- Never invent facts not supported by the source text.

SOURCE TEXT:
"""
${text}
"""`;
}

router.post("/", async (req, res) => {
  try {
    const { text, options = {} } = req.body;
    const { language, mode } = options;

    if (!text || typeof text !== "string" || text.trim().length < 20) {
      return res.status(400).json({
        error: "Please provide 'text' (string, at least ~20 characters) in the request body.",
      });
    }

    if (!GEMINI_API_KEY) {
      return res.status(500).json({
        error: "Server misconfigured: GEMINI_API_KEY is not set. Add it to your .env file.",
      });
    }

    const prompt = buildPrompt(text, language, mode);

    const response = await fetch(`${GEMINI_URL}?key=${GEMINI_API_KEY}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        contents: [{ parts: [{ text: prompt }] }],
        generationConfig: {
          // Gemini's native JSON mode — much more reliable than asking
          // nicely and hoping the model skips markdown fences.
          response_mime_type: "application/json",
        },
      }),
    });

    if (!response.ok) {
      const errText = await response.text();
      console.error("Gemini API error:", response.status, errText);
      return res.status(502).json({ error: "Upstream AI API error", detail: errText });
    }

    const data = await response.json();

    const candidate = data.candidates && data.candidates[0];
    const rawText =
      candidate &&
      candidate.content &&
      candidate.content.parts &&
      candidate.content.parts.map((p) => p.text || "").join("\n");

    if (!rawText) {
      console.error("Unexpected Gemini response shape:", JSON.stringify(data));
      return res.status(502).json({
        error: "Model returned no content. It may have blocked the input — check server logs.",
      });
    }

    let parsed;
    try {
      parsed = JSON.parse(rawText);
    } catch (parseErr) {
      console.error("JSON parse failed. Raw model output:\n", rawText);
      return res.status(502).json({
        error: "Model did not return valid JSON. See server logs for raw output.",
      });
    }

    return res.json(parsed);
  } catch (err) {
    console.error("Unexpected error in /api/generate:", err);
    return res.status(500).json({ error: "Internal server error" });
  }
});

module.exports = router;
