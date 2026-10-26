"""Audit a source-visible conductor ledger and render its native-coordinate review.

Run: python -m silicon_eye.conductive_inventory --inventory FILE --output runs/NEW_DIR
Uses existing project dependencies and conductive workflow. No image recognition,
cross-frame registration, design reconstruction or connection inference is performed.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import tempfile
from collections import Counter
from pathlib import Path
from string import Template

from PIL import Image, ImageChops
from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union

from .conductive_workflow import prepare
from .geometry_reconstruction import digest
from .review_package import Inputs


def require(value, message):
    if not value:
        raise ValueError(message)


def audit(root, inventory):
    root, inputs = Path(root).resolve(), Inputs(root)
    require(
        inventory["kind"] == "conductive_visible_inventory" and inventory["schema_version"] == 1,
        "Unsupported visible inventory",
    )
    for flag in (
        "complete_physical_inventory",
        "full_geometry_reconstruction_complete",
        "canonical_geometry_adopted",
        "complete_network",
        "automatic_network_export_allowed",
    ):
        require(inventory[flag] is False, "Visible ledger cannot authorize completion or adoption")
    scope = inventory["scope"]
    require(
        scope["source_to_design_transform"] is None
        and scope["cross_frame_projection_allowed"] is False,
        "Unqualified cross-frame projection",
    )
    baseline = inputs.document(inventory["baseline"]["model"])
    inputs.document(inventory["baseline"]["manifest"])
    model, _, _, snapshot, files = prepare(
        root, inputs.document(inventory["baseline"]["next_request"])
    )
    inputs.files.update(files)
    require(model == baseline, "Baseline continuation changed")
    domains = {}
    for frame, source in scope["frames"].items():
        require(source["photo"] == snapshot["source_photos"][frame], "Wrong source photograph")
        inputs.read(source["photo"])
        bounds = source["native_bounds"]
        require(
            len(bounds) == 4
            and all(math.isfinite(v) for v in bounds)
            and bounds[0] < bounds[2]
            and bounds[1] < bounds[3],
            "Invalid scope bounds",
        )
        with Image.open(root / source["photo"]["path"]) as photo:
            require(
                box(0, 0, photo.width, photo.height).covers(box(*bounds)),
                "Scope outside source photo",
            )
            inputs.read(source["raw_review_asset"])
            with Image.open(root / source["raw_review_asset"]["path"]) as raw:
                crop = photo.crop(bounds).convert("RGB")
                require(
                    crop.size == raw.size
                    and ImageChops.difference(crop, raw.convert("RGB")).getbbox() is None,
                    "Review asset differs from native photo crop",
                )
        domains[frame] = box(*bounds)

    metals = inventory["metal_observations"]
    interfaces = inventory["inherited_interfaces"]
    unknowns = inventory["unknown_observations"]
    records = metals + interfaces + unknowns
    indexed = {row["id"]: row for row in records}
    require(len(indexed) == len(records), "Duplicate observation ID")
    shapes = {}
    for row in records:
        domain = domains[row["source_frame"]]
        shape = (
            LineString(row["native_path"]) if "native_path" in row else box(*row["native_bounds"])
        )
        require(
            not shape.is_empty and shape.is_valid and domain.covers(shape),
            "Observation outside declared source scope",
        )
        shapes[row["id"]] = shape
    objects = {o["id"]: o for layer in baseline["objects_by_layer"].values() for o in layer}
    for row in metals:
        require(row["authority"] == "AI_SOURCE_OBSERVATION", "Metal observation is not human truth")
        old = row["mapped_model_id"]
        if old:
            require(
                old in objects and objects[old]["layer"].lower() == row["source_frame"],
                "Wrong layer/model mapping",
            )
        require(len(row["endpoints"]) == 2, "Missing endpoints")
        for endpoint, xy in zip(
            row["endpoints"], (row["native_path"][0], row["native_path"][-1]), strict=True
        ):
            require(endpoint["native_xy"] == xy, "Endpoint differs from source path")
            boundary = domains[row["source_frame"]].boundary.covers(Point(xy))
            require(
                (endpoint["state"] == "exits_scope") == boundary,
                "Boundary exit omitted or fabricated",
            )
    approved = {c["id"]: c for c in baseline["reviewed_local_connections"]}
    require(set(approved) == {c["id"] for c in interfaces}, "Inherited interface omitted or added")
    for row in interfaces:
        prior = approved[row["id"]]
        require(
            all(
                row[key] == prior[key]
                for key in (
                    "layer",
                    "source_frame",
                    "native_bounds",
                    "lower_metal_id",
                    "upper_metal_id",
                    "human_review",
                    "connection_confirmed",
                    "physical_cut_count",
                )
            ),
            "Inherited interface identity or approval changed",
        )
    for row in unknowns:
        require(
            row["physical_conductor_count"] is None and row.get("connection_confirmed") is not True,
            "Unknown observation cannot manufacture counts or connection approval",
        )

    surveys = inventory["interface_surveys"]
    m2_ids = {m["id"] for m in metals if m["source_frame"] == "m2"}
    require(
        {s["metal_observation_id"] for s in surveys} == m2_ids and len(surveys) == len(m2_ids),
        "M2 interface survey omitted or duplicated",
    )
    for survey in surveys:
        metal = indexed[survey["metal_observation_id"]]
        require(
            survey["source_frame"] == metal["source_frame"]
            and domains[survey["source_frame"]].covers(box(*survey["native_bounds"]))
            and box(*survey["native_bounds"]).covers(shapes[metal["id"]]),
            "Survey omits metal extent",
        )
        require(
            survey["new_resolved_via_groups"] == []
            and survey["connection_for_unresolved_sites"] is None,
            "Survey cannot manufacture new interfaces or negative connections",
        )
        known = {c["id"] for c in interfaces if c["lower_metal_id"] == metal["mapped_model_id"]}
        require(set(survey["inherited_interface_ids"]) == known, "Survey loses inherited interface")

    tiles = inventory["scan_tiles"]
    require(len({t["id"] for t in tiles}) == len(tiles), "Duplicate scan tile")
    seen = set()
    for frame, domain in domains.items():
        windows = [box(*t["native_bounds"]) for t in tiles if t["source_frame"] == frame]
        require(
            windows and unary_union(windows).equals(domain), "Scan tiles leave a gap or overshoot"
        )
    for tile in tiles:
        require(
            tile["source_frame"] in domains
            and tile["actor"] == "AI"
            and tile["status"] == "SOURCE_INSPECTED",
            "Uninspected/invalid scan tile",
        )
        window = box(*tile["native_bounds"])
        for key in tile["recorded_observation_ids"]:
            require(
                key in indexed
                and indexed[key]["source_frame"] == tile["source_frame"]
                and shapes[key].intersects(window),
                "Tile references wrong-frame/outside record",
            )
            seen.add(key)
    require(seen == set(indexed), "Visible observation omitted from scan ledger")
    counts = Counter(row["source_frame"] for row in metals)
    mapped = Counter(row["source_frame"] for row in metals if row["mapped_model_id"])
    return dict(
        status="LEDGER_CHECKS_PASS_GEOMETRY_COVERAGE_INCOMPLETE",
        scoped_frames=list(domains),
        metal_fragment_observations=dict(counts),
        existing_model_correspondences=dict(mapped),
        unmodeled_fragment_observations=len(metals) - sum(mapped.values()),
        inherited_interfaces=len(interfaces),
        interface_surveys=len(surveys),
        unresolved_observations=len(unknowns),
        boundary_exits=sum(e["state"] == "exits_scope" for m in metals for e in m["endpoints"]),
        scan_tiles_cover_declared_windows=True,
        all_listed_records_accounted=True,
        physical_inventory_exhaustiveness="AI_SCANNED_NOT_INDEPENDENTLY_VERIFIED",
        actual_photo_coverage_fraction=None,
        five_layer_coverage="NOT_EVALUATED",
        source_to_design_registration=False,
        new_connections_confirmed=0,
        baseline_full_model_exact=True,
        complete_network=False,
    ), inputs.files


def run(root, inventory_path, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    require(
        output.is_relative_to(root) and not output.exists(), "Output must be new inside project"
    )
    path = Path(inventory_path).resolve()
    require(path.is_relative_to(root), "Inventory outside project")
    inventory = json.loads(path.read_text())
    report, files = audit(root, inventory)
    files[str(path.relative_to(root))] = digest(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".conductive-inventory-", dir=output.parent) as tmp:
        stage = Path(tmp) / "package"
        stage.mkdir()
        for name, value in [("inventory", inventory), ("report", report)]:
            (stage / (name + ".json")).write_text(
                json.dumps(value, ensure_ascii=False, indent=2) + "\n"
            )
        sources = {
            f: os.path.relpath(root / s["raw_review_asset"]["path"], output)
            for f, s in inventory["scope"]["frames"].items()
        }
        payload = json.dumps(
            dict(inventory=inventory, report=report, sources=sources), ensure_ascii=False
        )
        page = Template(Path(__file__).with_suffix(".html").read_text()).substitute(
            payload=payload.replace("<", r"\u003c")
        )
        (stage / "index.html").write_text(page)
        manifest = dict(
            inputs=files,
            code_sha256=digest(__file__),
            template_sha256=digest(Path(__file__).with_suffix(".html")),
            artifacts={p.name: digest(p) for p in stage.iterdir()},
        )
        (stage / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        stage.rename(output)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = run(Path.cwd(), args.inventory, args.output)
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(2, f"Inventory rejected: {error}\n")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
