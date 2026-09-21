# Product Requirements Document (PRD)

**Project:** Campus Sustainability & Issue-Response Platform
**Repository:** `campus-issue-platform`
**Product Name:** TBD
**Program:** 1M1B – IBM SkillsBuild AI + Sustainability Virtual Internship
**Status:** Pre-development — documentation phase
**Last Updated:** 2026-09-20

---

## 1. Problem

Campus sustainability and safety issues — leaking taps, broken lighting, energy waste, unsafe electrical or structural conditions — are frequently under-reported or poorly managed. When multiple people observe the same problem:

- They may report it separately, creating duplicate tickets and wasted effort.
- Maintenance teams may not be able to easily identify which reports describe the same issue.
- There is no consistent, accessible channel for reporting.
- Reporters receive no immediate guidance on what to do while waiting.
- There is no location-aware alert system to warn nearby users of active hazards.
- Historical data is rarely used for proactive sustainability planning.

Campus users currently have no unified, easy-to-use platform that connects their reports to meaningful action and keeps them informed.

---

## 2. Goals

1. Provide a low-friction, mobile-friendly reporting experience for all campus users.
2. Group likely-duplicate reports to avoid redundant maintenance tickets.
3. Deliver immediate, contextual guidance to reporters — safe temporary actions for ordinary issues; safety alerts for hazardous situations.
4. Give maintenance staff a prioritized, de-duplicated issue queue with status tracking.
5. Give administrators campus-wide analytics to support sustainability planning.
6. Use AI responsibly as an assistive layer — not as a replacement for human judgement.
7. Align with 1M1B internship guidelines: SDG alignment, responsible AI, real-world impact.

---

## 3. Non-Goals

The following are explicitly **out of scope** for this project:

- General-purpose AI chatbot or sustainability Q&A assistant
- Global or city-wide environmental monitoring
- Integration with external municipal or government systems
- Automated dispatch or routing of maintenance staff
- Financial management or procurement features
- Social media sharing or external public visibility
- Face recognition, biometrics, or any form of student surveillance
- Mandatory paid third-party APIs or services
- Native mobile apps (web-first; mobile-responsive)

---

## 4. Target Users

### 4.1 Student / Faculty / Staff (Reporters)
- Primary reporters of issues
- Varying levels of technical proficiency
- May use mobile devices in the field
- Expect instant feedback and minimal form complexity

### 4.2 Facility / Maintenance Staff
- Receive and act on reported issues
- Need clear prioritization and de-duplication
- Update issue status; resolve alerts
- May have limited technical proficiency — interface must be simple

### 4.3 College Administration
- View campus-wide analytics and trends
- Use data for sustainability and maintenance planning
- Not involved in day-to-day issue resolution

### 4.4 Green Club / NSS / Eco Club Members
- May act as motivated reporters
- May later participate in sustainability tracking (future scope)

---

## 5. User Stories

### Reporter Stories

| ID | As a... | I want to... | So that... |
|---|---|---|---|
| R-01 | Student | Report an issue with a photo and short description | Maintenance is notified quickly without a complex form |
| R-02 | Student | Select my campus location from a familiar list | My report reaches the right team |
| R-03 | Student | Receive immediate guidance after reporting | I know what to do right now |
| R-04 | Student | See a safety warning for hazardous situations | I stay safe and don't attempt dangerous repairs |
| R-05 | Faculty | See active alerts for the areas I use regularly | I am informed of nearby hazards |
| R-06 | Staff | Know whether someone else has already reported the same issue | I don't duplicate existing reports |

### Maintenance Staff Stories

| ID | As a... | I want to... | So that... |
|---|---|---|---|
| M-01 | Maintenance staff | See a prioritized queue of open issues | I address the most critical issues first |
| M-02 | Maintenance staff | See how many people reported the same issue | I understand the scale and impact |
| M-03 | Maintenance staff | See likely duplicate reports grouped together | I don't work from redundant tickets |
| M-04 | Maintenance staff | Update issue status (Open, In Progress, Resolved) | The team and reporters are kept informed |
| M-05 | Maintenance staff | Resolve the alert when I have fixed the issue | The alert disappears for location-relevant users |
| M-06 | Maintenance staff | See a plain-language AI summary of multiple reports | I understand the issue without reading each one |

### Admin Stories

