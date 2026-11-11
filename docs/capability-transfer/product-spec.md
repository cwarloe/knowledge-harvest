# Product specification: one dependency, four screens

**Proposed implementation, not shipped functionality.** The [workbook](pilot-workbook.md) is usable now. [Implementation backlog](implementation-backlog.md) controls build order.

## Existing app integration

`web/src/App.js` currently provides recording, metadata, browsing, search, and playback in a single React component. `services/server.js` exposes `/api/recordings` with PostgreSQL metadata and local-file uploads; its `s3_key` currently holds a filename. The same server also has an unauthenticated `DELETE /api/recordings/:id` route, but the current UI does not call it. `services/schema.sql` defines only recordings. These observations describe source inspection, not a verified deployment.

Add a separate Cases area and components rather than replacing the recording workflow. A case can link an existing recording as one evidence source; recording is optional. Do not assume S3 exists because older architecture documents mention it. Do not add microservices for this workflow.

## Four screens

| Screen | Inputs and actions | Output / visible boundary |
| --- | --- | --- |
| Dependency | Define behavior and task boundary; log eligible opportunities; attach source references; confirm diagnoses | Baseline counts, causes, unresolved barriers, next owner/action |
| Expertise | Capture expert cues and contrasting cases; draft aid; approve a version; review unfamiliar practice | Draft vs approved aid, practice readiness, source provenance |
| Application | Agree authority, access, time, next opportunity, supervisor review, recovery plan | Ready/blocked conditions; supported work recorded separately from independent work |
| Results | Review live outputs and delayed defects; compare windows; record conclusion and owner decision | Raw counts + rates + missing data + scope/limitations; no automatic competence badge |

Keep workflow stage, evidence status, and owner decision as separate fields. A case can be in Prove with insufficient evidence or return to Diagnose after a failed attempt. A reviewer records each transition, reason, time, and referenced evidence. Changes to approved aid rules create a new draft version and require renewed review; preserve the prior version used in each attempt.

## Domain model

Use server-generated IDs and timestamps, required case ownership, foreign keys, and explicit null for unknown values. The following is a logical model, not a deployed SQL migration.

| Entity | Key fields / relationships |
| --- | --- |
| Case | id, title, target behavior, scope/exclusions, owner/employee/expert/supervisor/reviewer references, workflow_stage, evidence_status, decision, baseline/follow-up windows, evidence requirement, quality/stop rules, review date, revision |
| Opportunity | id, case_id, date, period, task category/complexity, original employee decision/reason, escalated, founder_minutes nullable, other_support_minutes nullable, aid_version_id nullable, evidence_ref |
| Diagnosis | id, case_id, cause category, evidence/opportunity refs, employee account, alternative explanation, confirmation status, confirmed_by/at |
| Condition/action | id, case_id, condition, ready/blocked/unknown/not_applicable, rationale, owner, due date, resolution evidence |
| Source | id, case_id, reference, optional recording_id, timestamp or excerpt location, provenance, access restrictions |
| Aid version | id, case_id, version, content, source/rule refs, draft/approved/retired, approved_by/at, review trigger/date |
| Attempt | id, case_id, practice/live, opportunity_id required for live, scenario/input, original response, aid version, actual assistance, submitted_at |
| Review | id, attempt_id, reviewer/at, quality acceptable/unacceptable/unknown, severity, rework, escalation classification/reason, criteria version, feedback, delayed check date/result |
| Conclusion/event | id, case_id, actor/at, previous/new stage or evidence status, rationale, evidence IDs, scope, owner decision; append-only history |

Foreign keys must prevent linking an aid, attempt, source, opportunity, or review from another case. Validate nonnegative minutes and date-window ordering. Missing minutes stay unknown: aggregates show known totals and completeness rather than filling zero. Practice attempts never enter live-work denominators. Record one current accepted review per attempt for aggregation, retaining superseded reviews in history. Reports identify review coverage and unresolved disagreements.

## Proposed API contract

All endpoints below are future work. Existing `/api/recordings` stays compatible.

| Route | Purpose |
| --- | --- |
| `GET/POST /api/cases` | List/create cases |
| `GET/PATCH /api/cases/:id` | Read/update agreement and metadata with expected revision |
| `GET/POST /api/cases/:id/opportunities` | Log all eligible work, including non-escalated items |
| `GET/POST /api/cases/:id/diagnoses` | Record confirmed and competing explanations |
| `GET/POST /api/cases/:id/conditions` | Record readiness and accountable actions |
| `GET/POST /api/cases/:id/sources` | Link approved artifacts and optional recordings |
| `GET/POST /api/cases/:id/aids` | Retrieve/create versioned guidance |
| `POST /api/cases/:id/aids/:aidId/approval` | Named expert approves a specific version |
| `GET/POST /api/cases/:id/attempts` | Practice and actual work records |
| `GET/POST /api/cases/:id/attempts/:attemptId/reviews` | Human reviews and corrections with history |
| `POST /api/cases/:id/transitions` | Gate-checked stage/evidence changes with reason |
| `POST /api/cases/:id/conclusions` | Human conclusion, evidence refs, owner decision |
| `GET /api/cases/:id/report` | Derived metrics with raw counts, denominators, and missingness |
| `GET /api/cases/:id/export` | Portable JSON of permitted case records with schema_version |

Reject invalid fields with 400, unauthorized access with 403, absent resources with 404, stale revisions with 409, and unmet transition gates with 422 plus missing requirements. Validate role and case access server-side. Use database transactions for approval and transitions; reject duplicate submissions using an idempotency key. Exports exclude artifact bytes and secrets and obey the same permissions as reads.

## Evidence and approval rules

- Draft guidance may be edited; approved versions are immutable. AI may propose content but cannot supply expert approval or evidence of actual performance.
- When training is selected, practice readiness requires a reviewed attempt against approved criteria. For a management-only intervention, record why practice is not applicable. Live application always requires authority, essential access, fallback, and the supervisor agreement.
- An observed-independent conclusion requires reviewed real-work evidence without unplanned help, quality checks, and a named reviewer confirming the pre-agreed scope/volume/variety/window. Software checks required evidence exists; the reviewer judges sufficiency.
- A critical error holds live application and requires a new review before resumption. Never auto-advance from viewing a recording, completing a practice count, or achieving a rate.
- For a single internal pilot, restrict the whole service and uploads to authenticated authorized users before storing client evidence. The current recorder's anonymous routes and static upload serving do not meet this requirement. Multi-client use additionally requires tenant isolation and per-case roles; do not infer these from a creator text field.

## AI assistance, later

An optional draft includes source references, proposed rules, uncertain points, and questions for the expert. Treat pasted tickets and transcripts as evidence rather than executable instructions. No model call is needed for the manual workflow. Disclose AI processing and use client-approved data handling before sending private material to an external model.
