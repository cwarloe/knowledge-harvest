#!/usr/bin/env python3
"""Validate and summarize de-identified capability-transfer opportunity records.

This is a local/manual-pilot QA aid, not a client-data service or a competence
decision engine.  Never commit real case records to this public repository.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


CLASSIFICATIONS = {"none", "appropriate", "avoidable", "missed_required", "disputed", "unknown"}
QUALITIES = {"pass", "fail", "unreviewed"}
FIELDS = {
    "id", "escalated", "escalation_class", "quality", "independent",
    "founder_minutes", "other_support_minutes", "critical_error",
}


class InvalidEvidence(ValueError):
    """A record is malformed or makes an unsupported quality assertion."""


def _fraction(numerator: int, denominator: int) -> dict:
    return {
        "numerator": numerator,
        "denominator": denominator,
        "rate": numerator / denominator if denominator else None,
    }


def _minutes(value: object, label: str) -> float | int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise InvalidEvidence(f"{label}: minutes must be nonnegative finite numbers or null")
    return value


def _one_opportunity(record: object, phase: str) -> dict:
    if not isinstance(record, dict) or set(record) != FIELDS:
        raise InvalidEvidence(f"{phase}: opportunity must contain exactly the documented de-identified fields")
    ident = record["id"]
    if not isinstance(ident, str) or not ident or len(ident) > 64 or not ident.replace("-", "").replace("_", "").isalnum():
        raise InvalidEvidence(f"{phase}: opportunity id must be a short opaque identifier")
    escalated = record["escalated"]
    classification = record["escalation_class"]
    quality = record["quality"]
    independent = record["independent"]
    if not isinstance(escalated, bool) or not isinstance(classification, str) or classification not in CLASSIFICATIONS:
        raise InvalidEvidence(f"{phase}/{ident}: invalid escalation data")
    if escalated and classification in {"none", "missed_required"}:
        raise InvalidEvidence(f"{phase}/{ident}: inconsistent escalated/classification")
    if not escalated and classification in {"appropriate", "avoidable"}:
        raise InvalidEvidence(f"{phase}/{ident}: no escalation was recorded")
    if not isinstance(quality, str) or quality not in QUALITIES or (independent is not None and not isinstance(independent, bool)):
        raise InvalidEvidence(f"{phase}/{ident}: invalid review or independence value")
    if quality == "unreviewed" and independent is not None:
        raise InvalidEvidence(f"{phase}/{ident}: unreviewed work cannot assert independence")
    if independent is True and quality != "pass":
        raise InvalidEvidence(f"{phase}/{ident}: independence requires a passing human review")
    if not isinstance(record["critical_error"], bool):
        raise InvalidEvidence(f"{phase}/{ident}: critical_error must be a boolean")
    _minutes(record["founder_minutes"], f"{phase}/{ident}/founder")
    _minutes(record["other_support_minutes"], f"{phase}/{ident}/other")
    return record


def _summarize(phase: str, window: object, scope_id: str) -> dict:
    if not isinstance(window, dict) or set(window) != {"scope_id", "opportunities"}:
        raise InvalidEvidence(f"{phase}: expected scope_id and opportunities")
    if window["scope_id"] != scope_id or not isinstance(window["opportunities"], list):
        raise InvalidEvidence(f"{phase}: scope must match the agreed pilot scope")
    records = [_one_opportunity(item, phase) for item in window["opportunities"]]
    ids = [x["id"] for x in records]
    if len(ids) != len(set(ids)):
        raise InvalidEvidence(f"{phase}: duplicate opportunity id")
    count = len(records)
    escalated = [x for x in records if x["escalated"]]
    reviewed = [x for x in records if x["quality"] != "unreviewed"]
    known_independence = [x for x in reviewed if x["independent"] is not None]
    minutes_report = {}
    for name in ("founder_minutes", "other_support_minutes"):
        known = [x[name] for x in records if x[name] is not None]
        minutes_report[name] = {
            "known_total": sum(known),
            "coverage": _fraction(len(known), count),
            "per_opportunity": sum(known) / count if len(known) == count and count else None,
        }
    both_support_known = all(x["founder_minutes"] is not None and x["other_support_minutes"] is not None for x in records)
    minutes_report["total_support_per_opportunity"] = (
        sum(x["founder_minutes"] + x["other_support_minutes"] for x in records) / count
        if both_support_known and count else None
    )
    return {
        "eligible_opportunities": count,
        "escalated": len(escalated),
        "avoidable_escalations": _fraction(sum(x["escalation_class"] == "avoidable" for x in records), count),
        "missed_required_escalations": _fraction(sum(x["escalation_class"] == "missed_required" for x in records), count),
        "escalation_classification_coverage": _fraction(
            sum(x["escalation_class"] in {"appropriate", "avoidable"} for x in escalated), len(escalated)
        ),
        "quality_review_coverage": _fraction(len(reviewed), count),
        "acceptable_reviewed_outputs": _fraction(sum(x["quality"] == "pass" for x in reviewed), len(reviewed)),
        "independence_review_coverage": _fraction(len(known_independence), len(reviewed)),
        "independent_acceptable_outputs": {
            **_fraction(sum(x["independent"] is True for x in reviewed), len(reviewed)),
            "rate": sum(x["independent"] is True for x in reviewed) / len(reviewed)
            if reviewed and len(known_independence) == len(reviewed) else None,
        },
        "critical_errors": sum(x["critical_error"] for x in records),
        "human_safety_hold_required": any(x["critical_error"] or x["escalation_class"] == "missed_required" for x in records),
        "minutes": minutes_report,
    }


def summarize(data: object) -> dict:
    if not isinstance(data, dict) or set(data) != {"schema_version", "pilot_id", "scope_id", "comparison_review", "windows"}:
        raise InvalidEvidence("expected exactly schema_version, pilot_id, scope_id, comparison_review, windows")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise InvalidEvidence("unsupported schema version")
    for field in ("pilot_id", "scope_id"):
        if not isinstance(data[field], str) or not data[field] or len(data[field]) > 80:
            raise InvalidEvidence(f"{field} must be a nonempty short identifier")
    review = data["comparison_review"]
    if not isinstance(review, dict) or set(review) != {"same_inclusion_rules", "task_mix_reviewed"} or any(type(v) is not bool for v in review.values()):
        raise InvalidEvidence("comparison_review requires two explicit human-reviewed booleans")
    if not isinstance(data["windows"], dict) or set(data["windows"]) != {"baseline", "followup"}:
        raise InvalidEvidence("exactly baseline and followup windows are required")
    windows = {phase: _summarize(phase, data["windows"][phase], data["scope_id"]) for phase in ("baseline", "followup")}
    comparable = (all(review.values()) and all(w["eligible_opportunities"] > 0 for w in windows.values()))
    return {
        "schema_version": 1,
        "pilot_id": data["pilot_id"],
        "scope_id": data["scope_id"],
        "comparison_status": "DESCRIPTIVE_ONLY" if comparable else "NOT_COMPARABLE",
        "comparison_note": "Human-confirmed inclusion and task mix; observed differences are not causal proof" if comparable
        else "No numeric before/after interpretation until human comparability review and nonzero windows",
        "windows": windows,
        "safety_hold_required": any(w["human_safety_hold_required"] for w in windows.values()),
        "competence_and_release_verdict": "HUMAN_REVIEW_REQUIRED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="local JSON evidence summary, never real client data in this repo")
    parser.add_argument("--out", type=Path, help="optional report JSON path; contains only IDs and aggregates")
    parser.add_argument("--check", action="store_true", help="validate without printing full report")
    args = parser.parse_args()
    try:
        report = summarize(json.loads(args.input.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, InvalidEvidence) as exc:
        parser.exit(2, f"INVALID_EVIDENCE: {exc}\n")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.check:
        if report["safety_hold_required"]:
            print("SAFETY_HOLD: A critical error or missed mandatory escalation requires human investigation.")
            return 1
        print("VALIDATION_ONLY: PASS. Human outcome/release review remains required.")
    else:
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
