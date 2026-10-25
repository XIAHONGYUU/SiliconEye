"""Restore-before-delete guarantees for the optional local run archive."""

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "workspace_archive", Path(__file__).resolve().parents[1] / "scripts/workspace_archive.py"
)
archive_tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(archive_tool)


@pytest.fixture
def workspace(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    (root / "runs").mkdir()
    return root, tmp_path / "archive"


def file(root, name, content=b"pixels"):
    p = root / "runs" / name / "image.png"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(content)
    return p


def test_only_unreferenced_untracked_regular_runs_are_candidates(workspace):
    root, archive = workspace
    file(root, "tracked")
    file(root, "referenced")
    file(root, "inactive")
    file(root, "linked")
    (root / "runs/linked/link").symlink_to(root / "runs/inactive/image.png")
    (root / "guide.md").write_text("Keep runs/referenced/image.png")
    subprocess.run(["git", "add", "runs/tracked"], cwd=root, check=True)
    m = archive_tool.plan(root, archive)
    assert [r["name"] for r in m["runs"]] == ["inactive"]
    assert "linked" in m["skipped_symlink_runs"]
    assert (root / "runs/inactive/image.png").is_file()


def test_deduplicated_backup_roundtrip_and_no_overwrite(workspace):
    root, archive = workspace
    file(root, "one", b"same-image")
    file(root, "two", b"same-image")
    archive_tool.plan(root, archive)
    m = archive_tool.apply(root, archive)
    assert m["stored_bytes"] == len(b"same-image")
    assert m["deduplicated_bytes"] == len(b"same-image")
    assert archive_tool.verify(archive) == 1
    assert not (root / "runs/one").exists()
    archive_tool.restore(root, archive, "one")
    assert (root / "runs/one/image.png").read_bytes() == b"same-image"
    archive_tool.restore(root, archive, "one")  # A matching interrupted restore can resume.
    (root / "runs/one/image.png").write_bytes(b"user-new-content")
    with pytest.raises(ValueError, match="overwrite"):
        archive_tool.restore(root, archive, "one")
    assert (root / "runs/one/image.png").read_bytes() == b"user-new-content"


def test_new_reference_or_changed_file_blocks_removal(workspace):
    root, archive = workspace
    file(root, "old")
    archive_tool.plan(root, archive)
    (root / "new.md").write_text("now needed: runs/old/image.png")
    with pytest.raises(ValueError, match="now referenced"):
        archive_tool.apply(root, archive)
    (root / "new.md").unlink()
    (root / "runs/old/image.png").write_bytes(b"changed")
    with pytest.raises(ValueError, match="changed since plan"):
        archive_tool.apply(root, archive)
    assert (root / "runs/old/image.png").read_bytes() == b"changed"


def test_missing_or_corrupt_backup_never_restores(workspace):
    root, archive = workspace
    file(root, "old")
    m = archive_tool.plan(root, archive)
    archive_tool.apply(root, archive)
    obj = archive / "objects" / m["runs"][0]["files"][0]["sha256"]
    obj.write_bytes(b"bad-backup")
    with pytest.raises(ValueError, match="changed backup"):
        archive_tool.restore(root, archive, "old")
    assert not (root / "runs/old").exists()


def test_deletion_phase_can_resume_from_verified_backup(workspace):
    root, archive = workspace
    file(root, "old")
    archive_tool.plan(root, archive)
    archive_tool.apply(root, archive)
    m = archive_tool.load(archive)
    m["status"] = "backed_up"
    (archive / "manifest.json").write_text(json.dumps(m))
    # Simulate a disconnect with one original file still present.
    file(root, "old")
    assert archive_tool.apply(root, archive)["status"] == "archived"
    assert not (root / "runs/old").exists()
    archive_tool.restore(root, archive, "old")
    assert (root / "runs/old/image.png").read_bytes() == b"pixels"


def test_path_escape_in_archive_manifest_is_rejected(workspace):
    root, archive = workspace
    file(root, "old")
    m = archive_tool.plan(root, archive)
    m["runs"][0]["files"][0]["path"] = "../../outside"
    (archive / "manifest.json").write_text(json.dumps(m))
    with pytest.raises(ValueError, match="Invalid archive file"):
        archive_tool.apply(root, archive)


def test_retained_run_dependencies_are_protected_transitively(workspace):
    root, archive = workspace
    file(root, "active")
    file(root, "required")
    file(root, "unused")
    (root / "guide.md").write_text("runs/active/image.png")
    (root / "runs/active/manifest.json").write_text('{"source":"runs/required/image.png"}')
    m = archive_tool.plan(root, archive)
    assert {r["name"] for r in m["runs"]} == {"unused"}
