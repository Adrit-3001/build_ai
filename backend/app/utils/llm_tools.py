import json
import re
from typing import Any, Dict, Optional

import requests

from app.config import OLLAMA_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT


MAX_MODEL_INPUT_CHARS = 12000


def _truncate_text(text: str) -> str:
    text = text.strip()
    if len(text) <= MAX_MODEL_INPUT_CHARS:
        return text
    return text[:MAX_MODEL_INPUT_CHARS]


def _extract_json(text: str) -> Dict[str, Any]:
    text = text.strip()

    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        return json.loads(match.group(0))

    raise ValueError("Model did not return valid JSON.")


def _call_ollama(system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": OLLAMA_MODEL,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        },
        timeout=OLLAMA_TIMEOUT,
    )
    response.raise_for_status()

    data = response.json()
    content = data["message"]["content"]
    return _extract_json(content)


def smart_generate(
    text: str,
    mode: str,
    learner_type: str,
    difficulty: str,
    estimated_minutes: int = 5,
) -> Optional[Dict[str, Any]]:
    safe_text = _truncate_text(text)

    system_prompt = """
You are a study assistant that transforms notes into structured study outputs.
You MUST return valid JSON only.
Do not include markdown fences.
Do not include commentary outside JSON.
Be accurate and grounded in the provided notes.
Do not invent facts not supported by the notes.
Keep outputs concise, useful, and student-friendly.
For summary and simplified modes, ALWAYS return a non-empty "result".
"""

    user_prompt = f"""
Mode: {mode}
Learner type: {learner_type}
Difficulty: {difficulty}
Estimated minutes: {estimated_minutes}

Use only the notes below.

NOTES:
{safe_text}

Return one JSON object using the correct schema for the mode.

If mode == "summary":
{{
  "result": "A concise, accurate summary grounded in the notes."
}}

If mode == "simplified":
{{
  "result": "A simpler explanation grounded in the notes and adapted to the learner type."
}}

If mode == "key_terms":
{{
  "result": "Key terms extracted successfully.",
  "key_terms": [
    {{"term": "...", "definition": "..."}}
  ]
}}

If mode == "flashcards":
{{
  "result": "Flashcards generated successfully.",
  "flashcards": [
    {{"question": "...", "answer": "..."}}
  ]
}}

If mode == "quiz":
{{
  "result": "Quiz generated successfully.",
  "quiz": [
    {{
      "question": "...",
      "options": ["...", "...", "...", "..."],
      "answer": "..."
    }}
  ]
}}

If mode == "study_guide":
{{
  "result": "Study guide generated successfully.",
  "study_guide": [
    {{
      "heading": "...",
      "bullets": ["...", "..."]
    }}
  ]
}}

If mode == "session":
{{
  "result": "Study session generated successfully.",
  "session": {{
    "title": "...",
    "learner_type": "{learner_type}",
    "difficulty": "{difficulty}",
    "estimated_minutes": {estimated_minutes},
    "overview": "...",
    "blocks": [
      {{
        "block_type": "overview",
        "title": "...",
        "content": ["...", "..."]
      }}
    ],
    "flashcards": [
      {{"question": "...", "answer": "..."}}
    ],
    "quiz": [
      {{
        "question": "...",
        "options": ["...", "...", "...", "..."],
        "answer": "..."
      }}
    ]
  }}
}}

Rules:
- Use only information from the notes.
- Prefer specific concepts over generic words.
- For flashcards, avoid vague questions.
- For quiz answers, the correct answer must exactly match one option.
- Keep session content compact and useful.
- Summary and simplified must never return an empty result.
"""

    try:
        data = _call_ollama(system_prompt, user_prompt)

        if not isinstance(data, dict):
            return None

        if mode in {"summary", "simplified"}:
            result = data.get("result")
            if not isinstance(result, str) or not result.strip():
                return None

        return data
    except Exception as e:
        print(f"[SMART_GENERATE_ERROR] {type(e).__name__}: {e}")
        return None