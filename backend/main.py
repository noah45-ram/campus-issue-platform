import os
import requests
from pathlib import Path
from uuid import uuid4

from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv(find_dotenv())

from ai_service import classify_issue
from duplicate_detection import find_duplicate_candidate
from issue_store import (
    create_issue,
    get_issue,
    list_issues,
    update_issue,
    update_issue_status,
    increment_report_count,
    init_db,
)
from knowledge_base import search_knowledge
from priority_rules import calculate_priority
from safety_rules import assess_safety


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="GreenCampus Sentinel API",
    description="AI-assisted campus sustainability issue reporting platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize PostgreSQL tables.
init_db()


# ============================================================
# PHOTO EVIDENCE CONFIGURATION
# ============================================================

if os.getenv("VERCEL"):
    UPLOAD_DIR = Path("/tmp/snapact_uploads")
else:
    UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB


def save_evidence_image(upload: UploadFile | None):
    """
    Save an optional uploaded image as supporting evidence.

    The image is NOT sent to the AI model.
    It is only stored for human maintenance/admin review.
    """

    if upload is None:
        return None

    if upload.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only JPG, PNG, and WEBP images are allowed.",
        )

    data = upload.file.read()

    if len(data) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Image must be 5 MB or smaller.",
        )

    extension = ALLOWED_IMAGE_TYPES[upload.content_type]

    # Never trust the original filename.
    filename = f"{uuid4().hex}{extension}"
    destination = UPLOAD_DIR / filename

    destination.write_bytes(data)

    return {
        "filename": filename,
        "url": f"/evidence/{filename}",
    }


# ============================================================
# DEMO SEEDED ISSUES
# ============================================================

DEMO_SEEDED_ISSUES = [
    {
        "description": "Tap leaking continuously in H4 hostel washroom",
        "location": "H4 Hostel - Ground Floor",
        "category": "water",
        "severity": "medium",
        "safety": {
            "is_safety_critical": False,
            "safety_level": "caution",
            "priority_override": "normal",
            "alert_type": "quick_action",
            "message": (
                "If safe, place a container underneath to reduce water "
                "wastage until maintenance arrives."
            ),
            "reason": "Water-related issue detected",
        },
        "priority": {
            "priority": "medium",
            "score": 25,
            "reason": "Medium severity water issue",
        },
        "duplicate": {
            "is_duplicate": False,
            "duplicate_issue_id": None,
            "confidence": 0.0,
            "reason": "Initial demo issue",
        },
        "report_count": 1,
        "evidence": None,
    },
    {
        "description": "Tap leaking near H5 washroom",
        "location": "H5 Hostel - Ground Floor",
        "category": "water",
        "severity": "medium",
        "safety": {
            "is_safety_critical": False,
            "safety_level": "caution",
            "priority_override": "normal",
            "alert_type": "quick_action",
            "message": (
                "If safe, place a container underneath to reduce water "
                "wastage until maintenance arrives."
            ),
            "reason": "Water-related issue detected",
        },
        "priority": {
            "priority": "medium",
            "score": 25,
            "reason": "Medium severity water issue",
        },
        "duplicate": {
            "is_duplicate": False,
            "duplicate_issue_id": None,
            "confidence": 0.0,
            "reason": "Initial demo issue",
        },
        "report_count": 1,
        "evidence": None,
    },
    {
        "description": "Tap leakage in H4 washroom",
        "location": "H4 Hostel - Ground Floor",
        "category": "water",
        "severity": "medium",
        "safety": {
            "is_safety_critical": False,
            "safety_level": "caution",
            "priority_override": "normal",
            "alert_type": "quick_action",
            "message": (
                "If safe, place a container underneath to reduce water "
                "wastage until maintenance arrives."
            ),
            "reason": "Water-related issue detected",
        },
        "priority": {
            "priority": "medium",
            "score": 25,
            "reason": "Medium severity water issue",
        },
        "duplicate": {
            "is_duplicate": False,
            "duplicate_issue_id": None,
            "confidence": 0.0,
            "reason": "Historical demo issue",
        },
        "report_count": 1,
        "evidence": None,
    },
]


def _init_demo_store():
    if not list_issues():
        h4 = create_issue(DEMO_SEEDED_ISSUES[0])
        h5 = create_issue(DEMO_SEEDED_ISSUES[1])
        h4_old = create_issue(DEMO_SEEDED_ISSUES[2])

        update_issue_status(h4_old["id"], "resolved")


# Demo data is only inserted when explicitly enabled.
if os.getenv("SEED_DEMO_DATA", "false").lower() == "true":
    _init_demo_store()


# ============================================================
# REQUEST MODELS
# ============================================================

class IssueAnalyzeRequest(BaseModel):
    description: str
    location: str | None = None
    report_count: int = 1
    recurrence: bool = False
    affected_area: str = "local"


class IssueCreateRequest(BaseModel):
    """
    Kept for compatibility with the existing project structure.

    The actual POST /issues endpoint uses multipart/form-data
    so that it can receive an optional image.
    """

    description: str
    location: str | None = None
    report_count: int = 1
    recurrence: bool = False
    affected_area: str = "local"


