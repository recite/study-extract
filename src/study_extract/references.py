"""Import existing annotations as provisional evidence, never automatic gold."""

import csv
from pathlib import Path
from typing import Any

import yaml

from study_extract.io import read_json, sha256


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
