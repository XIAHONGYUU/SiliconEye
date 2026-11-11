"""Build/verify this checkpoint's deduplicated tar; run from the repository root.

Restores original runs paths. Never deletes or modifies source evidence.
"""

import hashlib
import json
import tarfile
import tempfile
from pathlib import Path

from silicon_eye.review_sheet import load_package

ROOT = Path.cwd()
OUT = ROOT / "benchmarks/github-checkpoint-2026-11-11"
RUNS = [
    "batch-production-20261109",
    "metal-extent-batch-replay-20261109-final",
    "batch-production-round2-20261109",
    "batch-expanded-20261109",
    "m3-wide-inventory-20261109",
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    files = []
    for name in RUNS:
        for p in (ROOT / "runs" / name).rglob("*"):
            if not p.is_file() or "__pycache__" in p.parts:
                continue
            # The obsolete full-frame trial duplicates the final 140MB package.
            if name == "m3-wide-inventory-20261109" and p.is_relative_to(
                ROOT / "runs" / name / "full"
            ):
                continue
            if p.is_symlink():
                raise ValueError("Symlink not supported: " + str(p))
            files.append(p)
    files.append(ROOT / "runs/batch-tracing-comparison-20261106/algorithm/run.py")
    archive = OUT / "evidence.tar.gz"
    if archive.exists() or list(OUT.glob("evidence.tar.gz.part*")):
        raise ValueError("Archive already exists")
    seen, entries = {}, []
    with tarfile.open(archive, "w:gz", compresslevel=6) as tar:
        for p in sorted(set(files)):
            name = str(p.relative_to(ROOT))
            digest = sha(p)
            info = tar.gettarinfo(p, arcname=name)
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            if digest in seen:
                info.type = tarfile.LNKTYPE
                info.linkname = seen[digest]
                info.size = 0
                tar.addfile(info)
            else:
                with p.open("rb") as stream:
                    tar.addfile(info, stream)
                seen[digest] = name
            entries.append(dict(path=name, sha256=digest, size=p.stat().st_size))
    with tempfile.TemporaryDirectory(prefix="siliconeye-checkpoint-") as tmp:
        restored = Path(tmp)
        with tarfile.open(archive) as tar:
            tar.extractall(restored, filter="data")
        for row in entries:
            assert sha(restored / row["path"]) == row["sha256"], row["path"]
        reviews = [
            "batch-production-20261109/review",
            "batch-production-round2-20261109/package-final/review",
            "batch-expanded-20261109/review-final",
            "m3-wide-inventory-20261109/final/review",
        ]
        for review in reviews:
            load_package(restored / "runs" / review)
    result = dict(
        status="PASS",
        files=len(entries),
        unique_blobs=len(seen),
        restored_files_verified=len(entries),
        restored_review_packages_verified=4,
        archive=dict(
            path=str(archive.relative_to(ROOT)), sha256=sha(archive), size=archive.stat().st_size
        ),
        entries=entries,
    )
    parts = []
    with archive.open("rb") as stream:
        while chunk := stream.read(32 * 1024 * 1024):
            part = OUT / f"evidence.tar.gz.part{len(parts) + 1:02}"
            part.write_bytes(chunk)
            parts.append(dict(path=str(part.relative_to(ROOT)), size=len(chunk), sha256=sha(part)))
    result["archive"]["parts"] = parts
    result["archive"]["path_is_reassembled"] = True
    archive.unlink()
    (OUT / "evidence-manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    print({k: v for k, v in result.items() if k != "entries"})


if __name__ == "__main__":
    main()