class IssueStatusUpdateRequest(BaseModel):
    status: str


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "GreenCampus Sentinel API",
    }


# ============================================================
# AI CONNECTION TEST
# ============================================================

@app.get("/ai/test")
def test_ai():
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="OPENROUTER_API_KEY is not configured",
        )

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "openrouter/free",
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Reply with exactly one short sentence confirming "
                        "that the GreenCampus Sentinel AI connection works."
                    ),
                }
            ],
        },
        timeout=60,
    )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail={
                "message": "OpenRouter request failed",
                "openrouter_error": response.text[:1000],
            },
        )

    data = response.json()

    return {
        "status": "ok",
        "model": "openrouter/free",
        "response": data["choices"][0]["message"]["content"],
    }


# ============================================================
# ISSUE ANALYSIS
# ============================================================

@app.post("/issues/analyze")
def analyze_issue(payload: IssueAnalyzeRequest):
    if not payload.description.strip():
        raise HTTPException(
            status_code=400,
            detail="Description cannot be empty",
        )

    # 1. AI classification
    classification = classify_issue(
        description=payload.description,
        location=payload.location,
    )

    # 2. Deterministic safety assessment
    safety = assess_safety(
        description=payload.description,
        category=classification.get("category", ""),
        severity=classification.get("severity", ""),
    )

    # 3. Deterministic priority calculation
    priority = calculate_priority(
        safety_assessment=safety,
        severity=classification.get("severity", "low"),
        report_count=payload.report_count,
        recurrence=payload.recurrence,
        affected_area=payload.affected_area,
    )

    # 4. Deterministic duplicate candidate check
    duplicate = find_duplicate_candidate(
        description=payload.description,
        location=payload.location or "",
        category=classification.get("category", ""),
        existing_issues=list_issues(),
    )

    return {
        "status": "ok",
        "classification": classification,
        "safety": safety,
        "priority": priority,
        "duplicate": duplicate,
    }


# ============================================================
# CREATE ISSUE WITH OPTIONAL PHOTO EVIDENCE
# ============================================================

