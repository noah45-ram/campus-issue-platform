import datetime

ALLOWED_STATUSES = {"open", "in_progress", "resolved"}

# In-memory store: {issue_id: issue_dict}
_ISSUES: dict[str, dict] = {}
_ISSUE_COUNTER: int = 0


def create_issue(issue_data: dict) -> dict:
    """
    Create a new issue with a generated sequential ID (e.g. ISSUE-0001)
    and store it in memory.
    """
    global _ISSUE_COUNTER
    _ISSUE_COUNTER += 1
    issue_id = f"ISSUE-{_ISSUE_COUNTER:04d}"

    created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

    new_issue = {
        "id": issue_id,
        "description": issue_data.get("description", ""),
        "location": issue_data.get("location", ""),
        "category": issue_data.get("category", "other"),
        "severity": issue_data.get("severity", "low"),
        "safety": issue_data.get("safety", {}),
        "priority": issue_data.get("priority", {}),
        "duplicate": issue_data.get("duplicate", {}),
        "status": "open",
        "created_at": created_at,
        "report_count": issue_data.get("report_count", 1),
        "evidence": issue_data.get("evidence"),
    }

    _ISSUES[issue_id] = new_issue
    return new_issue


def get_issue(issue_id: str) -> dict | None:
    """Retrieve an issue by ID from memory."""
    return _ISSUES.get(issue_id)


def list_issues() -> list[dict]:
    """Return all issues currently in memory, including resolved ones."""
    return list(_ISSUES.values())


def increment_report_count(issue_id: str) -> dict | None:
    """
    Increment the number of reports linked to an existing active issue.

    The issue remains a single ticket; only its report count increases.
    """
    issue = _ISSUES.get(issue_id)

    if not issue:
        return None

    issue["report_count"] = int(issue.get("report_count", 1)) + 1

    return issue


def update_issue_status(issue_id: str, status: str) -> dict | None:
    """
    Update the operational status of an existing issue.

    Allowed statuses:
    - open
    - in_progress
    - resolved

    Resolved issues remain in the historical record.
    """
    norm_status = (status or "").strip().lower()

    if norm_status not in ALLOWED_STATUSES:
        raise ValueError(
            f"Invalid status '{status}'. Allowed: {sorted(ALLOWED_STATUSES)}"
        )

    issue = _ISSUES.get(issue_id)

    if not issue:
        return None

    issue["status"] = norm_status

    if norm_status == "resolved":
        issue["resolved_at"] = (
            datetime.datetime.now(datetime.timezone.utc).isoformat()
        )

    return issue


def clear_issues() -> None:
    """Helper for testing: reset the in-memory store."""
    global _ISSUE_COUNTER

    _ISSUES.clear()
    _ISSUE_COUNTER = 0