import datetime
import os

from dotenv import find_dotenv, load_dotenv
import psycopg
from psycopg.rows import dict_row

load_dotenv(find_dotenv())

ALLOWED_STATUSES = {"open", "in_progress", "resolved"}


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")

    return database_url


def get_connection():
    return psycopg.connect(
        get_database_url(),
        row_factory=dict_row,
    )


def init_db():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS issues (
                    id TEXT PRIMARY KEY,
                    description TEXT NOT NULL DEFAULT '',
                    location TEXT NOT NULL DEFAULT '',
                    category TEXT NOT NULL DEFAULT 'other',
                    issue_type TEXT,
                    severity TEXT NOT NULL DEFAULT 'low',

                    safety JSONB NOT NULL DEFAULT '{}'::jsonb,
                    priority JSONB NOT NULL DEFAULT '{}'::jsonb,
                    duplicate JSONB NOT NULL DEFAULT '{}'::jsonb,

                    status TEXT NOT NULL DEFAULT 'open',
                    created_at TIMESTAMPTZ NOT NULL,
                    resolved_at TIMESTAMPTZ,

                    report_count INTEGER NOT NULL DEFAULT 1,
                    evidence JSONB,

                    recurrence BOOLEAN NOT NULL DEFAULT FALSE,
                    affected_area TEXT NOT NULL DEFAULT 'local'
                )
                """
            )

            cur.execute(
                """
                CREATE SEQUENCE IF NOT EXISTS issue_number_seq
                """
            )

            cur.execute(
                """
                SELECT COALESCE(
                    MAX(
                        CAST(
                            SUBSTRING(id FROM '[0-9]+$')
                            AS INTEGER
                        )
                    ),
                    0
                ) AS max_number
                FROM issues
                """
            )

            max_number = cur.fetchone()["max_number"]

            if max_number > 0:
                cur.execute(
                    """
                    SELECT setval(
                        'issue_number_seq',
                        %s,
                        true
                    )
                    """,
                    (max_number,),
                )
            else:
                cur.execute(
                    """
                    SELECT setval(
                        'issue_number_seq',
                        1,
                        false
                    )
                    """
                )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_issues_status
                ON issues(status)
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_issues_location
                ON issues(location)
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_issues_category
                ON issues(category)
                """
            )

        conn.commit()

def create_issue(issue_data: dict) -> dict:
    issue_number = get_next_issue_number()
    issue_id = f"ISSUE-{issue_number:04d}"

    created_at = datetime.datetime.now(datetime.timezone.utc)

    issue = {
        "id": issue_id,
        "description": issue_data.get("description", ""),
        "location": issue_data.get("location", ""),
        "category": issue_data.get("category", "other"),
        "issue_type": issue_data.get("issue_type"),
        "severity": issue_data.get("severity", "low"),
        "safety": issue_data.get("safety", {}),
        "priority": issue_data.get("priority", {}),
        "duplicate": issue_data.get("duplicate", {}),
        "status": "open",
        "created_at": created_at,
        "resolved_at": None,
        "report_count": issue_data.get("report_count", 1),
        "evidence": issue_data.get("evidence"),
        "recurrence": issue_data.get("recurrence", False),
        "affected_area": issue_data.get("affected_area", "local"),
    }

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO issues (
                    id,
                    description,
                    location,
                    category,
                    issue_type,
                    severity,
                    safety,
                    priority,
                    duplicate,
                    status,
                    created_at,
                    resolved_at,
                    report_count,
                    evidence,
                    recurrence,
                    affected_area
                )
                VALUES (
                    %(id)s,
                    %(description)s,
                    %(location)s,
                    %(category)s,
                    %(issue_type)s,
                    %(severity)s,
                    %(safety)s,
                    %(priority)s,
                    %(duplicate)s,
                    %(status)s,
                    %(created_at)s,
                    %(resolved_at)s,
                    %(report_count)s,
                    %(evidence)s,
                    %(recurrence)s,
                    %(affected_area)s
                )
                """,
                {
                    **issue,
                    "safety": psycopg.types.json.Jsonb(issue["safety"]),
                    "priority": psycopg.types.json.Jsonb(issue["priority"]),
                    "duplicate": psycopg.types.json.Jsonb(issue["duplicate"]),
                    "evidence": (
                        psycopg.types.json.Jsonb(issue["evidence"])
                        if issue["evidence"] is not None
                        else None
                    ),
                },
            )

        conn.commit()

    return serialize_issue(issue)


def get_issue(issue_id: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM issues
                WHERE id = %s
                """,
                (issue_id,),
            )

            issue = cur.fetchone()

    return serialize_issue(issue) if issue else None


