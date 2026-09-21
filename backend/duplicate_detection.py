import re

# Common non-informative stop words to exclude when computing keyword overlap
STOP_WORDS = {
    "a", "an", "the", "in", "on", "at", "to", "for", "of", "and", "or", "is",
    "are", "was", "were", "it", "this", "that", "near", "from", "with", "there",
    "here", "has", "have", "had", "been", "be", "by", "some", "any", "please"
}


def _tokenize(text: str) -> set[str]:
    """Extract normalized lowercase alphanumeric tokens, filtering out stop words."""
    if not text:
        return set()
    words = re.findall(r"\b[a-z0-9]+\b", text.lower())
    return {w for w in words if w not in STOP_WORDS and len(w) > 1}


def _normalize_location(loc: str) -> str:
    """Normalize location string for comparison (strip punctuation and extra whitespace)."""
    if not loc:
        return ""
    # Standardize common location variations e.g. "H4 Hostel - Ground Floor" -> "h4 hostel ground floor"
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", "", loc.lower())).strip()


def find_duplicate_candidate(
    description: str,
    location: str,
    category: str,
    existing_issues: list[dict],
) -> dict:
    """
    Deterministically find a likely duplicate candidate among existing issues.

    HARD FILTERS (disqualify immediately if not matching):
    1. Location: must match the relevant location (different location = separate issue).
    2. Category: must be compatible (e.g. water cannot be duplicate of waste).
    3. Status: must be active/open (resolved historical issues are NEVER active duplicates).

    EVIDENCE SCORING (on surviving candidates):
    - Normalized keyword overlap (Jaccard similarity on non-stop tokens)
    - Bonus if issue_type keywords match
    """
    if not existing_issues or not location:
        return {
            "is_duplicate": False,
            "duplicate_issue_id": None,
            "confidence": 0.0,
            "reason": "No candidate issues or location provided",
        }

    norm_new_loc = _normalize_location(location)
    new_cat = (category or "").strip().lower()
    new_tokens = _tokenize(description)

    best_candidate = None
    best_score = 0.0
    best_reason = ""

    for issue in existing_issues:
        issue_id = issue.get("id", "UNKNOWN")
        issue_status = str(issue.get("status", "")).strip().lower()

        # HARD FILTER 1: Issue must be active / open
        if issue_status != "open":
            continue

        # HARD FILTER 2: Relevant location match
        issue_loc = issue.get("location", "")
        norm_issue_loc = _normalize_location(issue_loc)
        # Check if locations match or one contains the other (e.g. "H4 Hostel" & "H4 Hostel - Ground Floor")
        if norm_new_loc != norm_issue_loc and (
            norm_new_loc not in norm_issue_loc and norm_issue_loc not in norm_new_loc
        ):
            continue

        # HARD FILTER 3: Compatible category
        issue_cat = str(issue.get("category", "")).strip().lower()
        if issue_cat != new_cat and issue_cat != "other" and new_cat != "other":
            continue

        # Candidate passed all hard filters! Now evaluate deterministic evidence.
        issue_desc = issue.get("description", "")
        issue_tokens = _tokenize(issue_desc)
        issue_type_tokens = _tokenize(issue.get("issue_type", ""))

        if not new_tokens or not issue_tokens:
            continue

        # Jaccard overlap on description tokens
        intersection = new_tokens.intersection(issue_tokens)
        union = new_tokens.union(issue_tokens)
        jaccard = len(intersection) / len(union) if union else 0.0

        # Type token overlap bonus
        type_overlap = 0.0
        if issue_type_tokens and new_tokens.intersection(issue_type_tokens):
            type_overlap = 0.2

        # Combined confidence score bounded [0.0, 1.0]
        confidence = min(1.0, round(jaccard * 0.8 + type_overlap, 2))

        # We consider score >= 0.25 sufficient evidence when location, category, and status all match
        if confidence > best_score:
            best_score = confidence
            best_candidate = issue_id
            matched_words = ", ".join(sorted(intersection))
            best_reason = (
                f"Matches active issue {issue_id} at {issue_loc} with category '{issue_cat}' "
                f"and overlapping keywords: [{matched_words}]"
            )

    if best_candidate and best_score >= 0.25:
        return {
            "is_duplicate": True,
            "duplicate_issue_id": best_candidate,
            "confidence": best_score,
            "reason": best_reason,
        }

    return {
        "is_duplicate": False,
        "duplicate_issue_id": None,
        "confidence": best_score,
        "reason": "No active duplicate candidate met the matching threshold",
    }
