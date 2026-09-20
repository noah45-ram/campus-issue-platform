# [Project Name — TBD]

> **Note:** The final product name has not been decided yet. This placeholder will be updated before public release.

---

## Overview

This is a campus-wide sustainability and issue-response platform being developed as part of the **1M1B – IBM SkillsBuild AI + Sustainability Virtual Internship**.

The platform allows students, faculty, and staff to report sustainability, maintenance, and safety issues on campus — and enables facility/maintenance teams and administrators to manage, prioritize, and resolve those issues efficiently.

---

## The Problem

Campus maintenance and sustainability issues — leaking taps, broken equipment, energy waste, unsafe conditions — are often under-reported, slow to be resolved, or managed through fragmented processes. Multiple people may notice the same problem but report it independently, creating duplicate tickets and wasted effort. There is no easy, unified way for campus users to report issues, receive guidance, and stay informed about hazards near them.

---

## Target Users

| Role | Needs |
|---|---|
| **Students** | Quick, low-friction issue reporting; immediate guidance; relevant location alerts |
| **Faculty & Staff** | Same as students; may also flag recurring or systemic concerns |
| **Facility / Maintenance Staff** | Prioritized issue queue; duplicate detection; status tracking |
| **College Administration** | Campus-wide analytics; trend identification; sustainability planning data |
| **Green Club / NSS / Eco Club** | Visibility into sustainability issues; participation in resolution |

---

## Planned Features

### For Reporters (Students, Faculty, Staff)
- Report an issue with a photo and/or short description
- Select or confirm the campus location (hostel, block, floor, etc.)
- Receive an immediate AI-generated response
- Receive a quick temporary action suggestion for ordinary issues
- Receive a safety alert (not DIY instructions) for hazardous situations
- See active alerts relevant to selected locations

### For Maintenance / Facility Staff
- Prioritized issue queue (safety-critical issues at top)
- View severity, category, and number of reports per issue
- Detect and merge likely duplicate reports
- Update issue status: Open → In Progress → Resolved
- Close alerts when issues are actually resolved

### For Administrators
- Campus-wide dashboard with trends
- Recurring problem and hotspot identification
- Issue analytics by category, severity, location, and time
- Data for sustainability and maintenance planning

---

## AI Role

AI assists — it does not replace — human judgement.

| Task | AI Role |
|---|---|
| Issue classification | Categorizes issue type from text and image |
| Image understanding | Extracts relevant visual evidence from uploaded photos |
| Duplicate detection | Groups likely-duplicate reports |
| Report summarization | Summarizes multiple reports for maintenance staff |
| Quick action generation | Suggests safe temporary actions for ordinary issues |
| Safety alert generation | Produces safety-first warnings for hazardous reports |
| RAG retrieval | Retrieves relevant campus policies and safety guidance |
| Priority assistance | Assists prioritization, bounded by deterministic safety rules |
| Pattern recognition | Identifies recurring issues from historical data |

> **Important:** AI does not make final safety classification decisions. Rule-based safeguards ensure critical hazards are always escalated correctly, regardless of AI output.

---

## Technology Direction

| Layer | Planned Technologies |
|---|---|
| Backend | Python, FastAPI |
| Database | PostgreSQL (relational) + MongoDB (unstructured/logs) — choice to be finalized |
| AI / LLM | Open-source or free-tier LLM (e.g., Gemini free tier, Ollama local models) |
| Vector Search / RAG | ChromaDB |
| Orchestration | LangGraph (where genuinely useful) |
| Containerization | Docker |
| Version Control | Git / GitHub |
| Frontend | To be determined — mobile-friendly, accessibility-first |

All mandatory components must have a free or open-source option. No paid services will be introduced without explicit approval.

---

## Responsible AI

This project is designed with responsible AI principles from the outset:

- **No face recognition or biometric data**
- **No unnecessary personal profiling**
- **No student surveillance**
- **Photos used only for issue classification — not retained unnecessarily**
- **AI transparency:** users can see when AI has contributed to a response
- **Fairness:** system does not penalize users for language or writing ability
- **Human control:** maintenance staff retain final authority over all decisions
- **Deterministic safety guardrails:** rule-based logic, not LLM alone, controls critical-hazard handling

---

## SDG Alignment

This platform contributes to:
- **SDG 11** — Sustainable Cities and Communities (campus as a model community)
- **SDG 6** — Clean Water and Sanitation (leak detection and resolution)
- **SDG 7** — Affordable and Clean Energy (energy waste reporting)
- **SDG 3** — Good Health and Well-Being (hazard reporting and rapid response)

---

## Development Status

| Phase | Status |
|---|---|
| Documentation & Architecture | 🟡 In Progress |
| Backend scaffolding | ⬜ Not started |
| AI pipeline | ⬜ Not started |
| Frontend | ⬜ Not started |
| Testing | ⬜ Not started |
| Deployment | ⬜ Not started |

---

## Screenshots / Demo

> _(Placeholder — screenshots and demo link will be added after prototype is complete.)_

---

## Project Context

- **Program:** 1M1B – IBM SkillsBuild AI + Sustainability Virtual Internship
- **Repository:** `campus-issue-platform`
- **Final product name:** TBD

---

## License

TBD
