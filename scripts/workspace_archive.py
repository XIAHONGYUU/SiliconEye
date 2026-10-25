"""Archive unreferenced, untracked run directories into a reversible deduplicated store.

Usage: python scripts/workspace_archive.py plan|apply|verify|restore --archive PATH
       --root REPO [--run RUN_NAME]
Requires Python and git. Only runs/ may be removed, after every file is hash-verified
in the archive; referenced/tracked runs and symlinks are protected. No git history edits.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
from pathlib import Path


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git_files(root):
    return [
        p
        for p in subprocess.check_output(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=root
        )
        .decode()
        .split("\0")
        if p
    ]


def protected_runs(root):
    tracked = subprocess.check_output(["git", "ls-files", "-z", "runs"], cwd=root).decode()
    protected = set(re.findall(r"runs/([A-Za-z0-9_.-]+)", tracked))
    suffixes = {".py", ".md", ".json", ".yaml", ".yml", ".html", ".js", ".toml", ".csv", ".txt"}
    for name in git_files(root):
        p = root / name
        if name.startswith("runs/") or p.suffix.lower() not in suffixes or not p.is_file():
            continue
        protected.update(re.findall(r"runs/([A-Za-z0-9_.-]+)", p.read_text(errors="replace")))
    # A retained package can itself refer to another run; keep that dependency closure.
    visited = set()
    while pending := protected - visited:
        for name in pending:
            visited.add(name)
            directory = root / "runs" / name
            if directory.is_symlink() or not directory.is_dir():
                continue
            for p in directory.rglob("*"):
                if p.is_file() and not p.is_symlink() and p.suffix.lower() in suffixes:
                    protected.update(
                        re.findall(r"runs/([A-Za-z0-9_.-]+)", p.read_text(errors="replace"))
                    )
    return protected


def write_manifest(archive, manifest):
    temp = archive / "manifest.tmp"
    temp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    temp.replace(archive / "manifest.json")


def plan(root, archive):
    root, archive = root.resolve(), archive.resolve()
    if archive.is_relative_to(root) or (archive / "manifest.json").exists():
        raise ValueError("Use a new archive directory outside the repository")
    protected = protected_runs(root)
    runs, skipped = [], []
    for directory in sorted((root / "runs").iterdir()):
        if not directory.is_dir() or directory.name in protected:
            continue
        paths = sorted(directory.rglob("*"))
        if directory.is_symlink() or any(p.is_symlink() for p in paths):
            skipped.append(directory.name)
            continue
        files = []
        for p in paths:
            if not p.is_file():
                continue
            info = p.stat()
            files.append(
                dict(
                    path=str(p.relative_to(directory)),
                    sha256=sha(p),
                    size=info.st_size,
                    mode=stat.S_IMODE(info.st_mode),
                    mtime_ns=info.st_mtime_ns,
                )
            )
        runs.append(dict(name=directory.name, files=files))
    manifest = dict(
        schema_version=1,
        root=str(root),
        archive=str(archive),
        status="planned",
        protected_runs=sorted(protected),
        skipped_symlink_runs=skipped,
        runs=runs,
    )
    archive.mkdir(parents=True, exist_ok=True)
    write_manifest(archive, manifest)
    return manifest


def load(archive):
    archive = archive.resolve()
    m = json.loads((archive / "manifest.json").read_text())
    if m["archive"] != str(archive):
        raise ValueError("Archive identity mismatch")
    for run in m["runs"]:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", run["name"]) or run["name"] in {".", ".."}:
            raise ValueError("Invalid run name")
        for f in run["files"]:
            path = Path(f["path"])
            if (
                path.is_absolute()
                or ".." in path.parts
                or not re.fullmatch("[a-f0-9]{64}", f["sha256"])
            ):
                raise ValueError("Invalid archive file identity")
    return m


def verify(archive, manifest=None):
    m = manifest or load(archive)
    seen = set()
    for run in m["runs"]:
        for f in run["files"]:
            key = f["sha256"]
            if key in seen:
                continue
            p = archive / "objects" / key
            if p.is_symlink() or not p.is_file() or p.stat().st_size != f["size"] or sha(p) != key:
                raise ValueError("Missing or changed backup object: " + key)
            seen.add(key)
    return len(seen)


def apply(root, archive):
    root, archive = root.resolve(), archive.resolve()
    m = load(archive)
    if (
        (root / "runs").is_symlink()
        or str(root) != m["root"]
        or m["status"] not in {"planned", "backed_up"}
    ):
        raise ValueError("Wrong root or archive already applied")
    names = {r["name"] for r in m["runs"]}
    if names & protected_runs(root):
        raise ValueError("A proposed run is now referenced; make a fresh plan")
    objects = archive / "objects"
    objects.mkdir(exist_ok=True)
    for run in m["runs"]:
        directory = root / "runs" / run["name"]
        actual = {str(p.relative_to(directory)) for p in directory.rglob("*") if p.is_file()}
        expected = {f["path"] for f in run["files"]}
        if (
            actual != expected if m["status"] == "planned" else not actual <= expected
        ) or directory.is_symlink():
            raise ValueError("Run file list changed since plan")
        for f in run["files"]:
            source = directory / f["path"]
            if not source.exists() and m["status"] == "backed_up":
                continue
            if source.is_symlink() or sha(source) != f["sha256"]:
                raise ValueError("Run file changed since plan")
            dest = objects / f["sha256"]
            if not dest.exists():
                temp = objects / (f["sha256"] + ".partial")
                shutil.copyfile(source, temp)
                if sha(temp) != f["sha256"]:
                    raise ValueError("File changed while being copied")
                temp.replace(dest)
    verify(archive, m)  # Complete backup must exist before any original is removed.
    m["status"] = "backed_up"
    write_manifest(archive, m)
    for run in m["runs"]:
        directory = root / "runs" / run["name"]
        if not directory.exists():
            continue
        for f in run["files"]:
            source = directory / f["path"]
            if not source.exists():
                continue
            if sha(source) != f["sha256"]:
                raise ValueError("Run changed during backup; preserving remaining source")
            source.unlink()
        for p in sorted(directory.rglob("*"), key=lambda p: len(p.parts), reverse=True):
            if p.is_dir():
                p.rmdir()
        directory.rmdir()
    m["status"] = "archived"
    m["logical_bytes"] = sum(f["size"] for r in m["runs"] for f in r["files"])
    m["stored_bytes"] = sum(p.stat().st_size for p in objects.iterdir())
    m["deduplicated_bytes"] = m["logical_bytes"] - m["stored_bytes"]
    write_manifest(archive, m)
    return m


def restore(root, archive, name):
    root, archive = root.resolve(), archive.resolve()
    m = load(archive)
    run = next((r for r in m["runs"] if r["name"] == name), None)
    if run is None or str(root) != m["root"]:
        raise ValueError("Unknown run or wrong root")
    dest = root / "runs" / name
    if (root / "runs").is_symlink() or dest.is_symlink():
        raise ValueError("Restore destination must not be a symlink")
    verify(archive, dict(m, runs=[run]))
    expected = {f["path"]: f for f in run["files"]}
    for p in dest.rglob("*"):
        key = str(p.relative_to(dest))
        if p.is_symlink() or (
            p.is_file() and (key not in expected or sha(p) != expected[key]["sha256"])
        ):
            raise ValueError("Restore would overwrite changed or unexpected files")
    dest.mkdir(exist_ok=True)
    for f in run["files"]:
        path = dest / f["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            shutil.copyfile(archive / "objects" / f["sha256"], path)
        path.chmod(f["mode"])
        os.utime(path, ns=(f["mtime_ns"], f["mtime_ns"]))
        if sha(path) != f["sha256"]:
            raise ValueError("Restore hash mismatch")
    return run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["plan", "apply", "verify", "restore"])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--run")
    args = parser.parse_args()
    if args.mode == "plan":
        result = plan(args.root, args.archive)
    elif args.mode == "apply":
        result = apply(args.root, args.archive)
    elif args.mode == "restore":
        result = restore(args.root, args.archive, args.run)
    else:
        print("Verified unique backup objects:", verify(args.archive))
        return
    runs = result.get("runs", [result])
    print(
        json.dumps(
            dict(
                status=result.get("status", "restored"),
                runs=len(runs),
                bytes=sum(f["size"] for r in runs for f in r["files"]),
                stored_bytes=result.get("stored_bytes"),
            ),
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
