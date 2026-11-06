"""Page-preserving PDF/text ingestion. Scans remain explicitly unreadable."""

import logging
from importlib.metadata import version as package_version
from pathlib import Path

import pypdf

from study_extract.io import read_json, sha256
from study_extract.models import Document, Packet, Page


class PageWarnings(logging.Handler):
    def __init__(self) -> None:
        super().__init__(logging.WARNING)
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(record.getMessage())


def ingest_document(path: Path, study_id: str, version: str) -> Document:
    data = path.read_bytes()
    digest = sha256(data)
    warnings: list[list[str]] = []
    if path.suffix.lower() == ".pdf":
        reader = pypdf.PdfReader(path)
        if reader.is_encrypted:
            raise ValueError(f"Encrypted PDF needs an accessible copy: {path.name}")
        texts = []
        logger = logging.getLogger("pypdf")
        for page in reader.pages:
            handler = PageWarnings()
            logger.addHandler(handler)
            try:
                texts.append(
                    page.extract_text(extraction_mode="layout", layout_mode_strip_rotated=False)
                    or ""
                )
            finally:
                logger.removeHandler(handler)
            warnings.append(handler.messages)
        parser = (
            f"pypdf/{pypdf.__version__}/layout/keep-rotated/"
            f"fonttools/{package_version('fonttools')}"
        )
    elif path.suffix.lower() == ".txt":
        texts = data.decode("utf-8").split("\f")
        parser = "utf8-formfeed/1"
    else:
        raise ValueError("Supported inputs: PDF and UTF-8 text with form-feed page boundaries")
    pages = [
        Page(
            number=i,
            text=t,
            text_sha256=sha256(t.encode()),
            needs_ocr=len(t.strip()) < 30,
            extraction_warnings=warnings[i - 1] if warnings else [],
        )
        for i, t in enumerate(texts, 1)
    ]
    return Document(
        source_id=f"doc_{digest[:20]}",
        study_id=study_id,
        version=version,
        filename=path.name,
        sha256=digest,
        parser=parser,
        pages=pages,
    )


def ingest_manifest(path: Path) -> Packet:
    manifest = read_json(path)
    if not isinstance(manifest, list) or not manifest:
        raise ValueError("Manifest must be a nonempty list of path/study_id/version objects")
    documents = []
    for item in manifest:
        if not isinstance(item, dict) or set(item) != {"path", "study_id", "version"}:
            raise ValueError("Each manifest item needs exactly path, study_id, version")
        if not all(isinstance(v, str) and v.strip() for v in item.values()):
            raise ValueError("Manifest values must be nonempty strings")
        source = Path(item["path"])
        if not source.is_absolute():
            source = path.parent / source
        documents.append(ingest_document(source, item["study_id"], item["version"]))
    return Packet(documents=documents)
