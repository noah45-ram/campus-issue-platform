# AI Design Document

**Project:** Campus Sustainability & Issue-Response Platform
**Repository:** `campus-issue-platform`
**Status:** Pre-development — AI design phase
**Last Updated:** 2026-09-20

> This document defines how AI is used in the system, what it is responsible for, what it is not responsible for, and how it is safeguarded. Every AI feature must trace back to a real need defined in the PRD.

---

## 1. AI Usage Overview

AI is used as an **assistive layer** — not as the system's decision-maker. Every AI-generated output either informs a human decision or is validated by deterministic rules before affecting system behavior.

| What AI Does | What AI Does NOT Do |
|---|---|
| Classify issue category | Set final safety classification alone |
| Suggest severity | Override rule-based safety guardrails |
| Generate quick action suggestions | Provide DIY repair instructions for hazardous issues |
| Generate safety alert text | Make autonomous decisions about maintenance routing |
| Summarize multiple reports | Determine final priority score (only contributes to it) |
| Detect likely duplicates (similarity scoring) | Merge or close issues without human confirmation |
| Retrieve relevant guidance via RAG | Fabricate campus policy it has not retrieved |
| Analyze uploaded images | Identify people, faces, or personal attributes |
| Surface recurring patterns | Guarantee 100% accuracy in any of the above |

---

## 2. Issue Classification Workflow

### 2.1 Input
- User-provided text description (optional)
- Uploaded image (optional; at least one of the two is required)
- Selected location (structured)

### 2.2 Processing Steps

```
Input received
  → Multimodal AI call: text + image → structured classification output
  → Output fields:
      - category (from predefined enum)
      - suggested_severity (Low / Medium / High / Critical)
      - safety_concern (boolean)
      - safety_concern_reason (brief text if flagged)
      - suggested_quick_action (text, only if not safety-critical)
      - confidence_score (optional, for internal logging)
  → Rule-based safety guardrails applied (see Section 7)
  → Final category and safety_flag written to Issue record
```

### 2.3 Predefined Category Enum (Draft — subject to refinement)

| Code | Category |
|---|---|
| `WATER` | Water / Plumbing |
| `ELECTRICAL` | Electrical / Power |
| `STRUCTURAL` | Structural / Civil |
| `WASTE` | Waste / Sanitation |
| `ENERGY` | Energy / Lighting |
| `FIRE_SAFETY` | Fire Safety |
| `PEST` | Pest / Infestation |
| `HVAC` | Ventilation / Cooling |
| `GENERAL` | General Maintenance |
| `OTHER` | Uncategorized |

> Categories may be expanded during development. Any addition must be reflected in both the AI prompt and the rule-based guardrail map.

### 2.4 Severity Enum
- `LOW` — Cosmetic or minor inconvenience
- `MEDIUM` — Functional impact, not immediately dangerous
- `HIGH` — Significant impact; potential for harm if unaddressed
- `CRITICAL` — Immediate safety risk; must be escalated

---

## 3. Image and Text Understanding

### 3.1 Image Handling
- Images are passed to a multimodal LLM (e.g., Gemini free-tier or local equivalent)
- The LLM is prompted to:
  - Describe what the image shows
  - Identify relevant issue indicators (water, smoke, damage, etc.)
  - Suggest a category based on visual evidence
  - Flag if the image contains any potential safety concern
- The image **is not** used to identify people, locations beyond what the user provides, or any personal attributes

### 3.2 Text Handling
- User description is included in the same prompt as the image
- Text can complement, override, or clarify the image interpretation
- The LLM extracts: key issue indicators, location hints, urgency signals

### 3.3 Limitations to Acknowledge
- Image quality (blur, low light) may degrade classification accuracy
- Users may upload irrelevant or misleading images — safety rules must not depend on image content alone
- The system must degrade gracefully: if image analysis fails, text-only classification is attempted

---

## 4. Duplicate Detection

### 4.1 Rationale
Multiple users often report the same issue independently. Creating separate tickets for the same physical issue wastes maintenance effort and obscures true impact.

### 4.2 Approach (Rule + Similarity Hybrid)

```
New report submitted with (location_id, category, description, image classification output)

Step 1 — Hard filter:
  → Query open issues WHERE location_id = report.location_id AND category = report.category
  → If none found → skip to Step 3 (create new issue)

Step 2 — Similarity scoring:
  → For each candidate issue in Step 1:
      - Text similarity: embed report description + existing issue descriptions → cosine similarity
      - Keyword overlap: extract key indicators from AI classification outputs → overlap score
      - Time proximity: reports within a configurable time window score higher
      - Combine scores into a weighted similarity score
  → If score > threshold (TBD, suggest 0.75 initially): flag as likely duplicate

Step 3 — Decision:
  → Similarity above threshold → link report to existing issue; increment report_count
  → Similarity below threshold → create new issue
  → Maintenance staff can always manually merge or separate
```

### 4.3 Important Constraint
- Two issues at different locations (e.g., H4 vs. H5) must **never** be merged regardless of similarity score
- Location is a hard filter, not a soft factor

