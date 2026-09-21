import json
import os
import re

import requests
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openrouter/free"

ALLOWED_CATEGORIES = {
    "water",
    "energy",
    "waste",
    "food",
    "paper",
    "e_waste",
    "other",
}

ALLOWED_SEVERITIES = {
    "low",
    "medium",
    "high",
    "critical",
}


def _extract_json(text) -> dict:
    """Safely extract a JSON object from model output."""

    if not isinstance(text, str) or not text.strip():
        raise ValueError("Model returned empty or null content")

    text = text.strip()

    # Direct JSON
    try:
        value = json.loads(text)
        if isinstance(value, dict):
            return value
    except json.JSONDecodeError:
        pass

    # JSON inside markdown code fences
    fenced = re.search(
        r"```(?:json)?\s*(\{.*?\})\s*```",
        text,
        re.DOTALL | re.IGNORECASE,
    )

    if fenced:
        try:
            value = json.loads(fenced.group(1))
            if isinstance(value, dict):
                return value
        except json.JSONDecodeError:
            pass

    # First JSON object found in the response
    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end > start:
        try:
            value = json.loads(text[start : end + 1])
            if isinstance(value, dict):
                return value
        except json.JSONDecodeError:
            pass

    raise ValueError("Failed to parse a valid JSON object from LLM response")


def _fallback_classification(description: str, reason: str) -> dict:
    """
    Deterministic local fallback.

    Used whenever the external AI provider is unavailable or returns
    unusable output. This keeps issue reporting operational.
    """

    text = (description or "").lower()

    keyword_groups = {
        "water": [
            "leak",
            "leaking",
            "leakage",
            "tap",
            "faucet",
            "pipe",
            "water",
            "overflow",
            "drip",
            "dripping",
        ],
        "energy": [
            "light",
            "lights",
            "fan",
            "electricity",
            "power",
            "ac",
            "air conditioner",
            "switch",
            "socket",
            "wire",
            "electrical",
            "short circuit",
            "spark",
            "sparks",
        ],
        "waste": [
            "bin",
            "garbage",
            "trash",
            "waste",
            "recycle",
            "recycling",
            "plastic",
            "segregation",
        ],
        "food": [
            "food",
            "mess",
            "leftover",
            "meal",
            "canteen",
            "kitchen",
        ],
        "paper": [
            "paper",
            "printing",
            "print",
            "document",
        ],
        "e_waste": [
            "e-waste",
            "ewaste",
            "electronic waste",
            "computer",
            "laptop",
            "charger",
            "battery",
            "monitor",
            "keyboard",
        ],
    }

    scores = {
        category: sum(1 for keyword in keywords if keyword in text)
        for category, keywords in keyword_groups.items()
    }

    category = max(scores, key=scores.get)

    if scores[category] == 0:
        category = "other"

    critical_terms = [
        "short circuit",
        "sparks",
        "spark",
        "electric shock",
        "exposed wire",
        "live wire",
        "fire",
        "smoke",
        "gas leak",
        "chemical spill",
        "water near electrical",
        "water near socket",
        "water near wiring",
    ]

    high_terms = [
        "overflowing",
        "major leak",
        "flooding",
        "broken pipe",
        "power failure",
    ]

    if any(term in text for term in critical_terms):
        severity = "critical"
    elif any(term in text for term in high_terms):
        severity = "high"
    elif category != "other":
        severity = "medium"
    else:
        severity = "low"

    return {
        "category": category,
        "severity": severity,
        "issue_type": "Fallback classification",
        "confidence": 0.5 if category != "other" else 0.2,
        "reason": reason,
        "ai_used": False,
        "fallback_used": True,
    }


def classify_issue(
    description: str,
    location: str | None = None,
) -> dict:

    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        return _fallback_classification(
            description,
            "AI provider is not configured; local classification was used.",
        )

    prompt = f"""Classify this campus issue and return ONLY valid JSON.

Description: {description.strip()}
Location: {location or "Not provided"}

Use exactly:
{{"category":"water|energy|waste|food|paper|e_waste|other",
"severity":"low|medium|high|critical",
"issue_type":"short label",
"confidence":0.0,
"reason":"short reason"}}

Do not give advice, safety instructions, policies, or priority decisions.
"""

    try:
        response = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                "temperature": 0,
                "max_tokens": 180,
            },
            timeout=(5, 20),
        )

    except requests.Timeout:
        return _fallback_classification(
            description,
            "OpenRouter timed out; local classification was used.",
        )

    except requests.RequestException as exc:
        return _fallback_classification(
            description,
            f"OpenRouter was unavailable; local classification was used. "
            f"Provider error: {str(exc)[:200]}",
        )

    # Non-success provider response
    if response.status_code != 200:
        return _fallback_classification(
            description,
            "OpenRouter returned an error; local classification was used.",
        )

    # Parse provider response
    try:
        data = response.json()

        choices = data.get("choices") or []

        if not choices:
            return _fallback_classification(
                description,
                "OpenRouter returned no model choices; local classification was used.",
            )

        message = choices[0].get("message") or {}
        raw_content = message.get("content")

    except (ValueError, TypeError, AttributeError):
        return _fallback_classification(
            description,
            "OpenRouter returned an unreadable response; local classification was used.",
        )

    # Critical fix:
    # Some OpenRouter/free responses can contain content=None.
    if not isinstance(raw_content, str) or not raw_content.strip():
        return _fallback_classification(
            description,
            "OpenRouter returned empty model content; local classification was used.",
        )

    # Extract JSON
    try:
        result = _extract_json(raw_content)

    except ValueError:
        return _fallback_classification(
            description,
            "The model returned malformed output; local classification was used.",
        )

    # Validate model output
    category = result.get("category")
    severity = result.get("severity")
    issue_type = result.get("issue_type")
    confidence = result.get("confidence")
    reason = result.get("reason")

    if category not in ALLOWED_CATEGORIES:
        category = "other"

    if severity not in ALLOWED_SEVERITIES:
        severity = "medium"

    if not isinstance(issue_type, str) or not issue_type.strip():
        issue_type = "Unclassified campus issue"

    if not isinstance(confidence, (int, float)):
        confidence = 0.0

    confidence = max(0.0, min(1.0, float(confidence)))

    if not isinstance(reason, str) or not reason.strip():
        reason = "The issue was classified from the submitted description."

    return {
        "category": category,
        "severity": severity,
        "issue_type": issue_type.strip(),
        "confidence": confidence,
        "reason": reason.strip(),
        "ai_used": True,
        "fallback_used": False,
    }