@app.post("/issues")
def report_issue(
    description: str = Form(""),
    location: str | None = Form(None),
    recurrence: bool = Form(False),
    affected_area: str = Form("local"),
    image: UploadFile | None = File(None),
):
    """
    Create a new campus issue or link a report to an existing active issue.

    Report count is application-managed. Users cannot manually set it.

    Images are evidence only. They are stored for human maintenance/admin
    review and are never sent to the AI model.
    """

    clean_description = (description or "").strip()

    if not clean_description and image is None:
        raise HTTPException(
            status_code=400,
            detail="Provide a short description or upload a photo.",
        )

    # --------------------------------------------------------
    # 1. PHOTO EVIDENCE
    # --------------------------------------------------------

    evidence = save_evidence_image(image)

    # --------------------------------------------------------
    # 2. AI CLASSIFICATION
    # --------------------------------------------------------

    manual_review_required = False

    if clean_description:
        classification = classify_issue(
            description=clean_description,
            location=location,
        )
    else:
        manual_review_required = True

        classification = {
            "category": "other",
            "severity": "low",
            "issue_type": "manual_review",
            "confidence": 0.0,
            "reason": (
                "No textual description was provided. The uploaded image "
                "is stored as evidence but is not analyzed by AI."
            ),
        }

    # --------------------------------------------------------
    # 3. DETERMINISTIC SAFETY ASSESSMENT
    # --------------------------------------------------------

    safety = assess_safety(
        description=clean_description,
        category=classification.get("category", ""),
        severity=classification.get("severity", ""),
    )

    # --------------------------------------------------------
    # 4. DETERMINISTIC DUPLICATE DETECTION
    # --------------------------------------------------------

    current_issues = list_issues()

    duplicate = find_duplicate_candidate(
        description=clean_description,
        location=location or "",
        category=classification.get("category", ""),
        existing_issues=current_issues,
    )

    # --------------------------------------------------------
    # 5. LOCAL KNOWLEDGE SEARCH
    # --------------------------------------------------------

    try:
        knowledge = (
            search_knowledge(
                query=clean_description,
                category=classification.get("category"),
            )
            if clean_description
            else []
        )
    except Exception:
        knowledge = []

    if knowledge:
        guidance_note = (
            "Relevant guidance retrieved from GreenCampus Sentinel Demo "
            "Knowledge Base (for reference only; does not replace official "
            "campus policy)."
        )
    else:
        guidance_note = (
            "Only general guidance is available; no relevant entry was "
            "found in the demo knowledge base."
        )

    # --------------------------------------------------------
    # 6. DUPLICATE HANDLING
    # --------------------------------------------------------

    if duplicate.get("is_duplicate"):
        dup_id = duplicate.get("duplicate_issue_id")
        existing_issue = get_issue(dup_id) if dup_id else None

        if existing_issue is None:
            duplicate["is_duplicate"] = False
            duplicate["reason"] = "Duplicate candidate no longer exists."

        else:
            # Increment persistent report count.
            updated_issue = increment_report_count(dup_id)

            # Preserve evidence from every linked report.
            if evidence:
                existing_evidence = existing_issue.get("evidence")

                if not isinstance(existing_evidence, list):
                    existing_evidence = (
                        [existing_evidence]
                        if existing_evidence
                        else []
                    )

                existing_evidence.append(evidence)
                existing_issue["evidence"] = existing_evidence

            # A later report can reveal a more serious condition.
            severity_rank = {
                "low": 1,
                "medium": 2,
                "high": 3,
                "critical": 4,
            }

            existing_severity = existing_issue.get("severity", "low")
            new_severity = classification.get("severity", "low")

            if severity_rank.get(new_severity, 1) > severity_rank.get(
                existing_severity, 1
            ):
                existing_issue["severity"] = new_severity

            # A critical safety report can upgrade the existing issue.
            if safety.get("is_safety_critical"):
                existing_issue["safety"] = safety

            merged_safety = existing_issue.get("safety", safety)

            # Recalculate operational priority.
            updated_priority = calculate_priority(
                safety_assessment=merged_safety,
                severity=existing_issue.get("severity", "low"),
                report_count=updated_issue.get("report_count", 1),
                recurrence=recurrence,
                affected_area=affected_area,
            )

            existing_issue["priority"] = updated_priority
            existing_issue["duplicate"] = duplicate

            # Persist all changed fields.
            persisted_issue = update_issue(
                dup_id,
                {
                    "severity": existing_issue.get("severity", "low"),
                    "safety": existing_issue.get("safety", {}),
                    "priority": updated_priority,
                    "duplicate": duplicate,
                    "evidence": existing_issue.get("evidence"),
                },
            )

            if persisted_issue:
                existing_issue = persisted_issue

            msg = (
                f"Report linked to existing active issue {dup_id}. "
                f"Report count is now "
                f"{existing_issue.get('report_count', 1)}. "
                f"{safety.get('message', '')} {guidance_note}"
            ).strip()

            return {
                "status": "ok",
                "action": "linked_to_existing",
                "issue": existing_issue,
                "duplicate": duplicate,
                "safety": safety,
                "knowledge": knowledge,
                "evidence": evidence,
                "manual_review_required": manual_review_required,
                "message": msg,
            }

    # --------------------------------------------------------
    # 7. CREATE NEW ISSUE
    # --------------------------------------------------------

    priority = calculate_priority(
        safety_assessment=safety,
        severity=classification.get("severity", "low"),
        report_count=1,
        recurrence=recurrence,
        affected_area=affected_area,
    )

    new_issue_data = {
        "description": clean_description,
        "location": location or "",
        "category": classification.get("category", "other"),
        "issue_type": classification.get("issue_type"),
        "severity": classification.get("severity", "low"),
        "safety": safety,
        "priority": priority,
        "duplicate": duplicate,
        "report_count": 1,
        "evidence": [evidence] if evidence else [],
        "manual_review_required": manual_review_required,
        "recurrence": recurrence,
        "affected_area": affected_area,
    }

    created = create_issue(new_issue_data)

    msg = (
        f"Issue {created['id']} reported successfully. "
        f"{safety.get('message', '')} {guidance_note}"
    ).strip()

    return {
        "status": "ok",
        "action": "created",
        "issue": created,
        "knowledge": knowledge,
        "manual_review_required": manual_review_required,
        "message": msg,
    }


# ============================================================
# SERVE PHOTO EVIDENCE
# ============================================================

@app.get("/evidence/{filename}")
def get_evidence(filename: str):
    """
    Serve an uploaded evidence image.

    Only files from the dedicated uploads directory can be served.
    """

    safe_name = Path(filename).name
    file_path = UPLOAD_DIR / safe_name

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Evidence image not found",
        )

    return FileResponse(file_path)


# ============================================================
# LIST ISSUES
# ============================================================

@app.get("/issues")
def get_issues():
    return {
        "status": "ok",
        "issues": list_issues(),
    }


# ============================================================
# GET SINGLE ISSUE
# ============================================================

@app.get("/issues/{issue_id}")
def get_single_issue(issue_id: str):
    issue = get_issue(issue_id)

    if not issue:
        raise HTTPException(
            status_code=404,
            detail=f"Issue '{issue_id}' not found",
        )

    return {
        "status": "ok",
        "issue": issue,
    }


# ============================================================
# UPDATE ISSUE STATUS
# ============================================================

@app.patch("/issues/{issue_id}/status")
def patch_issue_status(
    issue_id: str,
    payload: IssueStatusUpdateRequest,
):
    allowed = {
        "open",
        "in_progress",
        "resolved",
    }

    status_norm = (payload.status or "").strip().lower()

    if status_norm not in allowed:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid status '{payload.status}'. "
                f"Allowed statuses: {sorted(allowed)}"
            ),
        )

    updated = update_issue_status(
        issue_id,
        status_norm,
    )

    if not updated:
        raise HTTPException(
            status_code=404,
            detail=f"Issue '{issue_id}' not found",
        )

    return {
        "status": "ok",
        "issue": updated,
    }