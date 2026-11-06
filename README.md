# study-extract

Turn a supplied collection of research papers into structured records with evidence
for each substantive field. Keep reported values, calculations, and reviewer
judgments distinct. Evaluate against adjudicated references without treating
uncoded cells as negative findings.

This is an initial local implementation. It does not yet have measured extraction
accuracy on a held-out research corpus. A matching quotation proves where text
occurs; it does not prove that the text supports the extracted value.

## Start

Requires Python 3.11+ and uv. PDF ingestion uses pypdf; scanned pages are flagged
for OCR rather than silently treated as empty evidence.

```sh
uv sync
uv run study-extract ingest examples/manifest.json --output local/packet.json
uv run study-extract prepare local/packet.json --output local/task
```

`prepare` writes a prompt, JSON Schema, and task manifest. The packet contains
page-preserving text. References and existing coding are not included in prompts.
The initial Codex adapter requires the Codex CLI, an authenticated account, an
explicit model, and explicit execution authorization:

```sh
uv run study-extract extract local/packet.json --model YOUR_MODEL --execute --output local/run
```

The adapter uses read-only mode and disables shell/browser/app/plugin tools. It
runs sequentially, once per document, with no automatic retries. The CLI account's
usage terms apply; this adapter does not implement a monetary spending cap. Use
only an account and scope you have authorized. An API backend with bounded dollar
spending is future work.

You can also obtain a JSON response using another model and validate it locally:

```sh
uv run study-extract verify local/response.json --packet local/packet.json --output local/checks.json
uv run study-extract export local/response.json --output local/cells.csv
uv run study-extract review local/response.json --packet local/packet.json --output local/review.html
uv run study-extract evaluate local/response.json --packet local/packet.json --references local/references.json --output local/evaluation.json
```

The CSV has one row per record/field, including its evidence JSON; it does not
discard evidence to make a wide table. The HTML groups fields by record and exposes
quotations and locators. It labels semantic support as unreviewed.

## Contract and evaluations

- [Design and field groups](docs/design.md)
- [Evaluation protocol](docs/evaluation.md)
- [Validation and pilot status](docs/validation.md)
- [Sources and repository crosswalk](docs/sources.md)
- [Machine-readable field dictionary](schemas/fields.json)
- [Extraction JSON Schema](schemas/extraction.schema.json)

One study may have several reports, samples, outcomes, and estimates. A file hash
identifies a particular source version. Every evidence span includes that source
ID, a one-based PDF page and a quotation; table locators and evidence roles retain
headers, rows and notes. Printed page labels are separate from PDF page indexes.

The initial arithmetic operations are deliberately narrow: differences, ratios,
percent-to-proportion conversion, and estimate/SE ratios. They record their input
cells and assumptions and are recomputed during validation. No automatic pooling,
power, Type S/M calculation, or study quality score is produced.

For a small worked example without model calls, ingest `examples/manifest.json`,
then use `examples/response.json` with `verify`, `review`, or `evaluate` and
`examples/references.json`. These are invented fixture values, not an empirical
accuracy demonstration. The example contains three cells; model extraction requires
every field of each requested record kind, including explicit missing states.

## Existing reference material

`import-reference` builds a provisional local inventory from quota_spending,
quota_assignment and face_of_crime checkouts. It preserves the original annotations
and hashes without promoting them to adjudicated gold or putting answers in prompts.

```sh
uv run study-extract import-reference --quota-spending /path/to/quota_spending --quota-assignment /path/to/quota_assignment --face-of-crime /path/to/face_of_crime --output local/reference-inventory.json
```

Source PDFs and private research materials belong in ignored `local/` or `runs/`
directories. They are not distributed with the package. Reviewers should group
all reports of a study before assigning development/test splits. Some source
annotations have already been inspected during design; those studies are not an
unseen test set.

## Development

```sh
make check
make ci-docker
```

Ruff checks formatting, imports and lint; mypy checks types; pytest exercises
provenance, schema, evaluation, exports, and the runner with a local test backend.
`make schema` regenerates the schema and dictionary from the same code used at
runtime. GitHub Actions runs offline tests, never metered model calls.
