# Validation and pilot status

Validated locally on 2026-11-05. An assistant-authored Bose–Das development pilot
is available; no autonomous extraction or held-out accuracy evaluation has been
completed. The current implementation is not a validated research coding system.

## Software checks

- `make check`: Ruff lint/imports/format, mypy, 72 pytest tests, wheel and source
  distribution builds pass on macOS with Python 3.13.16.
- The test suite covers wrong signs and pages,
  source-version mixing, derivation arithmetic, missing values, provisional-gold
  exclusion, ambiguous matching, complete structured-output schemas, parser
  warnings, failed/empty outputs, resumption, and evidence-preserving exports.
- The wheel installs in a separate environment. Its CLI successfully ingests the
  invented example, verifies evidence, evaluates two fixture values, and produces
  a review page. Fixture agreement measures software behavior, not research accuracy.
- All 72 tests, lint, formatting, type checks and builds also pass in a standard
  Python 3.13 Linux Docker image. Colima was initially stopped and was started
  for this check. Hosted CI results are available in
  [GitHub Actions](https://github.com/recite/study-extract/actions/workflows/ci.yml).

## Research-material smoke test

Four quota PDFs were ingested and prepared without supplying reference answers:

| Document | PDF pages | Result |
|---|---:|---|
| Chattopadhyay–Duflo 2004, Econometrica | 35 | Prepared; rotated-layout warnings on PDF pages 16, 22, 24, 25 |
| Bose–Das 2018, Review of Development Economics | 18 | Prepared |
| Chaturvedi–Das–Mahajan 2023 working paper | 77 | Prepared |
| Chaturvedi–Das–Mahajan 2025 journal version | 31 | Prepared |

All 161 pages yield text above the sparse-text threshold. That is not a claim of
correct table reconstruction. Rotated text is retained and page warnings persist
in the packet and review output. The four affected pages need visual inspection
before relying on table associations.

The provisional reference inventory contains 23 quota_spending coding files,
16 quota_assignment claim/audit files, and the face_of_crime table. These are
file counts, not numbers of independent studies or adjudicated labels. Original
annotations and source hashes are retained in ignored `local/` files. The
new `import-estimates` command converts explicitly mapped numeric coding rows into
provisional evaluation references. Six Bose–Das published-version rows have been
converted; their 18 numeric targets agree with the frozen assisted extraction.
All remain unadjudicated. See [the pilot report](pilot-bose-das.md).

## Independent review

An independent design/code review reproduced four issues that are now fixed and
covered by regression tests: provisional duplicates changing scored accuracy,
outcome-driven record matching, links/calculations crossing paper versions, and
empty responses being labeled successful. The reviewer did not certify model
performance or independently adjudicate the research corpus.

## Remaining work

1. Run the authorized small Codex pilot using the existing ChatGPT account and
   configured `gpt-6-astra` model. Two launch attempts failed during local
   app-server initialization with `Operation not permitted`; no model response
   or usage report was produced. A session that permits Codex startup is needed.
2. Inspect source-page images, adjudicate reference cells and record disagreements.
3. Expand development cases, freeze the pipeline, and evaluate untouched families.
4. Add OCR/vision and explicit cross-report reconciliation after baseline results.

The runner is intended for one process per output directory. It has no monetary
spending cap, automatic retries, concurrent-run locking, or human semantic-support
scorer. Explicit retries archive the previous response, logs and status within
the task directory. Structured validation and literal
citation matching cannot determine whether the cited evidence entails a cell.

## Workspace location

The requested parent directory is `/Users/soodoku/Documents/GitHub/recite`.
This session can read it but cannot create a repository there. The new local
repository and private pilot artifacts are preserved at
`/Users/soodoku/Documents/GitHub/themains/study-extract`; move the repository to
`/Users/soodoku/Documents/GitHub/recite/study-extract` from a writable workspace.
No source-repository files were changed. Code and documentation are pushed to the
public [recite/study-extract repository](https://github.com/recite/study-extract).
Original papers, imported annotations and private pilot artifacts remain local.
