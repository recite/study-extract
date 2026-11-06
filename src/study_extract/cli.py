"""Command-line entry points."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from study_extract.agent import PROFILES, CodexBackend, prepare, run_batch
from study_extract.catalog import catalog_json
from study_extract.evaluate import ReferenceSet, evaluate
from study_extract.evidence import verify
from study_extract.export import export_csv, review_html
from study_extract.ingest import ingest_manifest
from study_extract.io import read_json, write_json
from study_extract.models import Extraction, Packet
from study_extract.references import EstimateMapping, import_estimates, reference_inventory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract study records with per-cell evidence")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ["schema", "catalog"]:
        command = sub.add_parser(name)
        command.add_argument("--output", type=Path, required=True)
    command = sub.add_parser("ingest")
    command.add_argument("manifest", type=Path)
    command.add_argument("--output", type=Path, required=True)
    for name in ["prepare", "extract"]:
        command = sub.add_parser(name)
        command.add_argument("packet", type=Path)
        command.add_argument("--output", type=Path, required=True)
        command.add_argument("--profile", choices=PROFILES, default="core")
        command.add_argument("--max-characters", type=int, default=250000)
        if name == "extract":
            command.add_argument("--model", required=True)
            command.add_argument("--execute", action="store_true")
            command.add_argument("--max-documents", type=int, default=3)
            command.add_argument("--timeout", type=float, default=600)
            command.add_argument("--retry-failed", action="store_true")
    for name in ["verify", "export", "review", "evaluate"]:
        command = sub.add_parser(name)
        command.add_argument("extraction", type=Path)
        command.add_argument("--output", type=Path, required=True)
        if name != "export":
            command.add_argument("--packet", type=Path, required=True)
        if name == "evaluate":
            command.add_argument("--references", type=Path, required=True)
    command = sub.add_parser("import-reference")
    for name in ["quota-spending", "quota-assignment", "face-of-crime", "output"]:
        command.add_argument(f"--{name}", type=Path, required=True)
    command = sub.add_parser("import-estimates")
    command.add_argument("coding", type=Path)
    command.add_argument("--packet", type=Path, required=True)
    command.add_argument("--source-id", required=True)
    command.add_argument("--version", required=True)
    command.add_argument("--mapping", type=Path, required=True)
    command.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "schema":
            write_json(args.output, Extraction.model_json_schema())
        elif args.command == "catalog":
            write_json(args.output, catalog_json())
        elif args.command == "ingest":
            write_json(args.output, ingest_manifest(args.manifest))
        elif args.command == "import-reference":
            write_json(
                args.output,
                reference_inventory(args.quota_spending, args.quota_assignment, args.face_of_crime),
            )
        elif args.command == "import-estimates":
            packet = Packet.model_validate(read_json(args.packet))
            source = next((d for d in packet.documents if d.source_id == args.source_id), None)
            if source is None:
                raise ValueError("Source ID is absent from the packet")
            mapping = read_json(args.mapping)
            if not isinstance(mapping, list):
                raise ValueError("Estimate mapping must be a JSON list")
            write_json(
                args.output,
                import_estimates(
                    args.coding,
                    source,
                    args.version,
                    [EstimateMapping.model_validate(row) for row in mapping],
                ),
            )
        elif args.command in ("prepare", "extract"):
            packet = Packet.model_validate(read_json(args.packet))
            if args.command == "prepare":
                prepare(packet, args.output, args.profile, args.max_characters)
            else:
                if not args.execute:
                    raise ValueError("Use --execute only after authorizing account/model usage")
                run_batch(
                    packet,
                    args.output,
                    CodexBackend(args.model),
                    args.profile,
                    args.max_documents,
                    args.timeout,
                    args.retry_failed,
                    args.max_characters,
                )
        else:
            extraction = Extraction.model_validate(read_json(args.extraction))
            if args.command == "export":
                export_csv(extraction, args.output)
            else:
                packet = Packet.model_validate(read_json(args.packet))
                if args.command == "verify":
                    report = verify(extraction, packet)
                    write_json(args.output, report)
                    return 0 if report["valid_locations"] else 1
                if args.command == "review":
                    review_html(extraction, packet, args.output)
                else:
                    references = ReferenceSet.model_validate(read_json(args.references))
                    write_json(args.output, evaluate(extraction, references, packet))
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
