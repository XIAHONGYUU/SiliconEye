"""Restore explicitly archived evidence without altering existing records.

Run: python -m silicon_eye.evidence_archive --archive inputs.zip --root .
Requires Python standard library only. Identical existing files are skipped.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


def restore_evidence(archive: str | Path, root: str | Path) -> dict:
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError("Evidence root must already exist")
    planned, skipped = [], []
    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate archive members")
        manifest = json.loads(bundle.read("evidence-manifest.json"))
        if manifest.get("schema_version") != 1 or manifest.get("kind") != "frozen_evidence":
            raise ValueError("Unsupported evidence archive")
        entries = manifest["files"]
        if not entries or len({e["path"] for e in entries}) != len(entries):
            raise ValueError("Empty or duplicate evidence inventory")
        if set(names) != {"evidence-manifest.json", *(e["path"] for e in entries)}:
            raise ValueError("Archive members differ from declared inventory")
        for entry in entries:
            name = entry["path"]
            relative = PurePosixPath(name)
            if relative.is_absolute() or ".." in relative.parts or "\\" in name:
                raise ValueError("Unsafe evidence path")
            path = (root / name).resolve()
            if not path.is_relative_to(root) or path == root:
                raise ValueError("Evidence destination escapes root")
            mode = bundle.getinfo(name).external_attr >> 16
            if stat.S_ISLNK(mode):
                raise ValueError("Symlink archive members are not allowed")
            data = bundle.read(name)
            if len(data) != entry["size"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
                raise ValueError("Archived evidence hash/size mismatch: " + name)
            if path.exists():
                if not path.is_file() or path.read_bytes() != data:
                    raise ValueError("Existing evidence differs; refusing overwrite: " + name)
                skipped.append(name)
            else:
                planned.append((name, path, data))
    # All contents and existing destinations are checked before any file is created.
    for _name, path, data in planned:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
        try:
            os.link(temporary, path)  # Exclusive publication, never overwrite a racing writer.
        finally:
            temporary.unlink()
    return {"restored": [name for name, _, _ in planned], "already_identical": skipped}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True)
    parser.add_argument("--root", required=True)
    args = parser.parse_args()
    try:
        result = restore_evidence(args.archive, args.root)
    except (ValueError, OSError, KeyError, zipfile.BadZipFile) as error:
        parser.exit(1, f"Evidence restore failed: {error}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
