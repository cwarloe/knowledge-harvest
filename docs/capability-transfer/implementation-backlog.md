# Implementation backlog

Framework delivered: documentation, reusable workbook, fictional case, evidence rules, and product specification. Application slices below remain **not implemented**. Sequence by demonstrated pilot need rather than dates or automatic infrastructure expansion.

| Order | Slice | Acceptance checks | Dependency |
| --- | --- | --- | --- |
| 0 | Run a manual pilot in an approved private workspace | One signed agreement, baseline covering all eligible opportunities, confirmed diagnosis, reviewed live evidence or explicit insufficient-evidence outcome; delivery effort recorded | Suitable owner, employee, expert and task |
| 1 | Case records and escalation log | Create/reload case; capture non-escalations; preserve unknown minutes; edit with revision conflicts; link existing recording optionally | Product spec agreed |
| 2 | Diagnosis, conditions and results record | Confirm multiple causes; assign blockers; show raw counts/denominators and missing reviews; record human conclusion; export/reimport losslessly | Slice 1 |
| 3 | Private pilot access | Unauthorized requests cannot read/write case records or recording bytes; restrict static uploads; authorize exports/deletes; migration backup and restore verified | Required before any real client data enters app |
| 4 | Expert capture and approved aids | Link sources; preserve conflicting rules; version/approve aids; edits do not overwrite approved content or past attempts | Slices 1–3 |
| 5 | Practice and application agreements | Fresh cases; original responses preserved; assistance visible; missing authority/access blocks live transition; recovery and next opportunity recorded | Slice 4 |
| 6 | Follow-up and evidence workflow | Critical error holds application; delayed reviews visible; practice cannot count as independence; reviewer accepts scope and evidence before conclusion | Slice 5 |
| 7 | Optional AI draft assistance | Expert can accept/reject sourced suggestions; unsupported claims flagged; model cannot approve guidance or award independence | Repeated manual bottleneck demonstrated |

Slices 1–2 should be developed with fictional data. Slice 3 must precede a software-based client pilot, regardless of whether later features are ready. Keep manual delivery available throughout.

## Integration work

- Extract new Case components from the recorder UI boundary; avoid adding the whole workflow to `App.js`.
- Add additive migrations under a documented migration runner; do not recreate or truncate `recordings` or reuse the sample-seeding schema as an upgrade script.
- Add case API routes/modules to the current Express service. Retain recording routes and local-file behavior until storage migration is independently justified.
- Introduce foreign keys and transactions for related evidence. Back up records and upload files together before migration; verify rollback on a copied database.
- Apply [measurement definitions](measurement.md) consistently in UI, API reports, and exports.

## Meaningful verification when implementation begins

1. Ten eligible items with four avoidable escalations report 4/10, not 4 divided by escalations only.
2. Zero opportunities yields not available; missing quality reviews or minutes remain unknown with completeness shown.
3. Practice-only evidence cannot support observed-independent status.
4. Approved aid edits create a new draft; past attempts retain the exact old version.
5. A stale revision cannot overwrite a newer agreement or review.
6. A linked aid or review belonging to a different case is rejected.
7. Reduced founder time accompanied by increased total support or critical errors remains visible.
8. Missing authority/access prevents live application; a recorded critical error holds it until reviewed.
9. Private data, recordings, exports, and deletions all require authorized access.
10. Migration preserves existing recordings; existing browse, upload, and playback behavior still works, and the unauthenticated `DELETE /api/recordings/:id` route still works if it remains part of the API.

These are implementation acceptance scenarios, not claims that tests or features already exist.

## What would change the plan

If the manual pilot finds authority or capacity dominates, prioritize condition/action follow-through over content generation. If expert elicitation is the costly bottleneck, improve guided capture. If outcome evidence is unavailable, fix the evidence workflow before building a dashboard. Scale the product only when repeated cases reveal repeatable delivery steps and credible customer value.
