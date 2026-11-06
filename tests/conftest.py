from pathlib import Path

import pytest

from study_extract.ingest import ingest_document
from study_extract.models import Cell, Coverage, Evidence, Extraction, Packet, Record


@pytest.fixture
def packet(tmp_path: Path) -> Packet:
    path = tmp_path / "paper.txt"
    path.write_text(
        "Synthetic test document, not a real research study.\n"
        "Table 2: drinking water. Treatment effect -0.20; standard error 0.08.\n"
        "The sample includes 250 villages.\f"
        "Appendix: this example has no statistical claim about the real world."
    )
    return Packet(documents=[ingest_document(path, "synthetic-study", "fixture-v1")])


@pytest.fixture
def extraction(packet: Packet) -> Extraction:
    source = packet.documents[0].source_id
    evidence = Evidence(
        source_id=source,
        pdf_page=1,
        quote="Table 2: drinking water. Treatment effect -0.20; standard error 0.08.",
    )
    fields = {
        "outcome": Cell(value="drinking water", state="present", evidence=[evidence]),
        "value": Cell(value=-0.2, state="present", evidence=[evidence]),
        "standard_error": Cell(value=0.08, state="present", evidence=[evidence]),
    }
    return Extraction(
        records=[
            Record(
                record_id=f"{source}:e1",
                study_id="synthetic-study",
                source_id=source,
                kind="estimate",
                fields=fields,
            )
        ],
        coverage=[
            Coverage(
                source_id=source,
                pages_read=[1, 2],
                unreadable_pages=[],
                missing_materials=[],
                scope="synthetic fixture",
            )
        ],
    )
