import pytest
import yaml

from study_extract.cli import main
from study_extract.evaluate import evaluate
from study_extract.io import read_json, write_json
from study_extract.references import EstimateMapping, import_estimates


@pytest.fixture
def coding(packet, tmp_path):
    doc = packet.documents[0]
    path = tmp_path / "coding.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "key": doc.study_id,
                "versions": [{"id": "v1", "file": doc.filename}],
                "estimates": [
                    {"version": "v1", "diff": -0.2, "se": 0.08, "n_obs": None, "preferred": True},
                    {"version": "draft", "diff": 0.9, "se": 0.2},
                ],
            }
        )
    )
    return path


def mapping(index=0):
    return EstimateMapping(index=index, anchors={"outcome": ["drinking water"]})


def test_import_preserves_origin_without_promoting_gold(coding, packet, extraction):
    refs = import_estimates(coding, packet.documents[0], "v1", [mapping()])
    ref = refs.records[0]
    assert ref.origin.pointer == "/estimates/0"
    assert len(ref.origin.artifact_sha256) == 64
    assert set(ref.expected) == {"value", "standard_error"}
    assert all(not c.adjudicated for c in ref.expected.values())
    assert refs.complete_scopes == []
    result = evaluate(extraction, refs, packet)
    assert result["scored_cells"] == 0
    assert result["cell_accuracy"] is None


def test_import_rejects_mixed_version(coding, packet):
    with pytest.raises(ValueError, match="another document version"):
        import_estimates(coding, packet.documents[0], "v1", [mapping(1)])


def test_import_rejects_wrong_source_filename(coding, packet):
    doc = packet.documents[0].model_copy(update={"filename": "other.pdf"})
    with pytest.raises(ValueError, match="filename"):
        import_estimates(coding, doc, "v1", [mapping()])


@pytest.mark.parametrize("indices", [[], [0, 0], [100]])
def test_import_rejects_empty_duplicate_and_missing_mappings(coding, packet, indices):
    with pytest.raises(ValueError):
        import_estimates(coding, packet.documents[0], "v1", [mapping(i) for i in indices])


def test_import_does_not_match_using_target_values(coding, packet):
    with pytest.raises(ValueError, match="anchors"):
        import_estimates(
            coding, packet.documents[0], "v1", [EstimateMapping(index=0, anchors={"value": [-0.2]})]
        )


def test_cli_import_estimates_is_provisional(coding, packet, tmp_path):
    write_json(tmp_path / "packet.json", packet)
    write_json(tmp_path / "mapping.json", [mapping().model_dump()])
    output = tmp_path / "references.json"
    assert (
        main(
            [
                "import-estimates",
                str(coding),
                "--packet",
                str(tmp_path / "packet.json"),
                "--source-id",
                packet.documents[0].source_id,
                "--version",
                "v1",
                "--mapping",
                str(tmp_path / "mapping.json"),
                "--output",
                str(output),
            ]
        )
        == 0
    )
    assert read_json(output)["records"][0]["expected"]["value"]["adjudicated"] is False
