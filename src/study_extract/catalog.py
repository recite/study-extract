"""The field dictionary shared by validation, prompts, and documentation."""

from dataclasses import asdict, dataclass
from typing import Literal

ValueType = Literal["text", "number", "integer", "boolean", "text_list"]


@dataclass(frozen=True)
class FieldSpec:
    type: ValueType
    description: str


def text(description: str) -> FieldSpec:
    return FieldSpec("text", description)


def number(description: str) -> FieldSpec:
    return FieldSpec("number", description)


def integer(description: str) -> FieldSpec:
    return FieldSpec("integer", description)


CATALOG: dict[str, dict[str, FieldSpec]] = {
    "study": {
        "title": text("Title of this report, preserving its version."),
        "authors": FieldSpec("text_list", "Authors as reported."),
        "year": integer("Year of this document version, not the first version of the study."),
        "setting": text("Country, region, institutions, and relevant time period."),
        "research_question": text("Question addressed by this study."),
        "registration": text("Registration/PAP identifier, date, and timing relative to data."),
        "data_availability": text("Reported data availability and exact access restrictions."),
        "code_availability": text("Reported code availability."),
        "funding": text("Funding statement; absence of a located statement is not no funding."),
        "conflicts_of_interest": text("Authors' reported conflict statement."),
    },
    "design": {
        "design_type": text("Reported research design; reviewer classification must be marked."),
        "estimand": text("Target quantity: population, contrast, weighting and time horizon."),
        "target_population": text("Population to which the authors target their claim."),
        "treatment": text("Assigned intervention or exposure, including dose and duration."),
        "comparison": text("Reference condition and treatment contrast orientation."),
        "assignment_unit": text("Unit assigned treatment, separate from observation unit."),
        "assignment_procedure": text("Actual described allocation procedure and constraints."),
        "assignment_pool": text("Pool within which assignment takes place, e.g. block/category."),
        "assignment_probability": text(
            "Reported probabilities, strata, and variation across units."
        ),
        "assignment_category": text(
            "Reservation or treatment category, without inferred splitting."
        ),
        "identifying_assumption": text(
            "Authors' assumption connecting comparison to causal claim."
        ),
        "compliance": text("Assignment versus receipt; first stage and noncompliance handling."),
        "interference": text("Spillover/exposure mapping assumptions and relevant evidence."),
        "attrition": text("Loss to follow-up by arm, denominators, timing, and handling."),
        "preregistered_analysis": text("What was prespecified and how timing is established."),
        "analysis_deviations": text(
            "Reported departures from plan; do not infer undisclosed intent."
        ),
        "running_variable": text("RD running variable, scale, and threshold."),
        "bandwidth": text("RD bandwidth, selection method, kernel and polynomial order."),
        "instrument": text("IV instrument and authors' relevance/exclusion arguments."),
        "treatment_timing": text("Timing/cohorts, anticipation and comparison periods for DiD."),
    },
    "sample": {
        "population": text("Population actually sampled or analyzed."),
        "geography": text("Geographic scope, preserving state/district/market distinctions."),
        "period": text("Collection/coverage dates, not publication date."),
        "sampling_method": text("Sampling frame, selection and representativeness claims."),
        "observation_unit": text("Unit counted as an observation."),
        "n_observations": integer("Observation count in this exact sample."),
        "n_units": integer("Distinct substantive units; not automatically independent."),
        "n_assigned": integer("Units assigned, before exclusions/attrition."),
        "n_treated": integer("Treated units in the stated denominator."),
        "n_control": integer("Control units in the stated denominator."),
        "n_clusters": integer("Total clusters in this sample."),
        "n_treated_clusters": integer("Treated clusters, when explicitly reported."),
        "exclusions": text("Eligibility and analysis exclusions with timing and reasons."),
        "weights": text("Sampling/analysis weights and their target population."),
        "overlap": text("Shared people, sites, controls, or data with other records/studies."),
    },
    "outcome": {
        "name": text("Reported outcome name."),
        "construct": text("Concept intended to be measured; separate from operational measure."),
        "definition": text("Exact operational definition, question wording or coding rules."),
        "family": text("Outcome family; analyst harmonization is a reviewer judgment."),
        "data_source": text("Survey, administrative record, audit, media coding, etc."),
        "instrument": text("Question, scale, coder procedure or measurement instrument."),
        "units": text("Units and scale: counts, proportions, percent, pp, logs, etc."),
        "direction": text("Meaning of larger values, without changing the reported sign."),
        "timepoint": text("Measurement period or follow-up after treatment."),
        "numerator": text("Who/what is counted in a share; event/person/story distinction."),
        "denominator": text(
            "Exact eligible population, including treatment of unknown categories."
        ),
        "missing_handling": text("Unknown race, missing outcomes, imputation and exclusions."),
        "reliability": text("Coder agreement or measurement reliability, sample and metric."),
        "primary_status": text("Authors' primary/secondary/exploratory designation and basis."),
    },
    "estimate": {
        "outcome": text("Outcome label for this estimate, preserving subgroup and scale."),
        "estimand": text("ATE/ITT/LATE/ATT/association/share/mean/etc.; do not infer causality."),
        "population": text("Exact sample/subgroup for the reported quantity."),
        "contrast": text(
            "Treatment minus control or other orientation; descriptive if no contrast."
        ),
        "timepoint": text("Outcome measurement time for this estimate."),
        "specification": text(
            "Model, table column, estimator, adjustments and sample restrictions."
        ),
        "measure": text("Coefficient, mean difference, proportion, RR, OR, log OR, etc."),
        "value": number("Signed estimate in the paper's units; never harmonize silently."),
        "units": text("Exact reported units, retaining percent versus percentage points."),
        "standard_error": number("SE, not SD or interval width; no inference from stars."),
        "standard_deviation": number(
            "SD of the variable, distinct from uncertainty of the estimate."
        ),
        "interval_lower": number("Reported lower endpoint on the stated scale."),
        "interval_upper": number("Reported upper endpoint on the stated scale."),
        "interval_level": number("Coverage/credibility level as a fraction, e.g. 0.95."),
        "interval_type": text("Confidence/credible/prediction; method and sidedness."),
        "p_value": text("Preserve inequalities and rounding, e.g. <0.001 or 0.000."),
        "test_statistic": number("Reported t/z/F/chi-square statistic; type belongs in test_type."),
        "test_type": text("Test/statistic type, null, sidedness and reference distribution."),
        "degrees_of_freedom": number("Reported df; never replace with N or cluster count."),
        "n_observations": integer("Exact estimation sample, not full-study N."),
        "n_clusters": integer("Exact cluster count for this estimate."),
        "uncertainty_method": text(
            "Robust/clustered/RI/bootstrap/Bayesian, corrections and level."
        ),
        "cluster_unit": text("Clustering unit(s), separate from assignment unit."),
        "covariates": FieldSpec("text_list", "Adjustment variables including potential mediators."),
        "fixed_effects": FieldSpec("text_list", "Reported fixed effects."),
        "weights": text("Weighting used in this specification."),
        "control_mean": number("Control mean for the same sample/outcome/time."),
        "control_sd": number("Control SD for the same sample/outcome/time."),
        "multiplicity": text("Adjustment, family and prespecified/exploratory status."),
        "preferred": FieldSpec(
            "boolean", "Authors explicitly designate this specification preferred."
        ),
        "dependence_group": text(
            "Shared sample/control/outcome dependence; judgment when inferred."
        ),
    },
    "diagnostic": {
        "assumption": text("Assumption or implementation question addressed."),
        "diagnostic_type": text("Balance, reconstruction, transitions, density, pretrends, etc."),
        "procedure": text("Test actually performed, separate from recommended tests."),
        "sample": text("Diagnostic sample, period, groups and geographic resolution."),
        "null_hypothesis": text("Null actually tested; not every check has a statistical null."),
        "statistic": number("Reported diagnostic statistic."),
        "statistic_type": text("Statistic type and units."),
        "p_value": text("Reported p-value including bounds/rounding."),
        "n_observations": integer("Sample used in this diagnostic."),
        "n_groups": integer("Number of assignment/geographic groups used."),
        "authors_interpretation": text("What authors conclude, retaining qualifications."),
        "scope_limit": text("What the test does not address; mark reviewer judgments."),
        "replication_status": text("Located, source-rechecked or reproduced; evidence for status."),
    },
    "claim": {
        "text": text("Authors' claim in context, including qualifications."),
        "claim_type": text("Finding, mechanism, identifying premise, normative or contextual."),
        "mechanism": text("Proposed mechanism; distinguish a label from its empirical test."),
        "evidence_status": text(
            "Asserted, speculated, tested, or mixed; give the coding rationale."
        ),
        "stance": text("Normative stance when authors state one, not the reviewer's preference."),
        "scope": text("Population, place, period, office/category and applicable conditions."),
        "support": text("Own test, theoretical argument, legal rule or prior-study citation."),
        "qualification": text("Limits and counterevidence stated alongside the claim."),
    },
    "comparison": {
        "quantity": text("What is compared, e.g. Black perpetrator share."),
        "observed_value": number("Reported study value in stated units."),
        "benchmark_value": number("Reported comparison value in stated units."),
        "units": text("Units of both values; mismatch must remain explicit."),
        "benchmark_source": text("Arrests, victimization, population or other comparison source."),
        "observed_denominator": text(
            "Denominator and missing-category handling for observed value."
        ),
        "benchmark_denominator": text("Benchmark denominator; arrests are not all offending."),
        "observed_scope": text("Observed geography, time, crime types and population."),
        "benchmark_scope": text("Benchmark geography, time, crime types and population."),
        "comparability": text("Authors' qualification or explicitly labeled reviewer assessment."),
    },
}


def catalog_json() -> dict[str, dict[str, dict[str, str]]]:
    return {
        kind: {name: asdict(spec) for name, spec in fields.items()}
        for kind, fields in CATALOG.items()
    }
