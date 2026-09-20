# Architecture Document

**Project:** Campus Sustainability & Issue-Response Platform
**Repository:** `campus-issue-platform`
**Status:** Pre-development — architecture planning
**Last Updated:** 2026-09-20

> This document describes the planned system architecture. Implementation details may evolve during development. All deviations from this document must be noted and justified.

---

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Client (Browser)                            │
│              Mobile-first, responsive web application               │
└────────────────────────────┬────────────────────────────────────────┘
                             │ HTTPS / REST
┌────────────────────────────▼────────────────────────────────────────┐
│                        FastAPI Backend                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  Auth / RBAC │  │  Issue API   │  │  Alert API   │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  Upload API  │  │  Analytics   │  │  Admin API   │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└─────────┬──────────────────┬──────────────────┬─────────────────────┘
          │                  │                  │
┌─────────▼──────┐  ┌────────▼───────┐  ┌──────▼──────────────────────┐
│  Primary DB    │  │   AI Layer     │  │   File Storage              │
│  PostgreSQL    │  │  (AI Service)  │  │   (local / object store)    │
│  or MongoDB    │  └────────┬───────┘  └─────────────────────────────┘
└────────────────┘           │
                    ┌────────▼───────┐
                    │   ChromaDB     │
                    │  (RAG vector   │
                    │   store)       │
                    └────────────────┘