### 4.4 Staff Override
- Maintenance staff can manually merge issues (link a report to a different parent issue)
- Maintenance staff can manually split issues (move a report to a new issue)
- These overrides are logged for audit

---

## 5. RAG Workflow

### 5.1 Purpose
Ground AI-generated guidance in actual campus documents rather than generating advice from model weights alone.

### 5.2 Knowledge Base Ingestion (One-time / Periodic)

```
Campus document (PDF, text, DOCX)
  → Text extracted and cleaned
  → Chunked (e.g., 300–500 tokens per chunk with overlap)
  → Each chunk embedded using local sentence embedding model
  → Chunk + embedding stored in ChromaDB with metadata:
      - source_document: filename or document title
      - section: section heading if extractable
      - category_tags: relevant issue categories (optional, for filtered retrieval)
```

### 5.3 Query-Time Retrieval

```
Issue report classification complete
  → Query string constructed from: category + key issue indicators + location type
  → Query embedded using same model
  → ChromaDB similarity search → top-k most relevant chunks retrieved
  → Retrieved chunks passed to LLM with prompt:
      "Based on the following campus guidance: [chunks]
       Generate a brief, user-friendly response for a [category] issue."
  → Response returned with source attribution
```

### 5.4 Attribution and Transparency
- Any response that uses retrieved content must include a note such as:
  _"Based on campus sustainability guidelines."_
- Source document name must be logged and available for audit
- AI-generated content not grounded in retrieved documents must be visually distinguished

### 5.5 RAG Failure Handling
- If ChromaDB returns no relevant chunks: fall back to a safe, general guidance response
- If RAG service is unavailable: log the failure; return a degraded but safe response; do not block issue submission

---

## 6. Quick Action Generation

### 6.1 When Used
- Issue category is NOT safety-critical (no safety flag triggered)
- Submitted report is for an ordinary maintenance or sustainability issue

### 6.2 Output Format
- Short (1–3 sentences maximum)
- Actionable, plain language
- Focused on safe, temporary measures until maintenance arrives
- Does not imply the user should fix the problem themselves

### 6.3 Example Outputs

| Issue | Quick Action |
|---|---|
| Leaking tap | "Place a bucket underneath to reduce water waste until maintenance arrives. Turn off the tap if it has a working shut-off valve." |
| Broken light | "Avoid working in the dark area if possible. Use available lighting from adjacent areas until the fixture is repaired." |
| Overflowing waste bin | "Do not add more waste to the bin. Use the nearest alternative bin and report the collection point." |

### 6.4 Constraints
- Quick actions must **never** suggest the user approach electrical equipment, handle structural elements, or enter unsafe areas
- If there is any ambiguity about safety, the system must default to a safety alert (Section 7) rather than a quick action

---

## 7. Safety Alert Generation

### 7.1 Trigger Conditions
A safety alert is generated when **any** of the following is true:
- Rule-based guardrail flags the category as safety-critical (see 7.2)
- AI classification outputs `safety_concern = true` AND the category is in the at-risk list
- Report contains keywords matching a safety keyword list (deterministic match — not LLM-dependent)

### 7.2 Rule-Based Safety Guardrail Map

The following categories always trigger safety handling regardless of AI output:

| Category Code | Safety Rule |
|---|---|
| `ELECTRICAL` | Always safety alert; never quick action |
| `FIRE_SAFETY` | Always safety alert; escalate immediately to Critical |
| `STRUCTURAL` | Safety alert if description/image suggests collapse/crack risk |
| `GAS` (future) | Always safety alert |

Additional keyword triggers (deterministic, case-insensitive match):
- `smoke`, `fire`, `burn`, `spark`, `shock`, `electrocution`, `collapse`, `crack`, `gas leak`, `fumes`

### 7.3 Safety Alert Content

A safety alert must:
- Tell the user to move away / not touch / not attempt repairs
- Direct the user to contact the responsible campus team or emergency services if appropriate
- Be written in plain, urgent but calm language
- Never include any suggestion that sounds like DIY guidance

**Example:**

> "⚠️ Safety Alert: Do not approach or touch the electrical equipment. Move away from the area immediately. Do not attempt any repairs. The campus maintenance team has been notified and will respond. If you observe smoke or fire, contact campus security immediately."

### 7.4 AI Role in Safety Alert Generation
- AI may generate the alert text (phrasing)
- AI does NOT decide whether to show a safety alert — that is determined by rule-based guardrails
- The guardrail runs on AI output and on raw user input (keyword check) independently

---

## 8. Priority-Assistance Workflow

### 8.1 AI Contribution
AI outputs a `suggested_severity` as part of classification. This is one input to the priority score.

### 8.2 Priority Score Computation (Deterministic)

```
priority_score = (
    safety_weight         # if safety_flag = True → +1.0 (overrides all other factors to Critical)
  + category_weight       # predefined weight per category (e.g., ELECTRICAL > WATER > WASTE)
  + severity_weight       # mapped from AI-suggested severity (Low=0.1, Medium=0.3, High=0.6, Critical=1.0)
  + report_count_factor   # log(report_count + 1) / log(max_reports + 1) — scales sublinearly
  + recurrence_factor     # 0.0–0.3 based on historical repeat rate for location/category pair
  + location_impact       # 0.0–0.2 based on expected user density of affected location
)
```

