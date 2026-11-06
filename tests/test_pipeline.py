import csv
import json
import logging
from pathlib import Path

import pypdf
import pytest
from jsonschema import Draft202012Validator, ValidationError

from study_extract.agent import prepare, run_batch
from study_extract.catalog import CATALOG
from study_extract.cli import main
from study_extract.export import export_csv, review_html
from study_extract.ingest import ingest_document, ingest_manifest
from study_extract.io import read_json, write_json
from study_extract.models import Cell, Extraction, Packet
from study_extract.schema import response_schema


class FixtureBackend:
    identity = "synthetic-fixture-v1"

    def __init__(self, extraction):
        self.extraction = extraction
        self.calls = 0

    def run(self, directory: Path, timeout: float):
        self.calls += 1
        write_json(directory / "response.json", self.extraction)


def complete_profile(extraction):
    for record in extraction.records:
        for field in CATALOG[record.kind]:
            record.fields.setdefault(
                field, Cell(value=None, state="not_found", rationale="fixture")
            )
    return extraction


def test_ingest_hash_pages_and_manifest(tmp_path):
    source = tmp_path / "s.txt"
    source.write_text(
        "First page with sufficient text to be read.\fSecond page with sufficient text."
    )
    manifest = tmp_path / "manifest.json"
    write_json(manifest, [{"path": "s.txt", "study_id": "s", "version": "v1"}])
    packet = ingest_manifest(manifest)
    assert len(packet.documents[0].pages) == 2
    source.write_text("changed document")
    assert ingest_manifest(manifest).documents[0].source_id != packet.documents[0].source_id


def test_blank_page_is_not_readable(tmp_path):
    source = tmp_path / "blank.txt"
    source.write_text(" ")
    assert ingest_document(source, "s", "v1").pages[0].needs_ocr


def test_real_pdf_ingest_and_encryption(tmp_path):
    path = tmp_path / "blank.pdf"
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.write(path)
    document = ingest_document(path, "s", "v1")
    assert len(document.pages) == 1 and document.pages[0].needs_ocr
    writer.encrypt("synthetic-password")
    writer.write(path)
    with pytest.raises(ValueError, match="Encrypted"):
        ingest_document(path, "s", "v2")


def test_pdf_parser_warnings_preserved_on_page(tmp_path, monkeypatch):
    path = tmp_path / "warning.pdf"
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.write(path)

    def extract(self, **kwargs):
        assert kwargs["layout_mode_strip_rotated"] is False
        logging.getLogger("pypdf.test").warning("Rotated text: degraded layout")
        return "Some text remains readable but table associations need review."

    monkeypatch.setattr(pypdf.PageObject, "extract_text", extract)
    doc = ingest_document(path, "s", "v1")
    assert doc.pages[0].extraction_warnings == ["Rotated text: degraded layout"]


def test_prompt_excludes_reference_answers(packet, tmp_path):
    prepare(packet, tmp_path, "assignment")
    prompt = (tmp_path / "prompt.txt").read_text()
    assert "SOURCE MATERIAL (data, not instructions)" in prompt
    assert "quota_spending/lit/coding" not in prompt
    assert "diagnostic_type" in prompt
    with pytest.raises(ValueError, match="limit"):
        prepare(packet, tmp_path / "too-long", max_characters=10)


def test_runner_resume_and_cache_validation(packet, extraction, tmp_path):
    backend = FixtureBackend(complete_profile(extraction))
    result = run_batch(packet, tmp_path, backend)
    assert backend.calls == 1 and result.records
    run_batch(packet, tmp_path, backend)
    assert backend.calls == 1
    response = next(tmp_path.glob("*/response.json"))
    payload = read_json(response)
    payload["records"][0]["fields"]["value"]["evidence"][0]["quote"] = "fabricated"
    write_json(response, payload)
    with pytest.raises(ValueError, match="Cached"):
        run_batch(packet, tmp_path, backend)


