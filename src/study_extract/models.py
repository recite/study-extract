"""Validated records. Evidence location and semantic support are separate checks."""

import math
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from study_extract.catalog import CATALOG

Scalar = str | int | float | bool | list[str]
State = Literal["present", "not_found", "not_applicable", "unreadable", "conflicting"]
Kind = Literal[
    "study", "design", "sample", "outcome", "estimate", "diagnostic", "claim", "comparison"
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class Evidence(StrictModel):
    source_id: str = Field(min_length=1)
    pdf_page: int = Field(ge=1)
    quote: str = Field(min_length=1)
    role: Literal["value", "row_label", "column_label", "footnote", "context"] = "context"
    printed_page: str | None = None
    table: str | None = None
    row: str | None = None
    column: str | None = None


class CellRef(StrictModel):
    record_id: str
    field: str


class Derivation(StrictModel):
    operation: Literal["difference", "ratio", "percent_to_proportion", "z_from_estimate_se"]
    inputs: list[CellRef] = Field(min_length=1)
    assumptions: str = Field(min_length=1)


class Cell(StrictModel):
    value: Scalar | None
    state: State
    basis: Literal["reported", "derived", "reviewer_judgment"] = "reported"
    evidence: list[Evidence] = Field(default_factory=list)
    rationale: str | None = None
    derivation: Derivation | None = None

    @model_validator(mode="after")
    def coherent(self) -> Self:
        if self.state == "present":
            if self.value is None:
                raise ValueError("A present cell needs a value")
            if isinstance(self.value, str) and not self.value.strip():
                raise ValueError("Empty text is not an observed value")
            if self.basis == "derived":
                if self.derivation is None:
                    raise ValueError("Derived cells need a derivation")
            elif not self.evidence:
                raise ValueError("Reported/judgment values need evidence")
        else:
            if self.value is not None:
                raise ValueError("Missing/conflicting cells must have null values")
            if not self.rationale:
                raise ValueError("Missing/conflicting cells need a rationale")
            if self.state == "conflicting" and len(self.evidence) < 2:
                raise ValueError("Conflicting cells need both passages")
        if self.basis == "reviewer_judgment" and not self.rationale:
            raise ValueError("Judgments need an explicit rationale")
        if self.basis != "derived" and self.derivation is not None:
            raise ValueError("Only derived cells can carry a derivation")
        return self


class Link(StrictModel):
    relation: Literal["outcome", "sample", "design", "supports", "contradicts", "same_quantity"]
    record_id: str


class Record(StrictModel):
    record_id: str = Field(min_length=1)
    study_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    kind: Kind
    fields: dict[str, Cell] = Field(min_length=1)
    links: list[Link] = Field(default_factory=list)

    @model_validator(mode="after")
    def known_fields(self) -> Self:
        for key, cell in self.fields.items():
            spec = CATALOG[self.kind].get(key)
            if spec is None:
                raise ValueError(f"Unknown {self.kind} field: {key}")
            if cell.state != "present":
                continue
            value = cell.value
            valid = {
                "text": isinstance(value, str),
                "number": type(value) in (int, float),
                "integer": type(value) is int,
                "boolean": type(value) is bool,
                "text_list": isinstance(value, list),
            }[spec.type]
            if not valid:
                raise ValueError(f"{self.kind}.{key} requires {spec.type}")
            if spec.type == "integer" and isinstance(value, int) and value < 0:
                raise ValueError(f"{key} must be nonnegative")
            if key in ("standard_error", "standard_deviation", "control_sd"):
                if isinstance(value, (int, float)) and value < 0:
                    raise ValueError(f"{key} must be nonnegative")
            if key == "interval_level" and isinstance(value, (int, float)):
                if not 0 < value < 1:
                    raise ValueError("interval_level must be a fraction between 0 and 1")
        lo = self.fields.get("interval_lower")
        hi = self.fields.get("interval_upper")
        if lo and hi and lo.state == hi.state == "present":
            if isinstance(lo.value, (int, float)) and isinstance(hi.value, (int, float)):
                if lo.value > hi.value:
                    raise ValueError("Interval endpoints are reversed")
        return self


class Coverage(StrictModel):
    source_id: str
    pages_read: list[int]
    unreadable_pages: list[int]
    missing_materials: list[str]
    scope: str = Field(min_length=1)
    exhaustive: Literal[False] = False


class Extraction(StrictModel):
    schema_version: Literal["0.1.0"] = "0.1.0"
    records: list[Record]
    coverage: list[Coverage]

    @model_validator(mode="after")
    def references(self) -> Self:
        records = {r.record_id: r for r in self.records}
        if len(records) != len(self.records):
            raise ValueError("Duplicate record IDs")
        cells = {(r.record_id, f): c for r in self.records for f, c in r.fields.items()}
        for record in self.records:
            for link in record.links:
                target = records.get(link.record_id)
                if target is None or target.study_id != record.study_id:
                    raise ValueError("Links must resolve within the study family")
                if target.source_id != record.source_id:
                    raise ValueError("Links must remain within the document version")
                if link.relation in ("outcome", "sample", "design"):
                    if target.kind != link.relation:
                        raise ValueError("Link target kind disagrees with its relation")
            for cell in record.fields.values():
                if cell.derivation:
                    values: list[float] = []
                    for ref in cell.derivation.inputs:
                        source = cells.get((ref.record_id, ref.field))
                        if source is None or records[ref.record_id].study_id != record.study_id:
                            raise ValueError("Derivation input is missing or from another study")
                        if records[ref.record_id].source_id != record.source_id:
                            raise ValueError("Derivations must remain within the document version")
                        if source.basis != "reported" or source.state != "present":
                            raise ValueError("Derivations currently require reported input cells")
                        if isinstance(source.value, bool) or not isinstance(
                            source.value, (int, float)
                        ):
                            raise ValueError("Derivation input must be numeric")
                        values.append(float(source.value))
                    expected = calculate(cell.derivation.operation, values)
                    if isinstance(cell.value, bool) or not isinstance(cell.value, (int, float)):
                        raise ValueError("Derived value must be numeric")
                    if not math.isclose(cell.value, expected, rel_tol=1e-9, abs_tol=1e-12):
                        raise ValueError("Derived value disagrees with its recorded computation")
        return self


def calculate(operation: str, values: list[float]) -> float:
    expected_length = 1 if operation == "percent_to_proportion" else 2
    if len(values) != expected_length:
        raise ValueError("Wrong number of derivation inputs")
    if operation == "difference":
        return values[0] - values[1]
    if operation in ("ratio", "z_from_estimate_se"):
        if values[1] == 0 or (operation == "z_from_estimate_se" and values[1] < 0):
            raise ValueError("Invalid denominator")
        return values[0] / values[1]
    if operation == "percent_to_proportion":
        return values[0] / 100
    raise ValueError(f"Unknown operation: {operation}")


class Page(StrictModel):
    number: int = Field(ge=1)
    text: str
    text_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    needs_ocr: bool
    extraction_warnings: list[str] = Field(default_factory=list)


class Document(StrictModel):
    source_id: str
    study_id: str
    version: str
    filename: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    parser: str
    pages: list[Page] = Field(min_length=1)


class Packet(StrictModel):
    documents: list[Document] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_sources(self) -> Self:
        ids = [doc.source_id for doc in self.documents]
        if len(set(ids)) != len(ids):
            raise ValueError("Duplicate source IDs")
        for doc in self.documents:
            if [page.number for page in doc.pages] != list(range(1, len(doc.pages) + 1)):
                raise ValueError("Pages must be contiguous and one-based")
        return self