### 8.3 Safeguard
- If `safety_flag = True`, priority is set to Critical regardless of numeric score
- This ensures no edge case in report count, category weight, or AI error can suppress a safety-critical issue

### 8.4 Priority Transparency
- Priority score and its contributing factors are visible to maintenance staff and admin
- Staff can view why an issue ranked as it did

---

## 9. Rule-Based Safety Guardrails

### 9.1 Design Principle
Safety guardrails are implemented as deterministic code, not as LLM instructions. The LLM cannot be instructed to "never give unsafe advice" with guaranteed reliability. Rules must enforce this at the code level.

### 9.2 Implementation Location
`app/core/safety_rules.py` — A standalone module that:
- Accepts AI classification output + raw user input text
- Runs keyword matching on raw text (independent of AI)
- Checks category against the safety rule map
- Returns: `{ safety_flag: bool, safety_level: str, override_applied: bool }`
- Is called before any AI-generated quick action is allowed through

### 9.3 Override Behavior
```
AI suggests category = ELECTRICAL, quick_action = "Try switching off the breaker"
  → safety_rules.py detects ELECTRICAL category
  → override_applied = True
  → quick_action is discarded
  → safety_alert is generated instead
  → override is logged with reason
```

### 9.4 Audit
Every time a safety override is applied, the following is logged:
- Timestamp
- Issue ID
- AI original output (for review)
- Rule that triggered the override
- Final output delivered to user

---

## 10. Human and Maintenance Control Points

| Decision | Who Decides | AI Role |
|---|---|---|
| Whether an issue is safety-critical | Rule-based guardrail (deterministic) | Contributes classification; can be overridden |
| Final priority of an issue in the queue | Computed deterministically from inputs | Contributes severity suggestion |
| Whether two reports are the same issue | Maintenance staff (with AI suggestion) | Scores similarity; does not merge autonomously |
| Issue status (Open / In Progress / Resolved) | Maintenance staff only | Not involved |
| Alert deactivation | Maintenance staff only | Not involved |
| Merging or splitting grouped issues | Maintenance staff only | Suggests grouping |
| Content of campus knowledge base | Administrator | Not involved |

---

## 11. AI Failure Cases and Mitigations

| Failure Case | Mitigation |
|---|---|
| LLM API is unavailable | System falls back to keyword-based category assignment; report is still submitted; user receives generic safe guidance |
| Image analysis fails (corrupt file, timeout) | Classification proceeds with text only; image processing failure is logged |
| AI generates a quick action for a safety-critical issue | Rule-based guardrail strips the output and replaces it with a safety alert |
| Duplicate detection misses a real duplicate | Maintenance staff can manually merge; report count is visible |
| Duplicate detection incorrectly merges different issues | Maintenance staff can manually split; override is logged |
| RAG retrieves irrelevant chunks | Response is still generated; attribution note indicates source; staff can verify |
| AI classification produces an unknown category | Defaults to `GENERAL`; flagged for manual review |
| AI confidence is very low | Issue is flagged for human review; default safe handling applied |

---

## 12. Evaluation and Test Cases

### 12.1 Classification Test Cases

| Input | Expected Category | Expected Safety Flag |
|---|---|---|
| "Water dripping from ceiling in H4 bathroom" | `WATER` | False |
| "Sparks coming from plug socket near lab entrance" | `ELECTRICAL` | True |
| "Lights flickering in corridor 3B" | `ELECTRICAL` | True |
| "Overflowing dustbin at canteen entrance" | `WASTE` | False |
| "Smoke visible from electrical panel room" | `ELECTRICAL` / `FIRE_SAFETY` | True |
| "Broken window in classroom 101" | `STRUCTURAL` | Conditional |
| "AC not cooling in library" | `HVAC` | False |

### 12.2 Duplicate Detection Test Cases

| Scenario | Expected Outcome |
|---|---|
| Two reports of leaking tap in H4 bathroom within 2 hours | Merged into one issue |
| Report of leaking tap in H4 followed by one in H5 | Two separate issues |
| Three reports of broken light in corridor 3B same day | Merged; report_count = 3 |
| Report of broken light in corridor 3B and a report 3 months later (resolved) | New issue created for the later report |

### 12.3 Safety Alert Test Cases

| Input Keyword | Expected Response Type |
|---|---|
| "spark" | Safety alert (electrical keyword match) |
| "fire" | Safety alert (fire keyword match) |
| Any report with category = ELECTRICAL | Safety alert regardless of description |
| "leaking tap" | Quick action (ordinary issue) |
| "smoke" | Safety alert (smoke keyword match) |

### 12.4 RAG Attribution Test Cases

| Query | Expected |
|---|---|
| Report about water wastage | Response cites campus water conservation policy |
| Report about overflowing bin | Response cites waste segregation guidelines |
| Report with no matching document | Response still given; no fabricated policy citation |
