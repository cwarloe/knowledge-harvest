# Capability Transfer Framework

Version 0.1 · November 6, 2026 · Pilot design, not a validated assessment instrument.

**Help an employee handle one defined class of work accurately, with less unnecessary founder intervention.**

This framework operationalizes [Knowledge Harvest's business hypothesis](../business-hypothesis.md). It can be delivered manually before the software is extended. The current app records, stores, and retrieves recordings; the four-screen case workflow below is specified, not implemented.

## Start a pilot

1. Copy the [pilot workbook](pilot-workbook.md) into an approved private client workspace. The public repo contains blank templates and fictional examples only.
2. Read the [fictional MSP example](example-msp.md) to see a completed case.
3. Agree on one recurring dependency, its boundaries, the people involved, the evidence window, and quality requirements.
4. Run the workflow below. Use [measurement rules](measurement.md) for baseline and follow-up.
5. Record whether to continue, revise, pause, or stop. Capture delivery effort and buyer feedback as well as employee results.

## Workflow and decision gates

| Stage | Produce | Gate to advance | Accountable person |
| --- | --- | --- | --- |
| Find | Defined task, incident log, baseline, quality standard | Owner confirms a recurring, economically meaningful dependency and access to evidence | Pilot lead + business owner |
| Diagnose | Confirmed causes and intervention choices | Employee and owner review evidence; unresolved authority/resource barriers have owners | Pilot lead |
| Harvest | Contrasting cases, cues, reasoning, exception boundaries | Expert validates the accuracy and limits of the extracted rules | Expert |
| Prepare | Versioned decision aid and unfamiliar practice cases | Expert approves aid and expected reasoning; employee demonstrates practice readiness | Expert + reviewer |
| Apply | Agreed authority, real opportunity, support, review date | Blocking work conditions resolved or live work held; employee knows when to escalate | Supervisor |
| Prove | Reviewed live work, comparable measures, limitations, next decision | Human reviewer accepts scope-limited conclusion; no automatic competence award | Business owner + reviewer |

Stages can loop. A live-work failure can return to diagnosis or invalidate an aid. A resource or decision-rights problem may go directly from diagnosis to a management intervention, without creating training content.

## Roles

- **Business owner:** chooses the business outcome, approves decision rights and investment, accepts the pilot conclusion.
- **Employee:** contributes their explanation, attempts practice/live work, records barriers and assistance.
- **Expert:** explains actual decisions, approves guidance and escalation limits.
- **Supervisor:** makes opportunity, time, access, feedback, and expectations concrete.
- **Pilot lead/reviewer:** maintains evidence and reviews performance against the agreed standard. One person may hold multiple roles; record that limitation when the founder is also the reviewer.

## Framework pack

- [Pilot workbook](pilot-workbook.md): reusable records for the complete engagement.
- [Diagnosis and transfer conditions](diagnosis.md): distinguish capability from other barriers.
- [Measurement and evidence](measurement.md): operational definitions and decision rules.
- [Worked MSP example](example-msp.md): fictional decisions and numbers, including a failed attempt.
- [Product specification](product-spec.md): four screens, domain model, API contract, review rules.
- [Implementation backlog](implementation-backlog.md): sequenced slices and acceptance checks.
- [Sources and design rationale](sources.md): external framework attribution and limits.

## Pilot boundaries

Choose a frequent, bounded task with reviewable outputs and reversible decisions. Agree a fallback route for uncertain cases. Never optimize for zero escalations: recognizing when to ask for help is part of the capability. No recordings watched, AI judgments, practice completions, or elapsed time automatically establish workplace independence.

Store real tickets, contracts, recordings, employee records, and customer information only in the client's approved private environment. Use redacted references in reports. The present development app has public upload routes and no demonstrated client access controls; it is not the place for sensitive client evidence yet.
