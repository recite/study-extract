# Evaluation protocol

## Question and comparison

How accurately can the agent recover the requested records and fields from a
supplied set of social-science papers, and how much verification work does it save?
Primary unit: underlying study family. Report document-, record- and cell-level
counts as diagnostics. Source passages, generated output, and review decisions
are retained separately.

Compare (1) full-document extraction with evidence, (2) the same extraction with
automatic evidence checks, and later (3) retrieval/chunking and an independent
semantic checker. Freeze model, prompt, schema, parser, profile and budget for each
comparison. Do not claim a Paperclip comparison unless Paperclip is actually run
on the same materials and task.

## References and splitting

Existing quota_spending YAML, quota_assignment claim/diagnostic tables, and
face_of_crime literature notes are provisional annotations. Preserve their values,
provenance, audit status, source versions and unresolved disagreements. Do not turn
missing codes into negative labels. A second source check and adjudication is
needed before an item counts as gold. References with no reviewer and rationale
cannot be marked adjudicated in the schema.

Group all versions, supplements, and duplicate study reports before splitting.
Shared samples and closely related replications may require a larger group. The
deterministic helper uses study_id; a researcher must verify those family IDs.
Do not rely on filenames or a random split of cells.

Already inspected: the project READMEs, coding protocol, Chattopadhyay–Duflo 2004
coding, selected assignment records and the face_of_crime summary table. Treat
these as development material. An honest test set needs untouched families or a
new independently adjudicated corpus. A retrospective hash split does not erase
this exposure.

Start with 6–10 development families spanning tables, version pairs, scans, missing
precision, conflicting prose/tables and descriptive denominators. Then evaluate
on a frozen adjudicated family-level holdout and a separate crime/media corpus.
Do not select only clean or easily extracted papers. Missing PDFs/supplements and
OCR failures stay in the operational denominator.

## Measures

| Measure | Definition and denominator |
|---|---|
| Record recall | Matched eligible gold records / eligible reviewed gold records |
| Record precision | Valid requested records / all produced records; only score against exhaustive reviewed scope |
| Cell accuracy | Correct value AND state / all adjudicated target cells; missing output is incorrect |
| Numeric accuracy | Sign, units, estimate, SE/SD/CI and N/cluster identity separately; field-specific tolerances based on printed rounding |
| Citation location | Exact version/page and located quote / reviewed locatable evidence targets |
| Evidence support | Human-adjudicated evidence supports the complete cell meaning / reviewed predicted assertions |
| Abstention | Missing known values; invented values where reviewed missing; coverage versus error, with explicit states |
| Critical errors | Sign flips, SE/SD swaps, wrong denominator/column, wrong version, causal-label invention, false absence |
| Consistency | Repeated runs' agreement, including correlated wrong answers; not a substitute for accuracy |
| Operational yield | Valid usable outputs / all attempted documents; include malformed/truncated/failed outputs |
| Cost and utility | Time, usage/cost, retries, corrections and reviewer minutes per usable record |
| Downstream impact | Differences in eligible estimates, direction/scale and review conclusions under a fixed analysis plan |

Current software computes deterministic value/state and citation-location scores.
Semantic support remains null until independent adjudication is supplied; it is
not inferred from literal quote matching. Do not report 100% when there are zero
reviewed items. The evaluator uses explicit anchor fields and approved aliases,
never numeric target values to select a convenient row. Ambiguous matching fails
closed and enters the review queue.

Report micro and study-macro averages, numerators/denominators, field groups,
domain, document quality and version status. Cluster bootstrap intervals at study
family (or shared-sample group) level after enough families are adjudicated; do not
bootstrap individual cells as independent. Include worst-case critical-error
counts. The current CLI reports point/count summaries only; bootstrap and human
timing collection are later evaluation work.

## Initial gates (proposed, not achieved)

- 100% contract validity for accepted records; every present reported cell has
  source evidence and every calculation is reproducible.
- At least 95% usable document yield, 95% precision and 90% recall on adjudicated
  requested records; report uncertainty and exact denominators.
- At least 98% numeric-cell accuracy and 95% independently judged semantic support.
- Zero observed sign flips, source-version swaps or false claims that an unreviewed
  study reports no test in the pilot. Zero observed is not a zero population rate.
- No expansion when evidence, truncation or cost gates fail. Do not loosen gates
  after seeing held-out results. Changes create a new development cycle/test set.

These pilot gates justify a reviewed extraction workflow, not autonomous
publication or unattended meta-analysis. Accuracy of the reference itself remains
a separate uncertainty. Human reference disagreements should be reported.
