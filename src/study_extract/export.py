"""Evidence-preserving long tables and a read-only local review page."""

import csv
import html
import json
from pathlib import Path
from typing import Any

from study_extract.evidence import verify
from study_extract.models import Extraction, Packet


def export_csv(extraction: Extraction, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "study_id",
                "source_id",
                "record_id",
                "kind",
                "field",
                "value_json",
                "state",
                "basis",
                "evidence_json",
                "rationale",
                "derivation_json",
            ],
        )
        writer.writeheader()
        for record in extraction.records:
            for name, cell in record.fields.items():
                writer.writerow(
                    {
                        "study_id": record.study_id,
                        "source_id": record.source_id,
                        "record_id": record.record_id,
                        "kind": record.kind,
                        "field": name,
                        "value_json": json.dumps(cell.value, ensure_ascii=False),
                        "state": cell.state,
                        "basis": cell.basis,
                        "evidence_json": json.dumps([e.model_dump() for e in cell.evidence]),
                        "rationale": cell.rationale,
                        "derivation_json": (
                            cell.derivation.model_dump_json() if cell.derivation else "null"
                        ),
                    }
                )


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def review_html(extraction: Extraction, packet: Packet, output: Path) -> None:
    report = verify(extraction, packet)
    blocks = []
    for record in extraction.records:
        rows = []
        for name, cell in record.fields.items():
            evidence = "".join(
                f"<details><summary>{esc(e.role)} · PDF p. {e.pdf_page}"
                f" · printed {esc(e.printed_page or 'unknown')}</summary>"
                f"<p>{esc(e.source_id)} · {esc(e.table or '')} · row {esc(e.row or '')}"
                f" · column {esc(e.column or '')}</p>"
                f"<blockquote>{esc(e.quote)}</blockquote></details>"
                for e in cell.evidence
            )
            if cell.derivation:
                evidence += f"<pre>{esc(cell.derivation.model_dump_json(indent=2))}</pre>"
            rows.append(
                f"<tr><th>{esc(name)}</th><td>{esc(cell.value)}</td>"
                f"<td>{esc(cell.state)} / {esc(cell.basis)}</td><td>{evidence}"
                f"<p>{esc(cell.rationale or '')}</p></td></tr>"
            )
        blocks.append(
            f"<section><h2>{esc(record.kind)} · {esc(record.record_id)}</h2>"
            f"<p>Study: {esc(record.study_id)} · Document: {esc(record.source_id)}</p>"
            "<table><thead><tr><th>Field</th><th>Value</th><th>Status</th>"
            f"<th>Evidence</th></tr></thead><tbody>{''.join(rows)}</tbody></table></section>"
        )
    errors = [f for f in report["findings"] if f["severity"] == "error"]
    warnings = [f for f in report["findings"] if f["code"] == "parser_warning"]
    sources = "".join(
        f"<li>{esc(d.source_id)}: {esc(d.filename)} · {esc(d.version)}"
        f" · {len(d.pages)} pages · SHA-256 {esc(d.sha256)}</li>"
        for d in packet.documents
    )
    text = (
        "<!doctype html><html lang='en'><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<title>Study extraction review</title><style>"
        "body{font:16px/1.5 system-ui;margin:2rem auto;max-width:1250px;padding:0 1rem}"
        "table{border-collapse:collapse;width:100%;table-layout:fixed}"
        "th,td{border-bottom:1px solid #ddd;padding:.7rem;text-align:left;vertical-align:top;"
        "overflow-wrap:anywhere}th:nth-child(1){width:16%}th:nth-child(4){width:40%}"
        "blockquote{white-space:pre-wrap;margin:.5rem;background:#f3f5f7;padding:1rem}"
        "section{margin:3rem 0}summary{cursor:pointer}aside{padding:1rem;background:#fff3cd}"
        "</style><h1>Study extraction review</h1><aside>"
        f"Evidence-location errors: {len(errors)}. Semantic support is unreviewed. "
        "A located quotation does not certify the extracted interpretation.</aside>"
        f"<pre>{esc(json.dumps(errors + warnings, indent=2))}</pre>"
        f"<h2>Sources</h2><ul>{sources}</ul>{''.join(blocks)}</html>"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
