"""Deterministic location checks; these do not establish semantic entailment."""

import re
import unicodedata
from dataclasses import asdict, dataclass
from typing import Any

from study_extract.io import sha256
from study_extract.models import Evidence, Extraction, Packet


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text)).strip()


@dataclass
class Finding:
    record_id: str
    field: str
    code: str
    detail: str
    severity: str = "error"


def quote_status(evidence: Evidence, packet: Packet) -> str:
    doc = next((d for d in packet.documents if d.source_id == evidence.source_id), None)
    if doc is None:
        return "unknown_source"
    if evidence.pdf_page > len(doc.pages):
        return "invalid_page"
    page = doc.pages[evidence.pdf_page - 1]
    if page.text_sha256 != sha256(page.text.encode()):
        return "changed_page_text"
    if page.needs_ocr:
        return "unreadable_page"
    if not normalized(evidence.quote):
        return "empty_quote"
    return "located" if normalized(evidence.quote) in normalized(page.text) else "quote_not_found"


def verify(extraction: Extraction, packet: Packet) -> dict[str, Any]:
    docs = {doc.source_id: doc for doc in packet.documents}
    findings: list[Finding] = []
    checked = located = present = 0
    for original in packet.documents:
        for page in original.pages:
            if page.extraction_warnings:
                findings.append(
                    Finding(
                        "",
                        "",
                        "parser_warning",
                        f"{original.source_id} PDF page {page.number}: "
                        + "; ".join(page.extraction_warnings),
                        "review",
                    )
                )
            if page.text_sha256 != sha256(page.text.encode()):
                findings.append(Finding("", "", "changed_page_text", original.source_id))
    coverage_ids = [c.source_id for c in extraction.coverage]
    if set(coverage_ids) != set(docs) or len(coverage_ids) != len(set(coverage_ids)):
        findings.append(Finding("", "", "coverage_sources", "Need one coverage record per source"))
    for coverage in extraction.coverage:
        doc = docs.get(coverage.source_id)
        if doc:
            read, unreadable = set(coverage.pages_read), set(coverage.unreadable_pages)
            expected = set(range(1, len(doc.pages) + 1))
            if (read | unreadable) != expected or read & unreadable:
                findings.append(Finding("", "", "page_coverage", coverage.source_id))
            if len(read) != len(coverage.pages_read) or len(unreadable) != len(
                coverage.unreadable_pages
            ):
                findings.append(Finding("", "", "duplicate_page_coverage", coverage.source_id))
            if any(p.needs_ocr and p.number in read for p in doc.pages):
                findings.append(Finding("", "", "unreadable_claimed_read", coverage.source_id))
    for record in extraction.records:
        doc = docs.get(record.source_id)
        if doc is None or doc.study_id != record.study_id:
            findings.append(Finding(record.record_id, "", "source_family", record.source_id))
        for field, cell in record.fields.items():
            present += cell.state == "present"
            for ev in cell.evidence:
                checked += 1
                status = quote_status(ev, packet)
                source = docs.get(ev.source_id)
                if source and source.study_id != record.study_id:
                    status = "wrong_study_family"
                if ev.source_id != record.source_id:
                    status = "wrong_document_version"
                if status == "located":
                    located += 1
                else:
                    findings.append(
                        Finding(
                            record.record_id,
                            field,
                            status,
                            f"{ev.source_id} PDF page {ev.pdf_page}",
                        )
                    )
            if cell.state == "present" and cell.basis != "derived":
                findings.append(
                    Finding(
                        record.record_id,
                        field,
                        "support_unreviewed",
                        "Located text is not proof it supports the value",
                        "review",
                    )
                )
    return {
        "valid_locations": not any(f.severity == "error" for f in findings),
        "evidence_checked": checked,
        "evidence_located": located,
        "present_cells": present,
        "semantic_support_accuracy": None,
        "findings": [asdict(f) for f in findings],
    }
