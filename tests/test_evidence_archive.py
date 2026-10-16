"""Archive restore must preserve old evidence and reject unsafe/changed inputs."""
import hashlib
import json
import zipfile

import pytest

from silicon_eye.evidence_archive import restore_evidence


def archive(tmp_path, name="runs/review/source.json", data=b"original", digest=None):
    path = tmp_path / "inputs.zip"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(name, data)
        z.writestr("evidence-manifest.json", json.dumps(dict(
            schema_version=1, kind="frozen_evidence", files=[dict(
                path=name, sha256=digest or hashlib.sha256(data).hexdigest(), size=len(data),
            )],
        )))
    return path


def test_restore_is_exact_and_idempotent(tmp_path):
    path = archive(tmp_path)
    assert restore_evidence(path, tmp_path)["restored"] == ["runs/review/source.json"]
    assert (tmp_path / "runs/review/source.json").read_bytes() == b"original"
    assert restore_evidence(path, tmp_path)["already_identical"] == ["runs/review/source.json"]


def test_existing_different_file_is_never_overwritten(tmp_path):
    path = archive(tmp_path)
    dest = tmp_path / "runs/review/source.json"
    dest.parent.mkdir(parents=True)
    dest.write_bytes(b"user data")
    with pytest.raises(ValueError, match="refusing overwrite"):
        restore_evidence(path, tmp_path)
    assert dest.read_bytes() == b"user data"


@pytest.mark.parametrize("name,digest", [("../outside", None), ("runs/file", "0" * 64)])
def test_bad_archive_fails_before_creating_inputs(tmp_path, name, digest):
    path = archive(tmp_path, name=name, digest=digest)
    with pytest.raises(ValueError):
        restore_evidence(path, tmp_path)
    assert not (tmp_path / "runs").exists()