| ID | As a... | I want to... | So that... |
|---|---|---|---|
| A-01 | Administrator | See campus-wide issue trends | I can plan maintenance and sustainability efforts proactively |
| A-02 | Administrator | Identify recurring problems and hotspot locations | I understand systemic issues |
| A-03 | Administrator | View issues by category, severity, and resolution status | I can report to leadership and allocate resources |
| A-04 | Administrator | See resolution rate and response time data | I can measure team performance |

---

## 6. Core Workflows

### 6.1 Reporting Workflow

```
User opens platform
  → Selects or confirms location (hostel, block, floor, area)
  → Optionally takes/uploads a photo
  → Provides short description (optional if photo provided)
  → Submits report
  → AI classifies issue (category, severity, safety level)
  → System checks for likely duplicate reports at same location
    → If duplicate found: report is linked to existing issue, count incremented
    → If new issue: new issue record created
  → System determines response type:
    → Safety-critical: displays safety alert
    → Ordinary issue: displays quick action suggestion
  → Reporter sees confirmation + guidance
  → Relevant location-based alert is created/updated for other users
```

### 6.2 Maintenance Workflow

```
Staff logs in
  → Sees prioritized issue queue (safety-critical first)
  → Each issue shows: category, severity, location, report count, AI summary
  → Staff selects issue
  → Reviews detail view (individual reports, photos, AI summary)
  → Updates status: Open → In Progress → Resolved
  → On resolution: active alert is closed; historical record preserved
```

### 6.3 Duplicate Detection Workflow

```
New report submitted
  → System extracts: location, category, key issue attributes (from text + image AI output)
  → Hard filter: only open issues at the SAME location and SAME category are considered
    (different location = always a separate issue, regardless of any other similarity)
  → Time window check: only issues reported within a configurable recent window are candidates
    (a report from last month at the same location may indicate a RECURRING issue,
     not the same active issue — see Recurring Issues note below)
  → Semantic similarity scored against candidate issues using extracted attributes + description
  → Duplicate decision requires ALL of:
      - Matching location (hard requirement)
      - Matching or closely related category (hard requirement)
      - Within the time window (hard requirement)
      - Semantic similarity above threshold
      - Consistent key attributes (e.g., same fixture type, same floor area if determinable)
  → If all conditions met: link report to existing issue; increment report_count
  → If any hard condition fails: create new issue record
  → Maintenance staff can always manually merge or separate issues
```

> **Recurring Issues:** If the same location and category produce a new report after the prior issue was resolved, the system creates a new issue record rather than reopening the old one. The historical relationship between the old and new issue is preserved for admin analytics to surface recurring patterns.


### 6.4 Alert Lifecycle

```
Issue reported → Alert created (if warranted) → Shown to location-relevant users
  → Status: Open → In Progress (visible, flagged as being worked on)
  → Status: Resolved → Alert removed from active view; record retained in history
Campus-wide critical alert → Shown to all users regardless of location filter
```

---

## 7. Functional Requirements

### 7.1 Issue Reporting
- FR-01: Users must be able to report an issue with at minimum one of: photo or text description.
- FR-02: Location selection must be structured (campus area → building → floor/zone) and required.
- FR-03: The system must classify the issue into a predefined category set automatically.
- FR-04: The system must assign a severity and safety-level flag, with rule-based guardrails for critical categories.
- FR-05: The system must detect likely duplicates before creating a new issue record. Reports must not be merged based on semantic similarity alone. A duplicate determination requires all of the following signals to agree: matching location, matching or closely related category, submission within a configurable time window, semantic similarity above threshold, and consistent key issue attributes extracted from the report.
- FR-06: For every submitted report, users must receive a response: either a quick action suggestion or a safety alert.

### 7.2 Alerts
- FR-07: Active alerts must be displayed to users who select a relevant location.
- FR-08: Campus-wide critical alerts must override location filtering.
- FR-09: Alerts must be removed from active view upon resolution; historical data must be preserved.
- FR-10: Alert severity must be human-readable and use plain language.

### 7.3 Maintenance Queue
- FR-11: Maintenance staff must see a prioritized issue queue.
- FR-12: Priority must reflect safety risk, report count, severity, recurrence, and category — not only AI output.
- FR-13: Each issue must show report count, category, severity, location, and AI summary.
- FR-14: Staff must be able to update status (Open, In Progress, Resolved).
- FR-15: Staff must be able to manually merge or separate grouped issues.

### 7.4 Admin Analytics
- FR-16: Admins must see campus-wide trends over time.
- FR-17: Admins must be able to filter by category, severity, location, and time range.
- FR-18: Recurring issues and hotspot locations must be surfaced prominently.
- FR-19: Resolution metrics (rate, average resolution time) must be available.

