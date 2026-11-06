"""Evaluation against adjudicated references, with explicit scoring denominators."""

import hashlib
import math
from typing import Any, Self

from pydantic import Field, model_validator

from study_extract.catalog import CATALOG
from study_extract.evidence import normalized, quote_status
from study_extract.models import Extraction, Kind, Packet, Scalar, State, StrictModel

MATCH_ANCHORS = {
    "study": {"title", "setting", "research_question"},
    "design": {"estimand", "target_population", "treatment", "comparison", "assignment_unit"},
    "sample": {"population", "geography", "period", "observation_unit"},
    "outcome": {"name", "construct", "timepoint", "instrument", "data_source"},
    "estimate": {
        "outcome",
        "estimand",
        "population",
        "contrast",
        "timepoint",
        "specification",
        "measure",
    },
    "diagnostic": {"assumption", "diagnostic_type", "procedure", "sample", "null_hypothesis"},
    "claim": {"text", "claim_type", "mechanism", "scope"},
    "comparison": {"quantity", "observed_scope", "benchmark_scope", "benchmark_source"},
}


class ExpectedCell(StrictModel):
    state: State
    value: Scalar | None
    accepted_values: list[Scalar] = Field(default_factory=list)
    absolute_tolerance: float = Field(default=0, ge=0)
    evidence_pages: list[int] = Field(default_factory=list)
    adjudicated: bool = False
    reviewer: str | None = None
    rationale: str | None = None

    @model_validator(mode="after")
    def reviewed(self) -> Self:
        if self.adjudicated and (not self.reviewer or not self.rationale):
            raise ValueError("Adjudicated references need reviewer and rationale")
        if (self.state == "present") != (self.value is not None):
            raise ValueError("Reference state and value disagree")
        return self


class ReferenceRecord(StrictModel):
    reference_id: str
    study_id: str
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    kind: Kind
    anchors: dict[str, list[Scalar]] = Field(min_length=1)
    expected: dict[str, ExpectedCell] = Field(min_length=1)
    origin: "ReferenceOrigin | None" = None

    @model_validator(mode="after")
    def validate_fields_and_anchors(self) -> Self:
        for name, choices in self.anchors.items():
            spec = CATALOG[self.kind].get(name)
            if (
                name not in MATCH_ANCHORS[self.kind]
                or not spec
                or spec.type != "text"
                or not choices
            ):
                raise ValueError("Match anchors must be nonempty descriptive text fields")
            if any(not isinstance(v, str) or not v.strip() for v in choices):
                raise ValueError("Anchor choices must be nonempty text")
            if name in self.expected:
                raise ValueError("Scored target fields cannot be used as matching anchors")
        for name, expected in self.expected.items():
            spec = CATALOG[self.kind].get(name)
            if spec is None:
                raise ValueError(f"Unknown reference field: {name}")
            if expected.state != "present" and expected.accepted_values:
                raise ValueError("Missing references cannot have alternative present values")
            for value in [expected.value, *expected.accepted_values]:
                if value is None:
                    continue
                valid = {
                    "text": isinstance(value, str),
                    "number": type(value) in (int, float),
                    "integer": type(value) is int,
                    "boolean": type(value) is bool,
                    "text_list": isinstance(value, list),
                }[spec.type]
                if not valid:
                    raise ValueError(f"Reference {name} requires {spec.type}")
        return self


class ReferenceOrigin(StrictModel):
    artifact: str
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    pointer: str
    version: str


class ReferenceSet(StrictModel):
    records: list[ReferenceRecord]
    complete_scopes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_ids(self) -> Self:
        ids = [r.reference_id for r in self.records]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate reference IDs")
        return self


def same_value(left: Scalar | None, right: Scalar | None, tolerance: float = 0) -> bool:
    if type(left) in (int, float) and type(right) in (int, float):
        return math.isclose(float(left), float(right), rel_tol=0, abs_tol=tolerance)  # type: ignore[arg-type]
    if isinstance(left, str) and isinstance(right, str):
        return normalized(left).casefold() == normalized(right).casefold()
    return type(left) is type(right) and left == right


def split_for_study(study_id: str, seed: str = "study-extract-v1") -> str:
    bucket = int(hashlib.sha256(f"{seed}:{study_id}".encode()).hexdigest()[:8], 16) % 10
    return "test" if bucket < 2 else "dev" if bucket < 4 else "train"


