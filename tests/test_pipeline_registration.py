import json

import pytest

from silicon_eye.config import ChipConfig, ChipDef, LayerDef, TileConfig
from silicon_eye.pipeline import Pipeline


def configuration():
    return ChipConfig(
        chip=ChipDef(name="chip"),
        layers=[
            LayerDef(name="aa", index=0),
            LayerDef(name="poly", index=1),
            LayerDef(name="m1", index=2),
        ],
        tiles=[TileConfig(id="tile")],
    )


def pipeline(tmp_path):
    return Pipeline(configuration(), str(tmp_path / "data"), str(tmp_path / "run"))


def test_data_root_jpeg_resolution_skips_unselected_layers(tmp_path):
    source = tmp_path / "data/chip/tile"
    source.mkdir(parents=True)
    for name in ["aa", "poly"]:
        (source / f"{name}.jpg").write_bytes(b"path resolution fixture, not decoded")
    result = pipeline(tmp_path)._build_tile_set(selected_layers={"aa", "poly"})
    assert [image.path for image in result.tiles[0].images] == [
        str(source / "aa.jpg"),
        str(source / "poly.jpg"),
    ]


@pytest.mark.parametrize("defect", ["missing", "ambiguous", "unconfigured"])
def test_path_resolution_fails_without_fabricated_png(tmp_path, defect):
    source = tmp_path / "data/chip/tile"
    source.mkdir(parents=True)
    names = {"aa"}
    if defect == "ambiguous":
        (source / "aa.jpg").touch()
        (source / "aa.png").touch()
    if defect == "unconfigured":
        names = {"unknown"}
    with pytest.raises((ValueError, FileNotFoundError)):
        pipeline(tmp_path)._build_tile_set(selected_layers=names)


@pytest.mark.parametrize("stages", [[], ["unknown"], ["phase1", "phase1"]])
def test_invalid_stage_plan_rejected(tmp_path, stages):
    job = pipeline(tmp_path)
    with pytest.raises(ValueError, match="stages"):
        job.run(stages)
    assert not (job.run_dir / "pipeline_manifest.json").exists()


def test_registration_requires_explicit_case(tmp_path):
    job = pipeline(tmp_path)
    with pytest.raises(ValueError, match="requires"):
        job.run(["registration"])


def test_unimplemented_segmentation_blocks_downstream_without_checkpoints(tmp_path):
    job = pipeline(tmp_path)
    result = job.run()
    assert result["phase1"]["status"] == "blocked"
    assert result["phase2"]["status"] == "blocked"
    assert json.loads((job.run_dir / "pipeline_manifest.json").read_text())["status"] == "blocked"
    assert not (job.run_dir / "phase1_devices.json").exists()
    assert not (job.run_dir / "netlist.spice").exists()


def test_candidate_registration_cannot_authorize_device_extraction(tmp_path, monkeypatch):
    job = pipeline(tmp_path)
    monkeypatch.setattr(
        job,
        "_run_registration",
        lambda _: {"status": "candidate", "acceptance": "unknown", "numeric_budget_met": True},
    )
    result = job.run(["phase2", "phase1", "registration"], registration_spec="explicit.json")
    assert list(result) == ["registration", "phase1", "phase2"]
    assert result["phase1"]["reason"] == "registration_not_confirmed"
    assert result["phase2"]["status"] == "blocked"
    assert not (job.run_dir / "phase1_devices.json").exists()


def test_registration_failure_is_recorded_and_downstream_blocked(tmp_path):
    job = pipeline(tmp_path)
    result = job.run(
        ["registration", "phase1", "phase2"], registration_spec=str(tmp_path / "missing.json")
    )
    assert result["registration"]["status"] == "failed"
    assert result["phase1"]["status"] == "blocked"
    assert result["phase2"]["status"] == "blocked"
    assert json.loads((job.run_dir / "pipeline_manifest.json").read_text())["status"] == "failed"


def test_output_cannot_overwrite_or_enter_source_data(tmp_path):
    job = pipeline(tmp_path)
    with pytest.raises(FileExistsError):
        Pipeline(configuration(), str(tmp_path / "data"), str(job.run_dir))
    with pytest.raises(ValueError, match="source data"):
        Pipeline(configuration(), str(tmp_path / "data"), str(tmp_path / "data/result"))
    assert not (tmp_path / "data/result").exists()