### 7.5 AI Behavior
- FR-20: AI must never provide DIY repair instructions for safety-critical issues.
- FR-21: AI must source recommendations from the campus knowledge base (RAG) where applicable and distinguish them from generated content. If no relevant verified campus source is retrieved, the system must clearly indicate that the response is based on general guidance rather than campus-specific policy. The system must never invent or imply that general guidance is an official campus policy.
- FR-22: Rule-based guardrails must override AI classification for defined critical hazard categories.
- FR-23: AI contributions must be transparently indicated in the interface.

### 7.6 Privacy and Data
- FR-24: Photos must not be retained after they are no longer needed for classification.
- FR-25: User identities must not be exposed in aggregated views or public-facing output.
- FR-26: The system must not collect unnecessary personal information.

### 7.7 Accessibility
- FR-27: Users with different levels of technical ability must be able to submit a basic report with minimal typing. The reporting interface must support this through:
  - Large, clear visual controls (tap targets sized for mobile use)
  - Predefined issue category selection (no free-text category entry required)
  - Structured location selection (hierarchical dropdowns or equivalent; no manual address entry)
  - Photo capture or upload as a primary reporting method (description text is optional when a photo is provided)
  - Plain-language instructions at each step with no technical jargon
- FR-28: Voice input may be considered as a future enhancement (see Section 9) and must not be required for basic report submission in the MVP.

---

## 8. MVP Scope

The Minimum Viable Product must include:

> **Prototype Constraint:** The MVP may use seeded or demo campus locations, sample reports, and a limited campus knowledge base sufficient to demonstrate the core workflows. Production-scale data integrations, live campus system connections, and full knowledge base population are outside the prototype scope.

| # | Feature | Priority |
|---|---|---|
| 1 | Issue report submission (photo + text, location selection) | Must have |
| 2 | AI issue classification (category + severity) | Must have |
| 3 | Rule-based safety flagging for critical categories | Must have |
| 4 | Duplicate detection and report grouping | Must have |
| 5 | Quick action response / safety alert on submission | Must have |
| 6 | Maintenance staff issue queue with status update | Must have |
| 7 | Location-based alert display for users | Must have |
| 8 | Alert lifecycle (open → resolved → removed) | Must have |
| 9 | Basic admin analytics view (trends, counts) | Should have |
| 10 | AI report summarization for maintenance staff | Should have |
| 11 | RAG-powered guidance retrieval | Should have |
| 12 | Role-based access (reporter, maintenance, admin) | Must have |

---

## 9. Future Scope

The following features are **explicitly deferred** and may be considered after MVP:

- Voice input for issue reporting
- Push notifications (browser or mobile)
- Native mobile app
- Green Club / NSS participation workflows
- Gamification or sustainability points
- Automated maintenance staff routing
- External API integrations (municipality, IoT sensors)
- Multi-language support
- Public-facing transparency dashboard
- Anonymous reporting option
- Offline-capable PWA

---

## 10. Success Metrics

| Metric | Description |
|---|---|
| Reporting adoption | Percentage of campus users who submit at least one report |
| Duplicate reduction | Ratio of reports merged vs. new issues created |
| Resolution time | Average time from report submission to Resolved status |
| Safety alert response | Time from hazard report to alert appearing for nearby users |
| AI classification accuracy | Manual review of category and severity assignments |
| Maintenance staff usability | Qualitative feedback on queue usability |
| Admin analytics utility | Qualitative feedback on trend visibility |
| Recurring issue detection | Whether the system surfaces known problem locations |

---

## 11. Responsible AI Requirements

| Principle | Requirement |
|---|---|
| **Safety** | AI never determines final safety classification alone; rule-based guardrails always apply |
| **Transparency** | Users are informed when AI has contributed to a response or classification |
| **No unsafe instructions** | System never generates DIY repair guidance for safety-critical issues |
| **Privacy** | No face recognition; no biometric data; photos used only for classification |
| **Minimal data** | Only necessary personal information is collected |
| **Fairness** | System does not disadvantage users based on writing style, language quality, or device type |
| **Human control** | Maintenance staff retain full authority to override, merge, split, or reclassify issues |
| **Source attribution** | RAG-retrieved information is distinguished from AI-generated content |
| **Auditability** | AI decisions, rule triggers, confidence/assessment metadata, and resulting actions can be logged for review. Audit logs must not unnecessarily store personally identifying information. |
