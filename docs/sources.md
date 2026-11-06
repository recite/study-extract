# Source ledger and crosswalk

Consulted 2026-11-05. Local repositories were read only. Original PDFs, reference
annotations and manuscripts have not been uploaded to a model service by this
project's development work.

| Source | Contribution to the design |
|---|---|
| quota_spending/lit/coding/BRIEF.md | Mechanisms, normative claims, measurement, estimates, verbatim evidence, printed pages, versions |
| quota_spending/lit/studies/*.yaml | Per-cell audit status, proposals and author decisions |
| quota_assignment/docs/literature_audit_protocol.md | Assumption/diagnostic links, family grouping, missing versus reviewed absence, scoped disagreement |
| quota_assignment/data/reference/literature_audit/schema.json | Typed diagnostics, results, source families and review decisions |
| face_of_crime/data/reference/literature.csv | Media, place, period, group shares, benchmarks and denominator ambiguities |
| [Paperclip](https://paperclip.gxl.ai/docs) | Parallel document reading, JSON Schema, per-value citations and uploaded corpora |
| [Paperclip Datasets](https://gxl.ai/blog/introducing-paperclip-datasets/) | User-defined row unit and columns, evidence inspection, refreshable extraction |
| [Green Lab SOP v1.05](https://alexandercoppock.com/Green-Lab-SOP/Green_Lab_SOP.html) | Implementation, inference, compliance, attrition and transparency |
| [Gerber–Green companion materials](https://isps.yale.edu/field-experiments-design-analysis-and-interpretation) | Book identity and reproducible companion data; full book not read in this review |
| [Gelman–Carlin](https://sites.stat.columbia.edu/gelman/research/published/retropower_final.pdf) | Sign/magnitude risk and externally specified plausible effect sizes |
| [Gelman–Loken](https://stat.columbia.edu/~gelman/research/unpublished/forking.pdf) | Analysis contingencies and multiplicity beyond counted tests |
| [Cochrane chapter 5](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-05) | Studies versus reports, data forms, extraction and reconciliation |

## Known reference limitations

The quota_assignment report describes 70 source versions and 50 families, with
36 provisionally included empirical studies, 7 verified family mappings, and zero
completed eligible reviews. Its positive diagnostic extractions are useful;
the absence of a diagnostic record is not an absence label. Those numbers describe
the inspected snapshot, not permanent facts.

The quota_spending corpus has 48 local PDFs and 23 study/coding records. The coding
brief mixes source facts and methodological judgments. Existing flags and reviewer
notes must travel into the reference inventory. The crime table summarizes eight
studies but does not supply a complete page-level reference annotation for every
quantity. It is a seed for adjudication, not a ready benchmark.

## Implementation documentation

- [Pydantic models](https://docs.pydantic.dev/latest/concepts/models/)
- [pypdf text extraction](https://pypdf.readthedocs.io/en/stable/user/extract-text.html)
- [Codex noninteractive command](https://learn.chatgpt.com/docs/developer-commands#codex-exec)
- GitHub Actions release pages checked: checkout v7.0.1; setup-uv v10.3.3.

Source excerpts are not redistributed here. Project-specific reference imports
stay in ignored local directories and retain a hash of their source annotations.