def list_issues():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM issues
                ORDER BY created_at DESC
                """
            )

            issues = cur.fetchall()

    return [serialize_issue(issue) for issue in issues]


def increment_report_count(issue_id: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE issues
                SET report_count = report_count + 1
                WHERE id = %s
                RETURNING *
                """,
                (issue_id,),
            )

            issue = cur.fetchone()

        conn.commit()

    return serialize_issue(issue) if issue else None

def update_issue(issue_id: str, updates: dict):
    allowed_fields = {
        "description",
        "location",
        "category",
        "issue_type",
        "severity",
        "safety",
        "priority",
        "duplicate",
        "report_count",
        "evidence",
        "recurrence",
        "affected_area",
    }

    clean_updates = {
        key: value
        for key, value in updates.items()
        if key in allowed_fields
    }

    if not clean_updates:
        return get_issue(issue_id)

    json_fields = {
        "safety",
        "priority",
        "duplicate",
        "evidence",
    }

    assignments = []
    values = []

    for key, value in clean_updates.items():
        assignments.append(f"{key} = %s")

        if key in json_fields:
            value = (
                psycopg.types.json.Jsonb(value)
                if value is not None
                else None
            )

        values.append(value)

    values.append(issue_id)

    query = f"""
        UPDATE issues
        SET {", ".join(assignments)}
        WHERE id = %s
        RETURNING *
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, values)
            issue = cur.fetchone()

        conn.commit()

    return serialize_issue(issue) if issue else None

def update_issue_status(issue_id: str, status: str):
    norm_status = (status or "").strip().lower()

    if norm_status not in ALLOWED_STATUSES:
        raise ValueError(
            f"Invalid status. Allowed values: {sorted(ALLOWED_STATUSES)}"
        )

    resolved_at = (
        datetime.datetime.now(datetime.timezone.utc)
        if norm_status == "resolved"
        else None
    )

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE issues
                SET
                    status = %s,
                    resolved_at = %s
                WHERE id = %s
                RETURNING *
                """,
                (norm_status, resolved_at, issue_id),
            )

            issue = cur.fetchone()

        conn.commit()

    return serialize_issue(issue) if issue else None


def get_next_issue_number() -> int:
    """
    Generates the next numeric issue ID.

    PostgreSQL stores the current maximum ID, so numbering survives
    FastAPI restarts.
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COALESCE(
                    MAX(
                        CAST(
                            SUBSTRING(id FROM '[0-9]+$')
                            AS INTEGER
                        )
                    ),
                    0
                ) + 1 AS next_number
                FROM issues
                """
            )

            result = cur.fetchone()

    return int(result["next_number"])


def serialize_issue(issue):
    if not issue:
        return None

    serialized = dict(issue)

    created_at = serialized.get("created_at")
    resolved_at = serialized.get("resolved_at")

    if isinstance(created_at, datetime.datetime):
        serialized["created_at"] = created_at.isoformat()

    if isinstance(resolved_at, datetime.datetime):
        serialized["resolved_at"] = resolved_at.isoformat()

    return serialized


def clear_issues():
    """
    Development/testing helper.
    Removes all issues from the database.
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM issues")

        conn.commit()