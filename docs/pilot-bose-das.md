# Bose–Das development pilot

This is a source-grounded, assistant-authored example, not a successful autonomous
Codex run or an independent accuracy benchmark. It exercises the extraction
contract and reference workflow on a real paper.

## Source and method

Bose and Das (2018), [Political reservation for women and delivery of public works
program](https://doi.org/10.1111/rode.12336), Review of Development Economics
22:203–219. Source SHA-256:
`edff6a779e9e920a0e9ef35defa42b361df11d0a8babc6250432172a775ebd1d`.

The assistant read the 18-page supplied PDF's extracted text and visually inspected
Tables 4–6 on PDF pages 10, 12 and 13 (printed pages 212, 214 and 215). A local,
source-specific authoring script transcribed the six columns of each selected row.
It is not part of the general extraction software. The response was frozen and
hashed before inspecting the existing Bose–Das coding YAML. Source highlights
were visible; this is development material, not an untouched test study.

The separate Codex adapter was attempted using the existing ChatGPT login and
configured `gpt-6-astra` model. Local app-server initialization failed with
`Operation not permitted`. No response or usage report was produced. The three
remaining papers were not submitted. No account or billing-provider switch was made.

## Output

- 134 records: one study, one design, six broad sample groups, 18 outcomes and
  108 regression estimates covering every coefficient in Tables 4–6.
- 3,720 fields: 1,780 present, 1,934 not found, six not applicable. Missing fields
  retain explanations. The overlapping sample-group records deliberately have
  no single observation count; each estimate carries its exact reported N.
- 3,244 evidence spans pass literal document/page checks. Spans include repeated
  headers and footnotes; this is not 3,244 independent pieces of evidence.
- All records pass the core-profile field contract. Semantic support remains
  unadjudicated. Table 1–2 descriptive statistics and Table 3 diagnostics are
  explicitly outside this output's scope.

Selected entries illustrate the distinctions retained:

| Outcome | Sample / column | Coefficient | SE | Observations | Scale |
|---|---|---:|---:|---:|---|
| Job cards | Phase I, full; T4 c1 | 0.039 | 0.013 | 9,797 | Log units |
| Female person-days | Phase I, full; T4 c1 | 0.048 | 0.034 | 9,797 | Log units |
| Water control/harvesting | Phase I, full; T5 c1 | 0.027 | 0.028 | 8,613 | Log number of works |
| Water control/harvesting | Phase I, not reserved in 2005; T5 c2 | 0.069 | 0.039 | 4,907 | Log number of works |
| SC/ST irrigation | Phase I, full; T5 c1 | -0.055 | 0.039 | 7,401 | Log number of works |
| SC/ST irrigation | Phase I, full; T6 c1 | -41.790 | 15.550 | 3,848 | Works per lakh rupees |

These quantities must not be pooled as if their outcomes, populations and units
were identical. Reported significance-star thresholds are preserved; the pipeline
does not recompute exact p-values, infer degrees of freedom, or turn observations
into cluster counts.

One source consistency issue is retained for review: Table 5 reports N = 7,214
for Phase I drought-proofing, while its two 2005-status subgroup Ns are 3,967 and
3,274 (sum 7,241). These values were checked against the rendered page and kept
as printed. The discrepancy needs a source/data check; the extractor does not
silently replace any count or infer an explanation.

## Existing coding comparison

Six published-version coding rows were mapped by outcome, sample and table-column
identity. All 18 available numeric targets (coefficient, SE and N) agree with the
frozen extraction. Two draft-version rows were excluded. This is provisional
agreement, not 100% model accuracy: one study, selected references, assistant
authoring, and no independent adjudicator.

The importer writes unadjudicated references with original coding-file hash and
row pointers. The normal evaluator correctly reports **zero scored gold cells**
and null accuracy until adjudication. Missing reference labels do not become
negative findings. Existing `preferred` labels describe coding choices and are
not imported into the field reserved for explicit author preferences.

## Local artifacts and next run

Private artifacts are in ignored `local/assisted-bose/`:
`response.json`, `cells.csv`, `review.html`, `packet.json`, `verification.json`,
`provenance.json`, `reference-mapping.json`, `reference-candidates.json`,
`provisional-comparison.json`, and `evaluation.json`.

Once the workspace permits launching Codex, run the autonomous adapter in a new
output directory and compare its unedited response against this development
example and the adjudicated reference subset:

```sh
uv run study-extract extract local/bose-das-packet.json --model gpt-6-astra --execute --max-documents 1 --timeout 600 --output local/autonomous-bose
```

The user has authorized continuing this small pilot with the existing account.
Do not switch to an API billing account or scale to the remaining corpus merely
because the first process was blocked. Inspect the first successful output before
expanding, retain failures and usage, and keep this assisted example out of any
claim about autonomous extraction accuracy.
