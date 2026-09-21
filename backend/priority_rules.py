def calculate_priority(
    safety_assessment: dict,
    severity: str,
    report_count: int = 1,
    recurrence: bool = False,
    affected_area: str = "local",
) -> dict:
    """
    Deterministically calculate operational issue priority.

    1. If safety_assessment["priority_override"] == "critical",
       priority is forced to "critical" (safety override).
    2. Otherwise, a transparent multi-factor score is computed:
       - base severity: low (10), medium (25), high (45), critical (70)
       - report volume: +10 for 2-3 reports, +20 for 4+ reports
       - recurrence: +15 if recurring issue
       - affected area: local (+0), building (+10), campus (+20)

    Score mapping:
       0 - 19: low
       20 - 39: medium
       40 - 69: high
       70+: critical
    """
    # 1. Rule-based critical safety override
    if safety_assessment and safety_assessment.get("priority_override") == "critical":
        return {
            "priority": "critical",
            "score": 100,
            "reason": f"Critical safety override triggered ({safety_assessment.get('reason', 'safety risk')})",
        }

    # 2. Base severity score
    sev = (severity or "low").strip().lower()
    severity_scores = {
        "low": 10,
        "medium": 25,
        "high": 45,
        "critical": 70,
    }
    score = severity_scores.get(sev, 25)
    reasons = [f"Base severity '{sev}' (+{score})"]

    # 3. Report count adjustments
    count = max(1, int(report_count or 1))
    if count >= 4:
        score += 20
        reasons.append(f"High report volume ({count} reports, +20)")
    elif count >= 2:
        score += 10
        reasons.append(f"Multiple reports ({count} reports, +10)")

    # 4. Recurrence adjustment
    if recurrence:
        score += 15
        reasons.append("Recurring issue detected (+15)")

    # 5. Affected area adjustment
    area = (affected_area or "local").strip().lower()
    if area == "campus":
        score += 20
        reasons.append("Campus-wide impact (+20)")
    elif area == "building":
        score += 10
        reasons.append("Building-wide impact (+10)")
    else:
        # "local" adds 0
        reasons.append("Local impact (+0)")

    # 6. Map final score to priority band
    if score >= 70:
        priority = "critical"
    elif score >= 40:
        priority = "high"
    elif score >= 20:
        priority = "medium"
    else:
        priority = "low"

    return {
        "priority": priority,
        "score": score,
        "reason": "; ".join(reasons),
    }
