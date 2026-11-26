# Capability-transfer metrics canary

**Purpose:** keep the pilot's arithmetic and evidence rules consistent as agents
work on engagement templates and later product slices. This is a **local,
de-identified fixture and validator**, not a live client-data workflow.

## Run it

From the repository root, with Python 3.10 or newer:

```bash
python3 tools/capability_transfer_metrics.py --input docs/capability-transfer/metrics-fixture.json
python3 -m unittest discover -s tools/tests -p 'test_capability_transfer_metrics.py' -v
```

The fictional fixture is an expanded, anonymous teaching example corresponding
to the ten baseline and ten follow-up opportunities described in
[`example-msp.md`](example-msp.md). It is **not** customer evidence. CI runs the
tests and fixture preflight without touching storage or making external calls.

## What one record means

- `id`: opaque, local opportunity ID, not an employee/client/ticket name.
- `escalated`: whether the case was escalated to a founder/expert.
- `escalation_class`: `none`, `appropriate`, `avoidable`, `missed_required`,
  `disputed`, or `unknown` after human classification. `missed_required` is
  necessarily a non-escalated case.
- `quality`: `pass`, `fail`, or `unreviewed`, using the pre-agreed task standard.
- `independent`: `true`, `false`, or `null` if not assessed. `true` is only
  permitted for a reviewed, passing output. Correct mandatory escalation can be
  an independent decision within the employee's authority; document that
  boundary in the private workbook.
- `founder_minutes`, `other_support_minutes`: nonnegative number or `null` if
  unknown. Zero is a measured zero, **not** a default for missing time.
- `critical_error`: human-recorded boolean; either this or `missed_required`
  raises a safety hold, without automatically making any release decision.

There must be a row for **every eligible opportunity**, not just escalations.
Keep `scope_id` identical between windows. `comparison_review` has two explicit
human judgments: same inclusion rules and task mix reviewed; if either is false,
the program declines a before/after interpretation. Even a comparable output
is **descriptive only**, not causal proof.

The report includes denominators, classification/review coverage, missing
independence, founder and other-support minutes separately, and a combined
burden only when **both** time fields are fully observed. No zero denominator
becomes 0%, no unreviewed work becomes a pass, and the output always says
`HUMAN_REVIEW_REQUIRED` for competence/release.

In `--check` mode a syntactically valid record with a critical error or a
missed mandatory escalation still exits nonzero (`SAFETY_HOLD`), requiring
human investigation. A successful check means the *arithmetic fixture* is
valid, not that an employee or intervention has been approved.

## Boundaries and next use

This repository is public. **Do not put real customer, employee, recording,
ticket, contract, interview, or other client evidence into this repo or this
fixture.** The validator rejects arbitrary extra row fields but it is not a
privacy control or authorized record store; even IDs can be sensitive. Use the
private approved pilot workbook and client retention rules for real engagements.

Product slices 1–3 in the [implementation backlog](implementation-backlog.md)
still need the actual record, access and security work. The current recorder's
client-data permissions have **not** been repaired or changed by this canary.
No real pilot conclusion, autonomous employee certification, customer outreach
or service launch is authorized by a green metrics check.