def evaluate(predictions: Extraction, references: ReferenceSet, packet: Packet) -> dict[str, Any]:
    docs = {doc.source_id: doc for doc in packet.documents}
    rows: list[dict[str, Any]] = []
    matched_ids: set[str] = set()
    eligible_records = matched_records = 0
    correct = scored = evidence_correct = evidence_scored = 0
    abstentions = false_present = unreviewed = ambiguous = 0
    candidate_map: dict[str, list[Any]] = {}
    for ref in references.records:
        if not any(cell.adjudicated for cell in ref.expected.values()):
            candidate_map[ref.reference_id] = []
            continue
        candidates = [
            p
            for p in predictions.records
            if p.study_id == ref.study_id
            and p.kind == ref.kind
            and p.source_id in docs
            and docs[p.source_id].sha256 == ref.source_sha256
            and all(
                name in p.fields
                and p.fields[name].state == "present"
                and any(same_value(p.fields[name].value, v) for v in allowed)
                for name, allowed in ref.anchors.items()
            )
        ]
        candidate_map[ref.reference_id] = candidates
    uses: dict[str, int] = {}
    for candidates in candidate_map.values():
        for p in candidates:
            uses[p.record_id] = uses.get(p.record_id, 0) + 1
    for ref in references.records:
        reviewed = {k: v for k, v in ref.expected.items() if v.adjudicated}
        unreviewed += len(ref.expected) - len(reviewed)
        if not reviewed:
            continue
        eligible_records += 1
        candidates = candidate_map[ref.reference_id]
        unique = len(candidates) == 1 and uses[candidates[0].record_id] == 1
        prediction = candidates[0] if unique else None
        if candidates and not unique:
            ambiguous += 1
        if prediction:
            matched_records += 1
            matched_ids.add(prediction.record_id)
        for field, gold in reviewed.items():
            scored += 1
            cell = prediction.fields.get(field) if prediction else None
            state_ok = cell is not None and cell.state == gold.state
            value_ok = cell is not None and any(
                same_value(cell.value, v, gold.absolute_tolerance)
                for v in [gold.value, *gold.accepted_values]
            )
            ok = state_ok and value_ok
            correct += ok
            if gold.state == "present" and (cell is None or cell.state != "present"):
                abstentions += 1
            if gold.state != "present" and cell and cell.state == "present":
                false_present += 1
            evidence_ok = None
            if gold.state == "present" and gold.evidence_pages:
                evidence_scored += 1
                evidence_ok = bool(
                    prediction
                    and cell
                    and cell.evidence
                    and all(
                        quote_status(ev, packet) == "located"
                        and ev.source_id == prediction.source_id
                        for ev in cell.evidence
                    )
                    and any(ev.pdf_page in gold.evidence_pages for ev in cell.evidence)
                )
                evidence_correct += evidence_ok
            rows.append(
                {
                    "reference_id": ref.reference_id,
                    "study_id": ref.study_id,
                    "field": field,
                    "correct": ok,
                    "evidence_location_correct": evidence_ok,
                    "record_match": "unique"
                    if unique
                    else "ambiguous"
                    if candidates
                    else "missing",
                }
            )
    scoped_extras = [
        p.record_id
        for p in predictions.records
        if p.source_id in docs
        and p.record_id not in matched_ids
        and f"{docs[p.source_id].sha256}:{p.kind}" in references.complete_scopes
    ]
    by_study: dict[str, dict[str, int]] = {}
    for row in rows:
        counts = by_study.setdefault(row["study_id"], {"correct": 0, "scored": 0})
        counts["correct"] += row["correct"]
        counts["scored"] += 1
    macro = (
        sum(v["correct"] / v["scored"] for v in by_study.values()) / len(by_study)
        if by_study
        else None
    )
    return {
        "eligible_reference_records": eligible_records,
        "matched_records": matched_records,
        "record_recall": matched_records / eligible_records if eligible_records else None,
        "correct_cells": correct,
        "scored_cells": scored,
        "cell_accuracy": correct / scored if scored else None,
        "macro_study_accuracy": macro,
        "unadjudicated_cells_excluded": unreviewed,
        "evidence_location_correct": evidence_correct,
        "evidence_location_scored": evidence_scored,
        "evidence_location_accuracy": evidence_correct / evidence_scored
        if evidence_scored
        else None,
        "semantic_support_accuracy": None,
        "missed_present_cells": abstentions,
        "unsupported_present_against_reviewed_missing": false_present,
        "ambiguous_record_matches": ambiguous,
        "extras_in_complete_scopes": scoped_extras,
        "unscored_prediction_records": len(predictions.records) - len(matched_ids),
        "by_study": by_study,
        "cells": rows,
    }
