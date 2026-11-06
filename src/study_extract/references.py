"""Import existing annotations as provisional evidence, never automatic gold."""

import csv
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field

from study_extract.evaluate import ExpectedCell, ReferenceOrigin, ReferenceRecord, ReferenceSet
from study_extract.io import read_json, sha256
from study_extract.models import Document, Scalar, StrictModel


class EstimateMapping(StrictModel):
    index: int = Field(ge=0)
    anchors: dict[str, list[Scalar]] = Field(min_length=1)


def import_estimates(
    coding: Path, document: Document, version: str, mappings: list[EstimateMapping]
) -> ReferenceSet:
    """Convert explicitly mapped quota coding rows into unadjudicated references."""
    raw = coding.read_bytes()
    annotation = yaml.safe_load(raw)
    if not isinstance(annotation, dict) or annotation.get("key") != document.study_id:
        raise ValueError("Coding study key does not match the document study family")
    versions = [v for v in annotation.get("versions", []) if v.get("id") == version]
    if len(versions) != 1 or versions[0].get("file") != document.filename:
        raise ValueError("Coding version does not identify this document filename")
    estimates = annotation.get("estimates", [])
    references = []
    for mapping in mappings:
        if mapping.index >= len(estimates):
            raise ValueError("Mapped estimate index is outside the coding file")
        entry = estimates[mapping.index]
        if entry.get("version") != version:
            raise ValueError("Mapped estimate belongs to another document version")
        expected = {}
        for old, new in [("diff", "value"), ("se", "standard_error"), ("n_obs", "n_observations")]:
            value = entry.get(old)
            if value is not None:
                expected[new] = ExpectedCell(state="present", value=value)
        if not expected:
            raise ValueError("Mapped estimate contains no numeric reference values")
        references.append(
            ReferenceRecord(
                reference_id=f"{document.study_id}:{version}:estimate-{mapping.index}",
                study_id=document.study_id,
                source_sha256=document.sha256,
                kind="estimate",
                anchors=mapping.anchors,
                expected=expected,
                origin=ReferenceOrigin(
                    artifact=str(coding.resolve()),
                    artifact_sha256=sha256(raw),
                    pointer=f"/estimates/{mapping.index}",
                    version=version,
                ),
            )
        )
    if not references:
        raise ValueError("Provide at least one explicit estimate mapping")
    return ReferenceSet(records=references)


def reference_inventory(
    quota_spending: Path, quota_assignment: Path, face_of_crime: Path
) -> dict[str, Any]:
    items = []
    for path in sorted((quota_spending / "lit/coding").glob("*.yaml")):
        data = path.read_bytes()
        annotation = yaml.safe_load(data)
        sources = []
        for version in annotation.get("versions", []):
            pdf = quota_spending / "lit/papers" / version["file"]
            sources.append(
                {
                    "path": str(pdf),
                    "exists": pdf.exists(),
                    "sha256": sha256(pdf.read_bytes()) if pdf.exists() else None,
                    "version": version,
                }
            )
        items.append(
            {
                "domain": "quota_spending",
                "reference_path": str(path),
                "reference_sha256": sha256(data),
                "adjudicated": False,
                "sources": sources,
                "annotation": annotation,
            }
        )
    for name in ["literature_a.json", "literature_b.json", "legal_and_external.json"]:
        path = quota_assignment / "data/reference/assignment_claims" / name
        items.append(
            {
                "domain": "quota_assignment",
                "reference_path": str(path),
                "reference_sha256": sha256(path.read_bytes()),
                "adjudicated": False,
                "annotation": read_json(path),
            }
        )
    for path in sorted((quota_assignment / "data/reference/literature_audit").glob("*.csv")):
        with path.open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        items.append(
            {
                "domain": "quota_assignment",
                "reference_path": str(path),
                "reference_sha256": sha256(path.read_bytes()),
                "adjudicated": False,
                "annotation": rows,
            }
        )
    path = face_of_crime / "data/reference/literature.csv"
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    items.append(
        {
            "domain": "face_of_crime",
            "reference_path": str(path),
            "reference_sha256": sha256(path.read_bytes()),
            "adjudicated": False,
            "annotation": rows,
        }
    )
    return {
        "status": "provisional_inventory",
        "items": items,
        "warning": "Existing annotations are not adjudicated gold; no absent-test labels inferred.",
    }