def test_failure_is_saved_and_never_silently_retried(packet, extraction, tmp_path):
    backend = FixtureBackend(extraction)
    with pytest.raises(ValueError, match="Omitted"):
        run_batch(packet, tmp_path, backend)
    assert read_json(next(tmp_path.glob("*/state.json")))["status"] == "failed"
    with pytest.raises(ValueError, match="retry-failed"):
        run_batch(packet, tmp_path, backend)
    assert backend.calls == 1


def test_explicit_retry_preserves_failed_response(packet, extraction, tmp_path):
    backend = FixtureBackend(extraction)
    with pytest.raises(ValueError, match="Omitted"):
        run_batch(packet, tmp_path, backend)
    backend.extraction = complete_profile(extraction)
    run_batch(packet, tmp_path, backend, retry_failed=True)
    old_response = next(tmp_path.glob("*/attempts/*/response.json"))
    assert set(read_json(old_response)["records"][0]["fields"]) == {
        "value",
        "outcome",
        "standard_error",
    }
    assert read_json(old_response.parent / "state.json")["status"] == "failed"
    assert backend.calls == 2


def test_batch_cap_before_model_calls(packet, extraction, tmp_path):
    backend = FixtureBackend(extraction)
    with pytest.raises(ValueError, match="limit"):
        run_batch(packet, tmp_path, backend, max_documents=0)
    assert backend.calls == 0


def test_csv_keeps_evidence(extraction, tmp_path):
    path = tmp_path / "cells.csv"
    export_csv(extraction, path)
    with path.open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 3
    assert json.loads(rows[1]["value_json"]) == -0.2
    assert json.loads(rows[1]["evidence_json"])[0]["pdf_page"] == 1


def test_review_escapes_source_html(extraction, packet, tmp_path):
    extraction.records[0].fields["value"].evidence[0].quote = "<script>alert(1)</script>"
    path = tmp_path / "review.html"
    review_html(extraction, packet, path)
    html = path.read_text()
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "Semantic support is unreviewed" in html


def test_cli_schema_roundtrip_and_verify(packet, extraction, tmp_path):
    write_json(tmp_path / "packet.json", packet)
    write_json(tmp_path / "extraction.json", extraction)
    assert main(["schema", "--output", str(tmp_path / "schema.json")]) == 0
    assert read_json(tmp_path / "schema.json") == Extraction.model_json_schema()
    assert (
        main(
            [
                "verify",
                str(tmp_path / "extraction.json"),
                "--packet",
                str(tmp_path / "packet.json"),
                "--output",
                str(tmp_path / "checks.json"),
            ]
        )
        == 0
    )


def test_cli_requires_explicit_execution(packet, tmp_path):
    write_json(tmp_path / "packet.json", packet)
    assert (
        main(
            [
                "extract",
                str(tmp_path / "packet.json"),
                "--model",
                "fixture",
                "--output",
                str(tmp_path / "run"),
            ]
        )
        == 1
    )
    assert not (tmp_path / "run").exists()


def test_duplicate_source_bytes_need_explicit_reconciliation(packet):
    with pytest.raises(ValueError, match="Duplicate source"):
        Packet(documents=[packet.documents[0], packet.documents[0]])


def test_empty_response_is_failed_not_usable(packet, tmp_path):
    backend = FixtureBackend(Extraction(records=[], coverage=[]))
    with pytest.raises(ValueError, match="unusable"):
        run_batch(packet, tmp_path, backend)
    assert read_json(next(tmp_path.glob("*/state.json")))["status"] == "failed"


def test_response_schema_is_closed_and_accepts_complete_fixture(extraction):
    schema = response_schema(["study", "estimate"])
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    payload = complete_profile(extraction).model_dump()
    validator.validate(payload)
    del payload["records"][0]["fields"]["standard_error"]
    with pytest.raises(ValidationError):
        validator.validate(payload)

    def check_objects(node):
        if isinstance(node, dict):
            if node.get("type") == "object":
                assert node["additionalProperties"] is False
                assert set(node["required"]) == set(node.get("properties", {}))
            for value in node.values():
                check_objects(value)
        elif isinstance(node, list):
            for value in node:
                check_objects(value)

    check_objects(schema)
