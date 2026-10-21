"""Read-only AA/POLY/CT integration audit and small quality-gate counterexamples.

Run from the repo: PYTHONPATH=. .venv/bin/python <this file> --output NEW_DIRECTORY
Requires the project environment plus SciPy (installed with segmentation-eval).
Writes only the new audit output directory, never edits models or source photographs.
This is an audit recipe, not a production extraction workflow or an Agent evaluator.
"""

import argparse
import copy
import hashlib
import json
import subprocess
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.spatial import cKDTree
from shapely.geometry import Polygon, box

from silicon_eye.aa_completion import validate as audit_aa
from silicon_eye.ct_joint_reconstruction import audit_contacts
from silicon_eye.poly_closeout import audit as audit_poly


def load(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def main(output):
    if output.exists():
        raise ValueError("Use a new audit directory")
    output.mkdir(parents=True)
    latest = Path("benchmarks/ct-work-layer-final-v5")
    material = load(latest / "material-model-v1.json")
    contacts = load(latest / "model-v1.json")["objects"]
    aa = {a["id"]: a for a in material["AA_objects"]}
    poly = {p["id"]: p for p in material["objects"]}
    protected_inputs = [
        latest / "model-v1.json",
        latest / "material-model-v1.json",
        latest / "freeze-manifest-v1.json",
    ]
    hashes = {str(p): sha(p) for p in protected_inputs}
    budget = load(latest / "spec-v1.json")["budget"]
    evidence = dict(
        audited_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        scope=(
            "workflow, interfaces, data consistency and quality gates; "
            "no re-extraction or new physical adjudication"
        ),
        baseline_inputs=hashes,
        counts=dict(AA=len(aa), POLY=len(poly), CT=len(contacts)),
        skill_inventory=sorted(str(p) for p in Path("skills").glob("*/SKILL.md")),
        current_geometry=dict(
            AA_overlap_conflicts=audit_aa(list(aa.values())),
            CT=audit_contacts(contacts, material, budget),
        ),
    )
    evidence["retired_references"] = dict(
        guard_AA_ids_missing=sorted(set(material["guard_AA_ids"]) - aa.keys()),
        active_POLY_AA_targets_missing=[
            p["id"] for p in poly.values() if p.get("AA_target") and p["AA_target"] not in aa
        ],
        current_aliases=material["local_material_revision"]["alias_map"],
    )
    try:
        evidence["original_POLY_audit"] = audit_poly(material)
    except (KeyError, ValueError) as error:
        evidence["original_POLY_audit"] = dict(error_type=type(error).__name__, error=str(error))
    # A diagnostic copy only: original data remains unchanged. This tests whether an
    # alias-only adaptation suffices; it is not an adopted repair or a release verdict.
    diagnostic = copy.deepcopy(material)
    aliases = material["local_material_revision"]["alias_map"]
    diagnostic["guard_AA_ids"] = sorted({aliases.get(k, k) for k in material["guard_AA_ids"]})
    evidence["alias_adapted_copy_POLY_audit"] = audit_poly(diagnostic)
    g = poly["G26-P01"]
    target = next(a for a in material["AA_objects"] if a["id"] == g["AA_target"])
    from silicon_eye.geometry_reconstruction import object_polygon

    p = Polygon(g["layout_outline"])
    target_shape = object_polygon(target)
    section = target_shape.intersection(box(p.bounds[0], 0, p.bounds[2], material["canvas_wh"][1]))
    evidence["G26_local_section_diagnostic"] = dict(
        POLY_bounds=list(p.bounds),
        target_AA_bounds=list(target_shape.bounds),
        local_AA_section_bounds=list(section.bounds),
        relation_cross_section=g.get("relation_cross_section"),
        upper_extension_px=section.bounds[1] - p.bounds[1],
        lower_extension_px=p.bounds[3] - section.bounds[3],
        required_relative_px=material["relative_budget"]["gate_extension_px"],
        interpretation=(
            "full-target bbox fails but local section satisfies endcap budget; "
            "validator scope mismatch, not new physical adjudication"
        ),
    )
    evidence["layer_evolution"] = []
    for path in [
        "benchmarks/aa-full-frame-workflow-v1/model-v1.json",
        "benchmarks/poly-closeout-v3/model-v1.json",
    ]:
        old = load(path)
        oldaa = {a["id"]: a for a in old.get("AA_objects", old["objects"])}
        evidence["layer_evolution"].append(
            dict(
                parent=path,
                parent_AA_count=len(oldaa),
                retired_AA_ids=sorted(oldaa.keys() - aa.keys()),
                new_AA_ids=sorted(aa.keys() - oldaa.keys()),
                changed_common_AA_ids=sorted(
                    k for k in oldaa.keys() & aa.keys() if oldaa[k] != aa[k]
                ),
                parent_POLY_count=len(old["objects"]) if "AA_objects" in old else None,
            )
        )
    evidence["AA_schema_compatibility"] = dict(
        AA_tool_reads=(
            "objects as AA plus sources, projection_matrices and object_projection_groups"
        ),
        joint_model_objects_are="POLY; AA is in AA_objects",
        joint_model_missing_AA_tool_fields=sorted(
            {"sources", "projection_matrices", "object_projection_groups", "groups"}
            - material.keys()
        ),
        direct_consume_supported=False,
    )
    groups = defaultdict(list)
    for i, j in sorted(
        cKDTree([o["source_evidence"]["native_center"] for o in contacts]).query_pairs(3)
    ):
        x, y = contacts[i], contacts[j]
        a, b = x.get("AA_target", x.get("POLY_target")), y.get("AA_target", y.get("POLY_target"))
        if a == b or x.get("source_frame") != y.get("source_frame"):
            continue
        groups[tuple(sorted([a, b]))].append(
            dict(
                contact_ids=[x["id"], y["id"]],
                targets=[a, b],
                source_centers=[
                    x["source_evidence"]["native_center"],
                    y["source_evidence"]["native_center"],
                ],
                distance_px=float(
                    np.linalg.norm(
                        np.array(x["source_evidence"]["native_center"])
                        - y["source_evidence"]["native_center"]
                    )
                ),
                canonical_centers=[x["layout_center"], y["layout_center"]],
            )
        )
    collisions = []
    photo = Image.open("data/test_chip/tile_full/poly.jpg").convert("RGB")
    for index, (targets, pairs) in enumerate(groups.items(), 1):
        points = np.array([p for pair in pairs for p in pair["source_centers"]])
        left, top = np.maximum(0, np.floor(points.min(axis=0) - [180, 160])).astype(int)
        right, bottom = np.minimum(photo.size, np.ceil(points.max(axis=0) + [180, 160])).astype(int)
        raw = photo.crop((left, top, right, bottom))
        raw.save(output / f"source-hotspot-{index}-raw.png")
        im = raw.resize((raw.width * 2, raw.height * 2))
        draw = ImageDraw.Draw(im)
        for ix, pair in enumerate(pairs, 1):
            for mark, (x, y) in enumerate(pair["source_centers"]):
                x, y = (x - left) * 2, (y - top) * 2
                rad = 10 if mark == 0 else 5
                color = "#ed8eff" if mark == 0 else "#65baff"
                draw.ellipse((x - rad, y - rad, x + rad, y + rad), outline=color, width=2)
            draw.text((x + 12, y - 3), str(ix), fill="#eeeeee")
        im.save(output / f"source-hotspot-{index}-marked.png")
        collisions.append(
            dict(
                id=f"SOURCE-{index}",
                targets=targets,
                pairs=pairs,
                count=len(pairs),
                native_bbox=[int(left), int(top), int(right), int(bottom)],
            )
        )
    evidence["global_source_nearby_assignments"] = dict(
        radius_px=3,
        total_pairs=sum(len(v) for v in groups.values()),
        hotspots=collisions,
        interpretation=(
            "source consistency candidates, not 16 missing holes or automatic authority "
            "to rewrite human decisions"
        ),
    )

    # Valid before/after fixtures show that a CT gate is not a joint-layer gate.
    g = dict(
        id="G",
        kind="MOS_gate_body",
        group_id="fixture",
        AA_target="A",
        layout_outline=[[40, -10], [50, -10], [50, 110], [40, 110]],
    )
    m = dict(
        objects=[g],
        AA_objects=[dict(id="A", outer_xyxy=[0, 0, 100, 100])],
        guard_AA_ids=[],
        relative_budget=dict(gate_extension_px=8),
        supersession_ledger=[],
        review_issues=[],
        canvas_wh=[150, 150],
    )
    cs = [
        dict(
            id="CG",
            family="G",
            column=0,
            row=0,
            landing_material="POLY",
            POLY_target="G",
            layout_outline=[[42.5, -7.5], [47.5, -7.5], [47.5, -2.5], [42.5, -2.5]],
            source_evidence=dict(native_center=[45, 5], supported=True),
        ),
        dict(
            id="CA",
            family="A",
            column=0,
            row=0,
            landing_material="AA",
            AA_target="A",
            layout_outline=[[17.5, 17.5], [22.5, 17.5], [22.5, 22.5], [17.5, 22.5]],
            source_evidence=dict(native_center=[20, 20], supported=True),
        ),
    ]
    bad = copy.deepcopy(m)
    bad["objects"][0]["layout_outline"] = [[40, -10], [50, -10], [50, 60], [40, 60]]
    examples = dict(
        truncated_gate=dict(
            before_CT=audit_contacts(cs, m, budget)["status"],
            before_POLY=audit_poly(m)["geometry_status"],
            after_CT=audit_contacts(cs, bad, budget)["status"],
            after_POLY=audit_poly(bad)["geometry_status"],
            rejected_by_POLY=audit_poly(bad)["errors"],
        )
    )
    a = dict(
        objects=[],
        AA_objects=[
            dict(id="A", outer_xyxy=[0, 0, 40, 40]),
            dict(id="B", outer_xyxy=[50, 0, 90, 40]),
        ],
    )
    ac = [dict(cs[1], layout_outline=[[10, 10], [15, 10], [15, 15], [10, 15]])]
    bad_a = copy.deepcopy(a)
    bad_a["AA_objects"][0]["outer_xyxy"] = [0, 0, 60, 40]
    examples["merged_neighbour_AA"] = dict(
        before_CT=audit_contacts(ac, a, budget)["status"],
        before_AA_conflicts=audit_aa(a["AA_objects"]),
        after_CT=audit_contacts(ac, bad_a, budget)["status"],
        after_AA_conflicts=audit_aa(bad_a["AA_objects"]),
    )
    evidence["synthetic_joint_gate_counterexamples"] = examples
    evidence["historical_replays"] = {}
    for layer in ["aa", "poly", "ct"]:
        p = Path(f"runs/workflow-audit-6e5bb17-{layer}-replay")
        r = load(p / "report.json")
        mm = load(p / ("material-model.json" if layer == "ct" else "model.json"))
        summary = dict(output_path=str(p), report=r)
        if layer == "ct":
            rr = load(p / "model.json")
            summary.update(
                CT_objects_exact=rr["objects"] == contacts,
                AA_exact=mm["AA_objects"] == material["AA_objects"],
                POLY_exact=mm["objects"] == material["objects"],
                raw_model_stage_status=rr.get("stage_status"),
                raw_model_limitations_ref=rr.get("source_limitations_ref"),
                unknown_scopes_retained=len(load(p / "unknown-sites.json")["unknown_scopes"]),
            )
        evidence["historical_replays"][layer] = summary
    evidence["agent_evaluation"] = dict(
        AA_known_case_acceptance=load("benchmarks/aa-skill-three-task-v1/acceptance-v1.json")[
            "tasks"
        ],
        AA_independent_agent_evaluation=load(
            "benchmarks/aa-full-frame-workflow-v1/skill-release-v1.json"
        )["independent_agent_evaluation"],
        seed_groups=load("benchmarks/agent-eval/index.json")["groups"],
        POLY_count_failure_preserved=load("benchmarks/poly-closeout-v3/agent-evaluation-v1.json"),
    )
    evidence["inputs_unchanged"] = {str(p): sha(p) == hashes[str(p)] for p in protected_inputs}
    assert all(evidence["inputs_unchanged"].values())
    assert evidence["historical_replays"]["ct"]["CT_objects_exact"]
    save(output / "evidence.json", evidence)
    print(
        json.dumps(
            dict(
                CT_status=evidence["current_geometry"]["CT"]["status"],
                AA_conflicts=len(evidence["current_geometry"]["AA_overlap_conflicts"]),
                POLY_validator=evidence["original_POLY_audit"],
                source_pairs=sum(len(v) for v in groups.values()),
                source_hotspots=len(groups),
                inputs_unchanged=True,
            ),
            ensure_ascii=False,
        )[:1600]
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    main(parser.parse_args().output)