```

---

## 2. Frontend

### 2.1 Technology
- Framework: TBD — options include plain HTML/JS with a lightweight framework (e.g., HTMX, Vue.js, or React)
- Priority constraints on framework choice:
  - Must be free/open-source
  - Must be mobile-responsive without requiring a native app
  - Must support accessible, large-control UI design
  - Must not require a paid build pipeline

> **Assumption:** The frontend framework will be decided at the start of development based on developer familiarity. The architecture is backend-first; the frontend can adapt to any REST API.

### 2.2 Key UI Views

| View | Accessible To |
|---|---|
| Home / Report Issue | All authenticated users |
| My Reports | All authenticated users |
| Active Alerts (location-filtered) | All authenticated users |
| Maintenance Queue | Maintenance staff, Admin |
| Issue Detail (staff view) | Maintenance staff, Admin |
| Admin Dashboard | Admin only |
| Login / Auth | All |

### 2.3 Principles
- Camera/photo-first reporting
- Minimal steps per workflow
- Large, clear controls
- Plain language — no technical jargon
- Strong visual hierarchy
- Works on mobile browsers without a native app install

---

## 3. FastAPI Backend

### 3.1 Structure (Planned)

```
campus-issue-platform/
├── app/
│   ├── main.py               # FastAPI app entry point
│   ├── config.py             # Environment and settings
│   ├── api/
│   │   ├── auth.py           # Auth endpoints
│   │   ├── issues.py         # Report and issue management
│   │   ├── alerts.py         # Alert management
│   │   ├── uploads.py        # File upload handling
│   │   ├── analytics.py      # Admin analytics
│   │   └── admin.py          # Admin-only operations
│   ├── models/               # Database models / schemas
│   ├── services/             # Business logic
│   │   ├── issue_service.py
│   │   ├── alert_service.py
│   │   ├── ai_service.py     # AI layer interface
│   │   └── rag_service.py    # RAG / ChromaDB interface
│   ├── core/
│   │   ├── security.py       # Auth utilities
│   │   ├── safety_rules.py   # Rule-based safety guardrails
│   │   └── priority.py       # Priority computation logic
│   └── db/
│       ├── database.py       # DB connection
│       └── migrations/       # Schema migrations
├── docs/
├── tests/
├── docker-compose.yml
├── Dockerfile
└── README.md
```

### 3.2 API Design
- RESTful endpoints
- JSON request/response bodies
- Authenticated via JWT (or session tokens) — no OAuth required for MVP
- Role-based access enforced at the route level via FastAPI dependencies

### 3.3 Key API Responsibilities

| Responsibility | Notes |
|---|---|
| Issue submission | Receive photo + text + location; trigger AI pipeline; return response |
| Duplicate check | Query open issues at same location before creating a new record |
| Alert creation/lifecycle | Create, update, and close alerts tied to issue status |
| Maintenance queue | Return prioritized issue list with computed priority score |
| Status update | Accept status changes from maintenance staff |
| Admin analytics | Aggregate queries by category, time, location, severity |
| File upload | Accept image files; store safely; pass to AI; manage retention |

---

## 4. Database

### 4.1 Primary Database

**Choice to finalize at development start:** PostgreSQL (preferred for relational integrity, reporting queries) or MongoDB (preferred for flexible document schemas).

> **Assumption:** PostgreSQL is the default preference based on the need for structured relational queries in the analytics and maintenance queue views. If document flexibility is needed for issue metadata, a hybrid approach or JSON columns in PostgreSQL will be used rather than introducing a second database unnecessarily.

### 4.2 Core Data Entities

#### Issue
| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| location_id | FK | References campus location |
| category | Enum | Classified by AI + guardrails |
| severity | Enum | Low / Medium / High / Critical |
| safety_flag | Boolean | True if rule-based safety guardrail triggered |
| status | Enum | Open / In Progress / Resolved |
| report_count | Integer | Number of reports linked to this issue |
| ai_summary | Text | Generated summary for maintenance staff |
| priority_score | Float | Computed deterministic score |
| created_at | Timestamp | |
| resolved_at | Timestamp | Nullable |
| is_active_alert | Boolean | Whether an active alert is live |

#### Report (individual submission)
| Field | Type | Notes |
|---|---|---|
| id | UUID | |
| issue_id | FK | Links to parent issue |
| user_id | FK | Reporter |
| description | Text | Raw user description |
| photo_path | String | Temporary storage path; purged after processing |
| ai_classification | JSONB | Raw AI output for audit |
| submitted_at | Timestamp | |

#### Location
| Field | Type | Notes |
|---|---|---|
| id | UUID | |
| name | String | e.g., "H4 Hostel" |
| type | Enum | Hostel / Academic / Block / Other |
| parent_id | FK | For hierarchical (block → floor → zone) |

#### Alert
| Field | Type | Notes |
|---|---|---|
| id | UUID | |
| issue_id | FK | |
| location_id | FK | |
| scope | Enum | Location-specific / Campus-wide |
| is_active | Boolean | False when resolved |
| resolved_at | Timestamp | |

#### User
| Field | Type | Notes |
|---|---|---|
| id | UUID | |
| role | Enum | Reporter / Maintenance / Admin |
| hashed_password | String | |
| location_preferences | FK Array | Selected locations for alert filtering |

### 4.3 Data Retention Policy
- Photos: Deleted from storage after AI processing is complete (unless explicitly retained for audit in flagged cases)
- Report text: Retained in anonymized form for analytics
- Resolved issues: Archived; never permanently deleted

---

## 5. AI Layer

The AI layer is a service within the FastAPI backend (`ai_service.py`) that:
- Accepts structured inputs (text, image, location, category)
- Calls an LLM (open-source / free-tier) for classification and response generation
- Returns structured outputs consumed by business logic
- Never directly sets safety-critical flags — those are validated by rule-based logic after AI output

### 5.1 LLM Options (in priority order of free/open access)
1. **Google Gemini free tier** — image + text multimodal, free API tier available
2. **Ollama (local)** — fully local, no API cost, suitable for development
3. **Other open-source models** — e.g., LLaMA via Ollama

> **Requirement:** The chosen LLM must have a free-tier or fully open-source/local option. Any switch to a paid model must be explicitly approved.

### 5.2 LangGraph Usage
LangGraph may be used where a multi-step agentic pipeline provides real value:
- Duplicate detection (compare → score → merge/create)
- RAG retrieval → response generation pipeline

LangGraph will **not** be used just for the sake of using it. Simple sequential logic in Python is preferred where LangGraph adds no meaningful benefit.

---

## 6. RAG / ChromaDB

### 6.1 Purpose
Retrieve relevant campus sustainability and safety guidance to ground AI-generated responses in authoritative campus documents.

### 6.2 Knowledge Base (Planned Sources)
- Campus sustainability policy documents
- Campus safety procedures
- Waste segregation guidelines
- Water conservation guidelines
- Energy-saving guidelines
- Electrical safety guidelines
- Any other approved campus documents

### 6.3 Architecture
```
Campus Documents (PDF / text)
  → Chunked and embedded (embedding model: free/local)
  → Stored in ChromaDB (local persistent store)
  → At query time: user report text → embedded → similarity search → top-k chunks retrieved
  → Chunks + user report → LLM → grounded response
```

### 6.4 Embedding Model
- Default: free open-source sentence embedding model (e.g., `sentence-transformers/all-MiniLM-L6-v2`)
- No paid embedding API is required

### 6.5 Attribution
- Retrieved source chunks are tagged with their source document and section
- Generated responses that use retrieved content must indicate this to the user

---

## 7. File / Image Handling

### 7.1 Upload Flow
```
User uploads photo
  → Backend receives file (multipart/form-data)
  → Validates file type (JPEG, PNG, HEIC — mobile-friendly)
  → Validates file size (limit TBD, suggest ≤ 10MB)
  → Stores temporarily in local file storage or configured object store
  → Passes image to AI service for classification
  → After classification complete: deletes file from storage
  → If audit retention required (safety-critical cases): stores in restricted audit path
