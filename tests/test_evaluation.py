import copy

import pytest
from pydantic import ValidationError

from study_extract.evaluate import (
    ExpectedCell,
    ReferenceRecord,
    ReferenceSet,
    evaluate,
    split_for_study,
)
from study_extract.models import Cell, Extraction


@pytest.fixture
def references(packet):
    return ReferenceSet(
        records=[
            ReferenceRecord(
                reference_id="synthetic-e1",
                study_id="synthetic-study",
                source_sha256=packet.documents[0].sha256,
                kind="estimate",
                anchors={"outcome": ["drinking water"]},
                expected={
                    "value": ExpectedCell(
                        value=-0.2,
                        state="present",
                        evidence_pages=[1],
                        adjudicated=True,
                        reviewer="synthetic fixture",
                        rationale="Original test text defines the value",
                    ),
                    "standard_error": ExpectedCell(value=0.08, state="present", adjudicated=False),
                },
            )
        ]
    )


def test_only_reviewed_cells_are_scored(extraction, packet, references):
    report = evaluate(extraction, references, packet)
    assert report["scored_cells"] == report["correct_cells"] == 1
    assert report["unadjudicated_cells_excluded"] == 1
    assert report["evidence_location_accuracy"] == 1
    assert report["semantic_support_accuracy"] is None


def test_empty_references_have_no_accuracy(extraction, packet):
    report = evaluate(extraction, ReferenceSet(records=[]), packet)
    assert report["cell_accuracy"] is None
    assert report["record_recall"] is None


def test_missing_prediction_is_failure_not_removed_from_denominator(packet, references):
    report = evaluate(Extraction(records=[], coverage=[]), references, packet)
    assert report["cell_accuracy"] == 0
    assert report["scored_cells"] == report["missed_present_cells"] == 1


def test_sign_error_cannot_pass_tolerance(extraction, packet, references):
    extraction.records[0].fields["value"].value = 0.2
    assert evaluate(extraction, references, packet)["cell_accuracy"] == 0


def test_duplicate_predictions_are_ambiguous(extraction, packet, references):
    extra = copy.deepcopy(extraction.records[0])
    extra.record_id = "duplicate-value"
    extraction.records.append(extra)
    report = evaluate(extraction, references, packet)
    assert report["ambiguous_record_matches"] == 1
    assert report["cell_accuracy"] == 0


def test_other_source_version_is_not_a_match(extraction, packet, references):
    references.records[0].source_sha256 = "0" * 64
    assert evaluate(extraction, references, packet)["record_recall"] == 0


def test_ref_missing_is_not_automatically_zero(extraction, packet, references):
    references.records[0].expected["value"] = ExpectedCell(
        value=None, state="not_found", adjudicated=True, reviewer="fixture", rationale="test case"
    )
    report = evaluate(extraction, references, packet)
    assert report["unsupported_present_against_reviewed_missing"] == 1
    extraction.records[0].fields["value"] = Cell(
        value=None, state="not_found", rationale="not located"
    )
    assert evaluate(extraction, references, packet)["cell_accuracy"] == 1


def test_no_automatic_promotion_to_gold():
    with pytest.raises(ValidationError, match="reviewer"):
        ExpectedCell(value=1, state="present", adjudicated=True)


def test_family_split_does_not_depend_on_document_version():
    assert split_for_study("one-family") == split_for_study("one-family")
    assert {split_for_study(f"study-{i}") for i in range(100)} == {"train", "dev", "test"}


def test_provisional_duplicates_do_not_change_scores(extraction, packet, references):
    duplicate = references.records[0].model_copy(deep=True)
    duplicate.reference_id = "unreviewed-duplicate"
    for cell in duplicate.expected.values():
        cell.adjudicated = False
    references.records.append(duplicate)
    assert evaluate(extraction, references, packet)["cell_accuracy"] == 1


@pytest.mark.parametrize(
    "anchors", [{"value": [-0.2]}, {"unknown": ["x"]}, {"outcome": []}, {"p_value": ["<0.05"]}]
)
def test_bad_or_scored_anchors_rejected(references, anchors):
    data = references.records[0].model_dump()
    data["anchors"] = anchors
    if "p_value" in anchors:
        data["expected"]["p_value"] = {"state": "present", "value": "<0.05"}
    with pytest.raises(ValidationError):
        ReferenceRecord.model_validate(data)


def test_reference_wrong_type_rejected(references):
    data = references.records[0].model_dump()
    data["expected"]["value"]["value"] = "-0.2"
    with pytest.raises(ValidationError, match="requires number"):
        ReferenceRecord.model_validate(data)


def test_unscored_p_value_is_not_an_identity_anchor(references):
    data = references.records[0].model_dump()
    data["anchors"] = {"p_value": ["<0.05"]}
    with pytest.raises(ValidationError, match="anchors"):
        ReferenceRecord.model_validate(data)
