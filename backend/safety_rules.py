import re


def assess_safety(
    description: str,
    category: str,
    severity: str,
) -> dict:
    """
    Deterministic safety guardrail operating after AI classification.

    Enforces rule-based safety levels, priority overrides, and user-facing messages
    without relying on LLM decisions or LLM confidence scores.
    """
    text = (description or "").lower()
    cat = (category or "").lower().strip()
    sev = (severity or "").lower().strip()

    # Critical patterns: immediate danger / safety hazards
    critical_patterns = [
        (r"\bshort\s*circuit\b", "Detected suspected short circuit"),
        (r"\bspark(s|ing)?\b", "Detected electrical sparks"),
        (r"\b(exposed|naked|open)\s+(live\s+)?wire(s)?\b", "Detected exposed live wire"),
        (r"\blive\s+wire(s)?\b", "Detected live wire"),
        (r"\belectric(al)?\s+shock(s)?\b", "Detected risk or occurrence of electric shock"),
        (r"\bfire\b", "Detected fire hazard"),
        (r"\bsmoke\b", "Detected smoke hazard"),
        (r"\bgas\s*leak\b", "Detected gas leak"),
        (r"\bchemical\s*spill\b", "Detected chemical spill"),
        (
            r"\b(flood(ing)?|water)\b.*\b(electr(ic|ical)|switch|socket|plug|wire)\b",
            "Detected water accumulation near electrical installations",
        ),
        (
            r"\b(electr(ic|ical)|switch|socket|plug|wire)\b.*\b(flood(ing)?|water)\b",
            "Detected water accumulation near electrical installations",
        ),
    ]

    for pattern, reason in critical_patterns:
        if re.search(pattern, text):
            return {
                "is_safety_critical": True,
                "safety_level": "critical",
                "priority_override": "critical",
                "alert_type": "safety_alert",
                "message": (
                    "Move away from the area immediately. Do not touch the equipment or attempt repairs. "
                    "Report this hazard to campus maintenance or emergency personnel immediately."
                ),
                "reason": reason,
            }

    # If the AI classified the issue as critical in an inherently high-risk category
    if sev == "critical" and cat in {"energy", "other"}:
        return {
            "is_safety_critical": True,
            "safety_level": "critical",
            "priority_override": "critical",
            "alert_type": "safety_alert",
            "message": (
                "Move away from the area immediately. Do not touch any affected equipment or attempt repairs. "
                "Report this critical situation to campus authorities immediately."
            ),
            "reason": f"Critical severity flagged in high-risk category '{cat}'",
        }

    # Caution patterns: ordinary sustainability / maintenance issues
    caution_patterns = [
        (
            r"\b(water\s*leak|leaking\s*tap|tap\s*leak|dripping\s*tap|dripping\s*pipe|pipe\s*leak|leaking\s*pipe|dripping)\b",
            "Water leak detected",
            (
                "If safe, place a bucket or container underneath the leak to prevent water wastage "
                "until maintenance arrives."
            ),
        ),
        (
            r"\b(overflowing\s*(bin|dustbin|trash|waste)|garbage\s*overflow)\b",
            "Overflowing bin detected",
            "Avoid adding more waste to the bin and use the nearest alternative disposal point.",
        ),
        (
            r"\b(minor\s*spill|liquid\s*spill|floor\s*wet|wet\s*floor|spilled\s*water)\b",
            "Minor spill detected",
            "Avoid the affected area to prevent slipping and inform maintenance personnel.",
        ),
        (
            r"\b(broken\s*switch|broken\s*socket|loose\s*fixture|faulty\s*light|flickering\s*light)\b",
            "Non-hazardous equipment issue detected",
            "Do not tamper with the equipment. Campus maintenance has been notified.",
        ),
    ]

    for pattern, reason, message in caution_patterns:
        if re.search(pattern, text):
            return {
                "is_safety_critical": False,
                "safety_level": "caution",
                "priority_override": "normal",
                "alert_type": "quick_action",
                "message": message,
                "reason": reason,
            }

    # Category-based caution fallback if text didn't trigger a specific pattern
    if cat == "water":
        return {
            "is_safety_critical": False,
            "safety_level": "caution",
            "alert_type": "quick_action",
            "priority_override": "normal",
            "message": "If safe, place a container underneath to reduce water wastage until maintenance arrives.",
            "reason": "Water-related issue detected",
        }

    if cat in {"waste", "food", "paper", "e_waste"}:
        return {
            "is_safety_critical": False,
            "safety_level": "caution",
            "alert_type": "quick_action",
            "priority_override": "normal",
            "message": "Avoid adding further waste and keep the area clear until staff attends to it.",
            "reason": f"Waste-related issue in category '{cat}'",
        }

    # Default: normal / no safety-related pattern detected
    return {
        "is_safety_critical": False,
        "safety_level": "normal",
        "priority_override": "normal",
        "alert_type": "none",
        "message": "",
        "reason": "No safety-related pattern detected",
    }
