"""Load one locked AA/POLY/CT snapshot and enforce joint continuation checks.

Run: python -m silicon_eye.joint_layers --snapshot configs/joint-work-layer-v1.json
      --output NEW_DIRECTORY
Requires the project environment. Checks do not infer material or electrical truth.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import numpy as np
from shapely.geometry import Point
from shapely.strtree import STRtree

from .geometry_reconstruction import digest
from .scene_geometry import load_locked


def material_aliases(model):
    """Resolve retained identity chains, rejecting ambiguity, cycles and resurrection."""
    active = [o["id"] for key in ("AA_objects", "objects") for o in model[key]]
    if len(set(active)) != len(active):
        raise ValueError("Duplicate active material ID")
    aliases = {}
    declarations = list(model.get("POLY_material_aliases", {}).items())
    declarations += list(model.get("local_material_revision", {}).get("alias_map", {}).items())
    declarations += [
        (alias, obj["id"])
        for key in ("AA_objects", "objects")
        for obj in model[key]
        for alias in obj.get("material_aliases", [])
    ]
    for alias, target in declarations:
        if alias in active or (alias in aliases and aliases[alias] != target):
            raise ValueError("Ambiguous or resurrected material alias: " + alias)
        aliases[alias] = target
    for alias in aliases:
        target, seen = aliases[alias], {alias}
        while target in aliases:
            if target in seen:
                raise ValueError("Cyclic material alias: " + alias)
            seen.add(target)
            target = aliases[target]
        if target not in active:
            raise ValueError("Dangling material alias: " + alias)
        aliases[alias] = target
    return aliases


def resolved_material(model):
    """Return a relationship view; never rewrite historical records or geometry."""
    result = copy.deepcopy(model)
    aliases = material_aliases(model)
    aa = {o["id"] for o in model["AA_objects"]}
    poly = {o["id"] for o in model["objects"]}

    def resolve(key, allowed):
        target = aliases.get(key, key)
        if target not in allowed:
            raise ValueError("Missing or wrong-layer material reference: " + key)
        return target

    result["guard_AA_ids"] = sorted({resolve(k, aa) for k in model.get("guard_AA_ids", [])})
    for obj in result["objects"]:
        if obj.get("AA_target"):
            obj["AA_target"] = resolve(obj["AA_target"], aa)
        if "member_POLY_ids" in obj:
            obj["member_POLY_ids"] = [resolve(k, poly) for k in obj["member_POLY_ids"]]
    return result


def resolved_contacts(contacts, model):
    aliases = material_aliases(model)
    by_layer = {
        "AA_target": {o["id"] for o in model["AA_objects"]},
        "POLY_target": {o["id"] for o in model["objects"]},
    }
    result = copy.deepcopy(contacts)
    for obj in result:
        field = "POLY_target" if obj.get("landing_material", "AA") == "POLY" else "AA_target"
        target = aliases.get(obj[field], obj[field])
        if target not in by_layer[field]:
            raise ValueError("Missing or wrong-layer CT target: " + obj["id"])
        obj[field] = target
    return result


def source_conflicts(contacts, radius=3):
    """Find same-frame cross-target source reuse; native pixels are not design pixels."""
    contacts = sorted(contacts, key=lambda o: o["id"])
    points = []
    for obj in contacts:
        xy = np.asarray(obj["source_evidence"]["native_center"], dtype=float)
        if xy.shape != (2,) or not np.isfinite(xy).all():
            raise ValueError("Invalid CT source coordinate: " + obj["id"])
        points.append(Point(xy))
    tree, pairs = STRtree(points), []
    for i, point in enumerate(points):
        for j in tree.query(point.buffer(radius).envelope):
            if j <= i or point.distance(points[j]) > radius:
                continue
            a, b = contacts[i], contacts[j]
            target_a = a.get("AA_target") or a.get("POLY_target")
            target_b = b.get("AA_target") or b.get("POLY_target")
            if a.get("source_frame") == b.get("source_frame") and target_a != target_b:
                pairs.append(
                    dict(
                        ids=sorted([a["id"], b["id"]]),
                        targets=[target_a, target_b],
                        source_frame=a.get("source_frame"),
                        native_centers=[
                            a["source_evidence"]["native_center"],
                            b["source_evidence"]["native_center"],
                        ],
                        distance_px=point.distance(points[j]),
                    )
                )
    return sorted(pairs, key=lambda p: p["ids"])


def reviewed_contact_errors(contacts, material):
    """Enforce scoped adjudications separately from geometric plausibility."""
    by_id = {o["id"]: o for o in contacts}
    poly = {o["id"]: o for o in material["objects"]}
    aliases = material_aliases(material)
    errors = []
    for rule in material.get("reviewed_contact_constraints", []):
        key = rule["contact_id"]
        obj = by_id.get(key)
        if obj is None:
            errors.append(dict(id=key, reason="reviewed_contact_missing"))
        else:
            landing = rule["landing_material"]
            field = "POLY_target" if landing == "POLY" else "AA_target"
            expected = aliases.get(rule[field], rule[field])
            if obj.get("landing_material", "AA") != landing or obj.get(field) != expected:
                errors.append(dict(id=key, reason="reviewed_contact_identity_changed"))
            if "shared_POLY_member_ids" in rule:
                members = poly.get(expected, {}).get("member_POLY_ids", [])
                if set(members) != set(rule["shared_POLY_member_ids"]):
                    errors.append(dict(id=key, reason="reviewed_shared_POLY_members_changed"))
        for retired in rule.get("forbidden_active_contact_ids", []):
            if retired in by_id:
                errors.append(dict(id=retired, reason="rejected_contact_identity_resurrected"))
    return errors


def audit_joint(contacts, material, budget, parent_contacts=None):
    """Hard geometry/reference checks plus a separate, non-laundered source gate."""
    from .aa_completion import validate
    from .ct_joint_reconstruction import audit_contacts
    from .poly_closeout import audit

    try:
        view = resolved_material(material)
        cuts = resolved_contacts(contacts, view)
        aa_conflicts = validate(view["AA_objects"])
        poly = audit(view)
        ct = audit_contacts(cuts, view, budget)
        identity_errors = reviewed_contact_errors(cuts, view)
        conflicts = source_conflicts(cuts)
        previous = (
            source_conflicts(resolved_contacts(parent_contacts, view))
            if parent_contacts is not None
            else []
        )
    except (KeyError, ValueError) as error:
        return dict(
            status="FAIL",
            geometry_status="FAIL",
            reference_errors=[str(error)],
            automatic_network_export_allowed=False,
        )
    old = {tuple(p["ids"]): p for p in previous}
    # A changed coordinate/target is not grandfathered merely because the IDs are old.
    inherited, new = [], []
    for pair in conflicts:
        (inherited if old.get(tuple(pair["ids"])) == pair else new).append(pair)
    geometry_ok = not aa_conflicts and poly["geometry_status"] == ct["status"] == "PASS"
    return dict(
        status="FAIL"
        if not geometry_ok or new or identity_errors
        else ("REVIEW_REQUIRED" if conflicts else "PASS"),
        geometry_status="PASS" if geometry_ok else "FAIL",
        reference_errors=[],
        reviewed_identity_status="FAIL" if identity_errors else "PASS",
        reviewed_contact_constraint_errors=identity_errors,
        AA_overlap_conflicts=aa_conflicts,
        POLY=poly,
        CT=ct,
        source_gate=dict(
            status="FAIL" if new else ("REVIEW_REQUIRED" if conflicts else "PASS"),
            radius_native_px=3,
            inherited_unresolved=inherited,
            new_conflicts=new,
        ),
        automatic_network_export_allowed=False,
        physical_PDK_DRC=False,
    )


def require_joint(contacts, material, budget, parent_contacts):
    report = audit_joint(contacts, material, budget, parent_contacts)
    if report["status"] == "FAIL":
        raise ValueError("Joint layer continuation blocked: " + json.dumps(report))
    return report


def load_snapshot(root, manifest):
    """Load all layer, approval, unknown and coordinate context from locked refs."""
    root = Path(root).resolve()
    spec = json.loads(Path(manifest).read_text())
    values = {k: load_locked(root, ref) for k, ref in spec["inputs"].items()}
    material, contacts = values["materials"], values["contacts"]["objects"]
    reject_retired_ids(spec, material)
    resolved_material(material)
    resolved_contacts(contacts, material)
    if material["canvas_wh"] != spec["canvas_wh"]:
        raise ValueError("Snapshot coordinate mismatch")
    if values["parent_spec"]["budget"] != spec["budget"]:
        raise ValueError("Snapshot budget differs from locked parent")
    for ref in spec.get("source_photos", {}).values():
        if digest(root / ref["path"]) != ref["sha256"]:
            raise ValueError("Snapshot source photo changed")
    snapshot = dict(manifest=spec, values=values, materials=material, contacts=contacts)
    if spec.get("conductive_layers"):
        from .conductive_layers import load_registry

        snapshot["conductors"] = load_registry(root, spec["conductive_layers"], spec)
    return snapshot


def write_snapshot(root, snapshot, output):
    """Write a reloadable candidate manifest, keeping inherited approval scope explicit."""
    root, output = Path(root).resolve(), Path(output).resolve()
    if not output.is_relative_to(root):
        raise ValueError("Snapshot output must remain inside the project")
    if any(
        (output / name).exists()
        for name in ("joint-materials.json", "joint-contacts.json", "joint-snapshot.json")
    ):
        raise ValueError("Snapshot output already exists")
    reject_retired_ids(snapshot["manifest"], snapshot["materials"])
    if snapshot["manifest"].get("conductive_layers"):
        from .conductive_layers import load_registry

        if snapshot.get("conductors") != load_registry(
            root, snapshot["manifest"]["conductive_layers"], snapshot["manifest"]
        ):
            raise ValueError("Conductive layer records changed outside a scoped transaction")
    require_joint(
        snapshot["contacts"],
        snapshot["materials"],
        snapshot["manifest"]["budget"],
        snapshot["values"]["contacts"]["objects"],
    )
    output.mkdir(parents=True, exist_ok=True)
    manifest = copy.deepcopy(snapshot["manifest"])
    parent_id = manifest["id"]
    manifest.update(
        id=parent_id + ":candidate",
        parent_snapshot_id=parent_id,
        adoption_status="candidate_not_new_human_approval",
    )
    for key, name, value in [
        ("materials", "joint-materials.json", snapshot["materials"]),
        (
            "contacts",
            "joint-contacts.json",
            {
                **copy.deepcopy(snapshot["values"]["contacts"]),
                "objects": snapshot["contacts"],
            },
        ),
    ]:
        path = output / name
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
        manifest["inputs"][key] = dict(path=str(path.relative_to(root)), sha256=digest(path))
    manifest["inherited_stage_is_not_candidate_approval"] = True
    path = output / "joint-snapshot.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return path


def reject_retired_ids(manifest, material):
    active = {o["id"] for key in ("objects", "AA_objects") for o in material[key]}
    if active & set(manifest.get("retired_material_ids", [])):
        raise ValueError("Retired material ID resurrected")


def aa_view(snapshot):
    """Adapt latest AA records with historical locator metadata, never old geometry."""
    context = copy.deepcopy(snapshot["values"]["AA_context"])
    historic = {o["id"]: o for o in context["objects"]}
    context["objects"] = copy.deepcopy(snapshot["materials"]["AA_objects"])
    context["joint_snapshot_id"] = snapshot["manifest"]["id"]
    # Multi-observation/merged sources cannot be represented by one old homography.
    context["source_footprint_policy"] = "observations_not_exact_joint_photo_projection"
    from .aa_completion import source_polygon

    footprints = {}
    for obj in context["objects"]:
        records = obj.get("merged_source_records", [])
        if not records and obj.get("source_native_geometry") == "unchanged_in_parent_records":
            records = [historic[k] for k in obj.get("material_aliases", []) if k in historic]
            if len(records) != len(obj.get("material_aliases", [])):
                raise ValueError("Missing merged AA source observation: " + obj["id"])
        if records:
            footprints[obj["id"]] = [
                dict(
                    outer_xy=list(source_polygon(o, context).exterior.coords),
                    holes_xy=[list(h.coords) for h in source_polygon(o, context).interiors],
                )
                for o in records
            ]
    context["source_footprints"] = footprints
    return context


def replace_layer(snapshot, layer, records, authorized_ids):
    """Return a bounded new joint snapshot; companion layers and limits remain exact."""
    if layer not in {"AA", "POLY", "CT"}:
        raise ValueError("Unknown layer")
    result = copy.deepcopy(snapshot)
    old = (
        snapshot["contacts"]
        if layer == "CT"
        else snapshot["materials"]["AA_objects" if layer == "AA" else "objects"]
    )
    before, after = {o["id"]: o for o in old}, {o["id"]: o for o in records}
    if len(after) != len(records):
        raise ValueError("Duplicate revision ID")
    changed = {k for k in before.keys() | after.keys() if before.get(k) != after.get(k)}
    if changed - set(authorized_ids):
        raise ValueError("Layer revision changed objects outside scope")
    if layer == "CT":
        result["contacts"] = copy.deepcopy(records)
    else:
        result["materials"]["AA_objects" if layer == "AA" else "objects"] = copy.deepcopy(records)
    reject_retired_ids(snapshot["manifest"], result["materials"])
    result["joint_report"] = require_joint(
        result["contacts"],
        result["materials"],
        snapshot["manifest"]["budget"],
        snapshot["contacts"],
    )
    return result


def run(root, manifest, output):
    output = Path(output)
    if output.exists():
        raise ValueError("Output must be new")
    snapshot = load_snapshot(root, manifest)
    report = audit_joint(
        snapshot["contacts"],
        snapshot["materials"],
        snapshot["manifest"]["budget"],
        snapshot["contacts"],
    )
    output.mkdir(parents=True)
    context = dict(
        snapshot_id=snapshot["manifest"]["id"],
        inputs=snapshot["manifest"]["inputs"],
        source_photos=snapshot["manifest"]["source_photos"],
        canvas_wh=snapshot["manifest"]["canvas_wh"],
        source_wh=snapshot["manifest"]["source_wh"],
        budget=snapshot["manifest"]["budget"],
        stage=snapshot["values"]["stage"],
        restrictions=snapshot["values"]["use_contract"],
        unknown=snapshot["values"]["unknown"],
        source_reinspection=snapshot["values"]["source_reinspection"],
        report=report,
    )
    if "conductors" in snapshot:
        from .conductive_layers import audit_summary

        report["conductive_layers"] = audit_summary(snapshot["conductors"])
        context["conductive_layers"] = snapshot["manifest"]["conductive_layers"]
    (output / "joint-report.json").write_text(
        json.dumps(context, ensure_ascii=False, indent=2) + "\n"
    )
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = run(args.root, args.snapshot, args.output)
    print(json.dumps(dict(status=result["status"], geometry_status=result["geometry_status"])))
    if result["status"] == "FAIL":
        raise SystemExit(1)
