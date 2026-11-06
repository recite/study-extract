import copy

import pytest
from pydantic import ValidationError

from study_extract.evidence import quote_status, verify
from study_extract.models import Cell, Extraction, Packet, calculate


@pytest.mark.parametrize(
    "data",
    [
        {"value": 4, "state": "not_found", "rationale": "not located"},
        {"value": None, "state": "present"},
        {"value": 4, "state": "present"},
        {"value": None, "state": "not_found"},
        {"value": None, "state": "conflicting", "rationale": "two claims"},
        {"value": float("nan"), "state": "present"},
    ],
)
def test_rejects_unsupported_or_incoherent_cells(data):
    with pytest.raises(ValidationError):
        Cell.model_validate(data)


def test_exact_evidence_is_located_not_certified(extraction, packet):
    report = verify(extraction, packet)
    assert report["valid_locations"]
    assert report["evidence_checked"] == 3
    assert report["semantic_support_accuracy"] is None
    assert all(f["code"] == "support_unreviewed" for f in report["findings"])


@pytest.mark.parametrize(
    "field,value,code",
    [
        ("pdf_page", 20, "invalid_page"),
        ("quote", "Treatment effect 0.20", "quote_not_found"),
        ("source_id", "wrong", "unknown_source"),
        ("quote", "   ", "empty_quote"),
    ],
)
def test_citations_cannot_hide_wrong_sign_or_page(extraction, packet, field, value, code):
    evidence = extraction.records[0].fields["value"].evidence[0].model_copy(update={field: value})
    assert quote_status(evidence, packet) == code


def test_page_hash_is_checked(extraction, packet):
    packet.documents[0].pages[0].text += "tampering"
    assert not verify(extraction, packet)["valid_locations"]


def test_missing_page_coverage_fails(extraction, packet):
    extraction.coverage[0].pages_read = [1]
    assert not verify(extraction, packet)["valid_locations"]


def test_unreadable_pages_cannot_be_claimed_read(extraction, packet):
    packet.documents[0].pages[1].needs_ocr = True
    assert not verify(extraction, packet)["valid_locations"]


def test_other_version_is_not_accepted(extraction, packet):
    other = packet.documents[0].model_copy(update={"source_id": "other-version", "version": "v2"})
    packet = Packet(documents=[*packet.documents, other])
    extraction.records[0].fields["value"].evidence[0].source_id = "other-version"
    report = verify(extraction, packet)
    assert "wrong_document_version" in [f["code"] for f in report["findings"]]


def test_duplicate_records_and_cross_family_links_fail(extraction):
    data = extraction.model_dump()
    data["records"].append(copy.deepcopy(data["records"][0]))
    with pytest.raises(ValidationError, match="Duplicate"):
        Extraction.model_validate(data)
    data["records"][1]["record_id"] = "other"
    data["records"][1]["study_id"] = "other-study"
    data["records"][0]["links"] = [{"relation": "supports", "record_id": "other"}]
    with pytest.raises(ValidationError, match="study family"):
        Extraction.model_validate(data)


@pytest.mark.parametrize("wrong_version", [False, True])
def test_links_reject_wrong_kind_and_version(extraction, wrong_version):
    data = extraction.model_dump()
    other = copy.deepcopy(data["records"][0])
    other["record_id"] = "other"
    if wrong_version:
        other["source_id"] = "different-version"
    data["records"].append(other)
    data["records"][0]["links"] = [{"relation": "outcome", "record_id": "other"}]
    with pytest.raises(ValidationError, match="document version|target kind"):
        Extraction.model_validate(data)


def test_derivation_rejects_another_document_version(extraction):
    data = extraction.model_dump()
    first = data["records"][0]
    other = copy.deepcopy(first)
    other["record_id"] = "other"
    other["source_id"] = "different-version"
    other["fields"]["test_statistic"] = {
        "state": "present",
        "value": -2.5,
        "basis": "derived",
        "derivation": {
            "operation": "z_from_estimate_se",
            "assumptions": "ratio only",
            "inputs": [
                {"record_id": first["record_id"], "field": "value"},
                {"record_id": first["record_id"], "field": "standard_error"},
            ],
        },
    }
    data["records"].append(other)
    with pytest.raises(ValidationError, match="document version"):
        Extraction.model_validate(data)


def test_duplicate_page_coverage_rejected(extraction, packet):
    extraction.coverage[0].pages_read = [1, 1, 2]
    assert not verify(extraction, packet)["valid_locations"]


def test_arithmetic_is_recomputed(extraction):
    data = extraction.model_dump()
    record = data["records"][0]
    record["fields"]["test_statistic"] = {
        "value": -2.5,
        "state": "present",
        "basis": "derived",
        "evidence": [],
        "derivation": {
            "operation": "z_from_estimate_se",
            "assumptions": "Ratio only, not a p-value",
            "inputs": [
                {"record_id": record["record_id"], "field": "value"},
                {"record_id": record["record_id"], "field": "standard_error"},
            ],
        },
    }
    assert Extraction.model_validate(data)
    record["fields"]["test_statistic"]["value"] = 2.5
    with pytest.raises(ValidationError, match="disagrees"):
        Extraction.model_validate(data)


@pytest.mark.parametrize(
    "operation,values",
    [("ratio", [1, 0]), ("difference", [1]), ("z_from_estimate_se", [1, -1]), ("eval", [1, 2])],
)
def test_invalid_computation_fails(operation, values):
    with pytest.raises(ValueError):
        calculate(operation, values)


@pytest.mark.parametrize(
    "field,value",
    [
        ("standard_error", -0.2),
        ("value", "-0.2"),
        ("n_observations", True),
        ("n_clusters", -1),
        ("interval_level", 95),
        ("made_up", 1),
    ],
)
def test_wrong_field_types_or_ranges_fail(extraction, field, value):
    data = extraction.model_dump()
    cell = copy.deepcopy(data["records"][0]["fields"]["value"])
    cell["value"] = value
    data["records"][0]["fields"][field] = cell
    with pytest.raises(ValidationError):
        Extraction.model_validate(data)
