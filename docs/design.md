# Extraction contract

The question is whether an agent can recover usable study information from a
supplied corpus, with enough evidence for a researcher to check every substantive
value. Discovering a complete literature is outside this first version.

## Records and measures

The runtime catalog in `src/study_extract/catalog.py` defines allowed fields and
types and generates `schemas/fields.json`. Source metadata and IDs are system or
manifest inputs, not LLM claims. Every substantive record field uses a Cell.

| Record | Unit and fields | Reason |
|---|---|---|
| study | One report's title, authors, year, setting, question, registration, availability, funding | Versioned identity and transparency |
| design | One design/contrast: estimand, population, assignment, receipt, strata/pool, assumptions, attrition, interference, RD/IV/DiD details | Distinguish identification from estimation |
| sample | One analysis sample: period, geography, selection, unit counts, clusters, exclusions, weights, overlap | Preserve the denominator and dependence |
| outcome | One construct/operationalization/timepoint: instrument, units, coding, numerator, denominator, unknown categories, reliability | Avoid combining different quantities |
| estimate | One population × outcome × contrast × time × specification: value, scale, SE/SD/CI, p-value, df, sample, adjustments, cluster method, multiplicity | Reproduce the reported quantity without silent conversion |
| diagnostic | One reported implementation/assumption check: target, procedure, sample, null, statistic, result, interpretation, limits | An assertion of random assignment is not an implementation audit |
| claim | One finding, mechanism, normative claim or identifying premise, retaining scope, qualifications and supporting arguments | Tested, asserted and speculated are different |
| comparison | One observed/benchmark pair, retaining both sources, units, denominators, geography and dates | Media shares, arrests, victimization and population shares differ |

Multiple records of a kind are allowed. IDs link estimates to outcomes, samples,
designs and claims. A study family may span reports; evidence is pinned to a
specific document. Cross-report reconciliation is a reviewer task. The extractor
must not silently attach a working-paper appendix to a journal article.

## Every cell has an evidence contract

`value`, `state`, `basis`, `evidence`, `rationale`, `derivation`:

- States: `present`, `not_found`, `not_applicable`, `unreadable`, `conflicting`.
- Bases: `reported`, `derived`, `reviewer_judgment`.
- Present reported/judgment cells require evidence. Judgment also requires a
  rationale. A mechanism classified as tested is usually a coding judgment even
  when the underlying analysis is directly reported.
- Missing states require null and an explanation. `not_found` means not located
  in the supplied materials, not absent from the entire study/literature.
- A conflicting cell preserves at least two passages and does not choose a value.
- Derived cells identify input record/field pairs, an allowed operation and its
  assumptions. The validator recomputes the number. Only directly reported inputs
  are supported initially; arbitrary code/formulas from documents are never run.
- Evidence: source ID, PDF page, quote, optional printed page/table/row/column,
  role (`value`, `row_label`, `column_label`, `footnote`, `context`). A numeric
  table cell needs enough surrounding evidence to establish its meaning.
- Automated location checks use Unicode normalization and whitespace folding,
  not fuzzy matching. They do not fix signs, punctuation or numbers. Failed
  matches are review tasks, not permission to rewrite the source.

Review decisions are external to model output. An LLM cannot mark its own cell
human verified. Neither a confidence score nor a citation match constitutes
semantic validation. The initial viewer is read-only; adjudication is stored in
explicit reference files.

## Measurement decisions

Preserve raw quantities and signs. Do not turn stars into exact SEs, 0.000 into a
zero probability, log odds into odds ratios, an SD into an SE, or sample N into df.
Cluster counts do not themselves establish effective sample size. Preserve
inequalities in p-values. Record reported interval method and scale before deriving
anything. Comparability and preferred-specification selection are explicit
decisions, not opportunities to select significant results.

Keep estimates sharing people, samples, arms, outcomes or papers linked. Do not
pool them as independent. Do not compute a generic quality score: individual
design limitations are useful; an unsupported composite score is not.

## Methodological basis

- [Lin, Green and Coppock, Green Lab SOP v1.05 (2016)](https://alexandercoppock.com/Green-Lab-SOP/Green_Lab_SOP.html):
  motivates fields for implementation checks, clustering/blocking, covariates,
  attrition, noncompliance and departures from prespecified analyses. This is a
  dated lab protocol, not a claim that its defaults govern every design.
- [Gelman and Carlin (2014)](https://sites.stat.columbia.edu/gelman/research/published/retropower_final.pdf):
  motivates magnitude/sign risks and retaining SEs and externally justified
  plausible effects. A later optional design-analysis module must record the
  external effect assumptions. No observed-effect post hoc power by default.
- [Gelman and Loken (2013)](https://stat.columbia.edu/~gelman/research/unpublished/forking.pdf):
  motivates recording selection, specifications, outcome families and
  prespecification. It does not license inferring undisclosed researcher intent.
- [Cochrane Handbook, chapter 5](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-05):
  motivates study/report separation, reconciliation, piloted extraction forms
  and preservation of original data before conversion.
- [Paperclip documentation](https://paperclip.gxl.ai/docs): motivates a document
  map/extract workflow with structured outputs and traceable sources. Its CLI
  requires citation fields in the schema; structured validity is not accuracy.

These are design inferences from the sources, not a schema endorsed by those authors.

## Implementation stages

1. Local manifest → hash and parse documents → page-preserving packet.
2. Select profile → serialize task/schema/prompt with no reference answers.
3. Extract per document → strict validation → deterministic location verification.
4. Preserve raw response, logs and request hash; invalid output remains failed.
5. Export evidence-bearing cells and a review view; score only adjudicated cells.
6. Later: OCR/vision with original-page linkage, explicit reconciliation, human
   support adjudication UI, API spending caps, and validated derived statistics.

No retrieval truncation in v0.1: over-limit documents stop explicitly. Full-text
input is the initial baseline. Retrieval/chunking needs separate coverage tests,
especially for supplements and negative/absence claims.

PDF ingestion keeps rotated text and records parser warnings on their page. Layout
warnings remain visible in the review view; retaining text does not establish that
a table's row/column associations survived. Sparse-text flags are a heuristic,
not proof of completeness or an OCR quality score.