```

### 7.2 Storage
- **Development:** Local filesystem
- **Production:** Object store with free tier preferred (e.g., MinIO self-hosted, or similar)
- **No mandatory paid object store** (e.g., AWS S3 is not required)

### 7.3 Security
- File names are sanitized and replaced with generated IDs
- Original file names are not stored or exposed
- Only whitelisted MIME types are accepted
- Maximum file size enforced
- Temporary files are cleaned up on a schedule

---

## 8. Authentication and Roles

### 8.1 Authentication Method
- JWT-based authentication for MVP
- No OAuth or SSO required for MVP (future scope)
- Passwords stored as hashed values (bcrypt or Argon2)

### 8.2 Roles

| Role | Access |
|---|---|
| **Reporter** (default) | Submit reports; view own reports; view location alerts; receive AI response |
| **Maintenance** | All reporter access; view full maintenance queue; update status; resolve issues |
| **Admin** | All maintenance access; view analytics dashboard; manage locations/categories |

### 8.3 Role Assignment
- Default role on registration: Reporter
- Role escalation (Maintenance / Admin): manual process by Admin — not self-service
- Role is verified server-side on every protected request

---

## 9. Notification and Alert Flow

### 9.1 Alert Creation
```
Issue created or safety flag raised
  → Alert record created with scope (location-specific or campus-wide)
  → Alert linked to issue and location
  → Alert visible to users whose selected locations match
```

### 9.2 Alert Display
- User selects preferred campus locations on their profile
- On login / dashboard load: system queries active alerts matching user's locations
- Campus-wide critical alerts are always shown regardless of location preference

### 9.3 Alert Resolution
```
Maintenance staff marks issue as Resolved
  → Issue status updated
  → Alert `is_active` set to False
  → Active alert removed from user-facing view
  → Historical record preserved (issue + alert both retained)
```

### 9.4 Push Notifications
- Out of scope for MVP
- May be added later as a progressive enhancement (Web Push API)

---

## 10. Maintenance Workflow (System Perspective)

```
1. Report submitted
2. AI classification runs (async where possible to avoid blocking user)
3. Duplicate check runs
4. Issue created or existing issue updated (report count++)
5. Priority score computed (rule-based + AI inputs)
6. Issue appears in maintenance queue at correct priority position
7. Staff reviews and acts
8. Staff updates status (Open → In Progress → Resolved)
9. On Resolved: alert deactivated; historical record updated
```

### Priority Score Computation
Priority is computed deterministically from:
- Safety flag (if rule-based safety guardrail triggered → always Critical regardless of AI score)
- Issue category weight
- Severity weight
- Report count (logarithmic scaling to avoid count-stuffing)
- Recurrence factor (historical repeat rate for same location/category)
- Location impact factor (hostel with 500 residents > single-occupancy room)

> AI may contribute a suggested severity or urgency — but the final priority is always computed by deterministic logic that can override the AI suggestion.

---

## 11. Admin Workflow (System Perspective)

Admin analytics queries aggregate from the issues and reports tables:
- Group by category, location, time window
- Compute resolution rate, average resolution time
- Surface recurring issues (same location/category appearing > N times in period)
- Export or view in dashboard

No real-time data pipeline is required for MVP — standard DB aggregation queries are sufficient.

---

## 12. Docker Architecture

```yaml
# docker-compose.yml (planned structure)
services:
  app:           # FastAPI backend
  db:            # PostgreSQL (or MongoDB)
  chromadb:      # ChromaDB vector store
  storage:       # MinIO (optional, for object storage in production)
  # AI models (Ollama) may run as a sidecar or external service
```

- All services are containerized
- Environment variables managed via `.env` files — never committed to Git
- Development and production docker-compose files are kept separate

---

## 13. Data Flow Summary

```
[User] → submits report (text + image + location)
  → [FastAPI] validates input
  → [AI Service] classifies (category, severity, suggested action)
  → [Safety Rules] validate and override if necessary
  → [Duplicate Service] checks for existing issues
  → [DB] creates or updates issue record
  → [RAG Service] retrieves relevant guidance (async)
  → [FastAPI] returns response to user (quick action or safety alert)
  → [Alert Service] creates/updates alert record
  → [DB] alert becomes visible to location-matched users
```

---

## 14. Security Considerations

| Concern | Approach |
|---|---|
| API authentication | JWT; every protected endpoint verifies token |
| Role enforcement | Server-side role check on every request |
| Input validation | FastAPI Pydantic models validate all inputs |
| File upload security | Type whitelist, size limit, name sanitization |
| Secret management | Environment variables via `.env`; never in source code |
| SQL injection | ORM (SQLAlchemy) or parameterized queries only |
| CORS | Restricted to known frontend origin |
| Rate limiting | Applied to report submission and upload endpoints (MVP: simple middleware) |
| Photo retention | Temporary files purged; no unnecessary retention |
| Personal data | Minimal collection; no face recognition; no profiling |
| Audit logging | AI decisions and status changes logged with timestamps |
