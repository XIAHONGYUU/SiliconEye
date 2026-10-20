"""Consolidate evidence-linked POLY revisions; audit a single full-frame candidate.

Run: python -m silicon_eye.poly_closeout --root . --spec SPEC --output NEW_DIR
Requires the project environment. No segmentation, material completion or net inference.
"""

from __future__ import annotations

import argparse
import copy
import html
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import LineString, Polygon, box
from shapely.strtree import STRtree

from .aa_completion import source_polygon
from .geometry_reconstruction import digest, object_polygon, orthogonal_fit, project
from .poly_full_frame import save
from .scene_geometry import load_locked


def rectified(points):
    edges = np.roll(points, -1, axis=0) - points
    axes = ["H" if abs(x) > abs(y) else "V" for x, y in edges]
    return orthogonal_fit(points, axes).tolist()


def consolidate(parent, inventory, aa, small, lower, review, settings, wide_match, scope_review):
    """Replace entire declared scopes, retaining IDs and explicit approval boundaries."""
    old = {o["id"]: o for o in parent["objects"]}
    observations = {o["id"]: o for o in inventory["objects"]}
    if len(old) != len(parent["objects"]) or len(observations) != len(inventory["objects"]):
        raise ValueError("Duplicate input IDs")
    replacement_groups = {g for row in settings["replace_scope_groups"].values() for g in row}
    replaced = [o for o in parent["objects"] if o.get("group_id") in replacement_groups]
    if any(k in old and old[k] not in replaced for k in observations):
        raise ValueError("Source ID collides with an object outside the replaced scope")
    small_by_id = {o["source_poly_id"]: o for o in small["joint_candidate"]["objects"]}
    lower_by_id = {o["source_poly_id"]: o for o in lower["derived_objects"]}
    wide_id = review["observation_id"]
    accepted_scopes = {
        d["scope"]
        for d in scope_review["decisions"]
        if d.get("status", "").startswith("human_approved_displayed")
    }
    if review["effective_state"]["device_class"] != "resistor":
        raise ValueError("Explicit resistor adjudication required")
    if set(observations) != set(small_by_id) | {wide_id}:
        raise ValueError("Incomplete small-source accounting")
    source_scope = {key: row["id"] for row in inventory["rows"] for key in row["object_ids"]}
    matrix = np.linalg.inv(np.asarray(aa["projection_matrices"]["global"]["poly"]))
    aa_objects = {o["id"]: o for o in aa["objects"]}
    if not settings.get("guard_AA_ids") or not set(settings["guard_AA_ids"]) <= set(aa_objects):
        raise ValueError("Require explicit, existing per-object guard roles")
    result = []
    for source in [o for o in parent["objects"] if o not in replaced] + inventory["objects"]:
        key = source["id"]
        obj = dict(
            id=key,
            material="POLY",
            native_outline=copy.deepcopy(source["native_outline"]),
            source_record=copy.deepcopy(source),
            source_scope=source_scope.get(key),
            group_id=source.get("group_id", source_scope.get(key, "LOCAL")),
            kind=source.get("kind", "POLY_body_fragment"),
            acceptance={
                "material": source.get("approval", source.get("status", "candidate")),
                "joint_geometry": "candidate",
                "electrical": "unknown",
            },
            AA_target=None,
            terminal_status="not_individually_verified",
            geometry_method="legacy_global_projection_then_orthogonal_fit_provisional",
        )
        if key in old:
            obj["legacy_record"] = copy.deepcopy(old[key])
        if key in small_by_id:
            entry = small_by_id[key]
            if entry["joint_layout_outline"] is None:
                raise ValueError("Cannot silently omit a blocked source")
            obj.update(
                layout_outline=copy.deepcopy(entry["joint_layout_outline"]),
                AA_target=entry["AA_object_id"],
                geometry_method="explicit_small_AA_relation",
                relation_record=copy.deepcopy(entry),
            )
            obj["acceptance"]["joint_geometry"] = (
                "human_accepted_displayed_relationship_not_exact_dimensions"
                if entry["scope"] in accepted_scopes
                else "AI_candidate"
            )
        elif key in lower_by_id:
            entry = lower_by_id[key]
            obj.update(
                group_id=entry["group_id"],
                layout_outline=copy.deepcopy(entry["joint_layout_outline"]),
                AA_target=entry.get("target_AA_id", entry.get("aa_object_id")),
                geometry_method="preserved_accepted_lower_joint_relationship",
                relation_record=copy.deepcopy(entry),
            )
            obj["acceptance"]["joint_geometry"] = "human_accepted_displayed_relationship"
        elif key == wide_id:
            left, top, right, bottom = wide_match["projected_POLY_bbox_AA_native"]
            center = np.array([[(left + right) / 2, (top + bottom) / 2]])
            # Recorded local source correspondence; no fictitious active assignment.
            local_aa = np.linalg.inv(np.asarray(aa["projection_matrices"]["global"]["aa"]))
            outline = project(
                np.array([[left, top], [right, top], [right, bottom], [left, bottom]]), local_aa
            )
            frame = settings["wide_layout_frame"]
            upper_obj, lower_obj = (aa_objects[frame[k]] for k in ("upper_AA_id", "lower_AA_id"))
            x = float(center[0, 0])
            line = LineString([(x, 0), (x, aa["canvas_wh"][1])])
            source_top = source_polygon(upper_obj, aa).intersection(line).bounds[3]
            source_bottom = source_polygon(lower_obj, aa).intersection(line).bounds[1]
            xl, _, xr, _ = Polygon(rectified(outline)).bounds
            slab = box(xl, 0, xr, aa["canvas_wh"][1])
            layout_top = object_polygon(upper_obj).intersection(slab).bounds[3]
            layout_bottom = object_polygon(lower_obj).intersection(slab).bounds[1]
            fractions = (np.array([top, bottom]) - source_top) / (source_bottom - source_top)
            if not np.all((fractions > 0) & (fractions < 1)):
                raise ValueError("Observed resistor does not lie inside declared source frame")
            y1, y2 = layout_top + fractions * (layout_bottom - layout_top)
            outline = [[xl, y1], [xr, y1], [xr, y2], [xl, y2]]
            obj.update(
                layout_outline=outline,
                kind="resistor_POLY_body",
                geometry_method="human_resistor_local_photo_match_to_AA_working_candidate",
                semantic_review=copy.deepcopy(review),
                projected_AA_center=center.tolist(),
                relative_frame=dict(
                    frame,
                    source_gap=[source_top, source_bottom],
                    layout_gap=[layout_top, layout_bottom],
                    observed_y_fractions=fractions.tolist(),
                ),
            )
            obj["acceptance"]["material"] = "human_confirmed_POLY_resistor"
        else:
            obj["layout_outline"] = rectified(project(np.asarray(source["native_outline"]), matrix))
        if obj["AA_target"] is not None and obj["AA_target"] not in aa_objects:
            raise ValueError("Missing explicit AA target")
        result.append(obj)
    # Align only provisional repeated families. Already reviewed relative geometry stays exact.
    for gid in {o["group_id"] for o in result}:
        members = [
            o
            for o in result
            if o["group_id"] == gid and o["geometry_method"].startswith("legacy_global")
        ]
        if (
            gid == "LOCAL"
            or len(members) < 2
            or any(len(o["layout_outline"]) != 4 for o in members)
        ):
            continue
        polygons = [Polygon(o["layout_outline"]) for o in members]
        top = float(np.median([p.bounds[1] for p in polygons]))
        bottom = float(np.median([p.bounds[3] for p in polygons]))
        width = float(np.median([p.bounds[2] - p.bounds[0] for p in polygons]))
        centers = np.linspace(polygons[0].centroid.x, polygons[-1].centroid.x, len(members))
        for obj, center_x in zip(members, centers, strict=True):
            obj["layout_outline"] = [
                [center_x - width / 2, top],
                [center_x + width / 2, top],
                [center_x + width / 2, bottom],
                [center_x - width / 2, bottom],
            ]
            obj["geometry_method"] += "_shared_row_parameters"
    for family in settings["cross_row_sets"]:
        reference = [o for o in result if o["group_id"] == family["reference"]]
        for gid in family["groups"]:
            members = [o for o in result if o["group_id"] == gid]
            if not members or not all(
                o["geometry_method"].startswith("legacy_global") for o in members
            ):
                continue
            if len(members) != len(reference):
                raise ValueError("Matched family count changed")
            for obj, ref in zip(members, reference, strict=True):
                p, q = np.array(obj["layout_outline"]), np.array(ref["layout_outline"])
                if p.shape != q.shape:
                    raise ValueError("Incompatible matched family outlines")
                p[:, 0] = q[:, 0]
                obj["layout_outline"] = p.tolist()
    by_id = {o["id"]: o for o in result}
    assigned_new = set()
    for relation in settings.get("new_joint_relations", []):
        target = object_polygon(aa_objects[relation["AA_id"]])
        if not target.equals(box(*target.bounds)):
            raise ValueError("Nonrectangular AA requires local cross-sections, not bbox fitting")
        left, top, right, bottom = target.bounds
        width, margin, extension = (relation[k] for k in ("width_px", "margin_px", "extension_px"))
        ids = relation["object_ids"]
        if not ids or width <= 0 or extension <= 0 or margin < 0:
            raise ValueError("Invalid explicit new relation")
        lower_x, upper_x = left + margin + width / 2, right - margin - width / 2
        if upper_x < lower_x or (len(ids) > 1 and (upper_x - lower_x) / (len(ids) - 1) <= width):
            raise ValueError("Cannot shrink a gate to force an infeasible AA relation")
        centers = np.linspace(lower_x, upper_x, len(ids)) if len(ids) > 1 else [(left + right) / 2]
        for key, cx in zip(ids, centers, strict=True):
            obj = by_id[key]
            if (
                key in assigned_new
                or obj["AA_target"]
                or not obj["geometry_method"].startswith("legacy_global")
            ):
                raise ValueError("New relation would replace an existing reviewed relationship")
            assigned_new.add(key)
            obj.update(
                AA_target=relation["AA_id"],
                relation_record=copy.deepcopy(relation),
                layout_outline=[
                    [cx - width / 2, top - extension],
                    [cx + width / 2, top - extension],
                    [cx + width / 2, bottom + extension],
                    [cx - width / 2, bottom + extension],
                ],
                geometry_method="explicit_new_AA_relation_AI_candidate",
            )
    for family in settings["cross_row_sets"]:
        reference = [o for o in result if o["group_id"] == family["reference"]]
        for gid in family["groups"]:
            members = [o for o in result if o["group_id"] == gid]
            if not members or not all(
                o["geometry_method"] == "explicit_new_AA_relation_AI_candidate" for o in members
            ):
                continue
            if len(members) != len(reference):
                raise ValueError("Explicit matched row count mismatch")
            for obj, ref in zip(members, reference, strict=True):
                p = np.asarray(obj["layout_outline"])
                p[:, 0] = np.asarray(ref["layout_outline"])[:, 0]
                obj["layout_outline"] = p.tolist()
                obj["matched_row_constraint"] = family["id"]
    if len({o["id"] for o in result}) != len(result):
        raise ValueError("Consolidation produced duplicate IDs")
    ledger = [
        dict(
            id=o["id"],
            previous_record=copy.deepcopy(o),
            action="same_ID_revised" if o["id"] in observations else "retired_scope_template",
            replacement_scope=next(
                scope
                for scope, groups in settings["replace_scope_groups"].items()
                if o.get("group_id") in groups
            ),
        )
        for o in replaced
    ]
    return dict(
        schema_version=1,
        coordinate_space="AA_working_layout_relative_pixels",
        canvas_wh=aa["canvas_wh"],
        objects=result,
        AA_objects=copy.deepcopy(aa["objects"]),
        supersession_ledger=ledger,
        parent_ref=settings["inputs"]["parent"],
        source_inventory_ref=settings["inputs"]["inventory"],
        source_scope_rows=copy.deepcopy(inventory["rows"]),
        original_unknown_regions=copy.deepcopy(parent["unresolved"]),
        unobserved_slots=small["joint_candidate"]["unobserved_slots"],
        final_status="candidate_not_fullframe_human_approved",
        counts_are_material_objects_not_devices=True,
        legacy_geometries_and_source_extents_preserved=True,
        guard_AA_ids=copy.deepcopy(settings.get("guard_AA_ids", [])),
        relative_budget=copy.deepcopy(settings["relative_budget"]),
        review_issues=copy.deepcopy(settings.get("review_issues", [])),
        known_exceptions=copy.deepcopy(settings.get("known_exceptions", [])),
        cross_row_sets=copy.deepcopy(settings["cross_row_sets"]),
        effective_human_reviews=dict(
            scoped_correspondence=copy.deepcopy(scope_review),
            wide_resistor=copy.deepcopy(review),
            fullframe_display_review_ref=settings["inputs"]["full_review"],
            scope_review_ref=settings["inputs"]["U05_review"],
            rule="Later resistor adjudication overrides previous disputed-wide status only; "
            "no blanket geometry approval transferred",
        ),
    )


def audit(model):
    objects = model["objects"]
    polygons = [Polygon(o["layout_outline"]) for o in objects]
    aa = {o["id"]: object_polygon(o) for o in model["AA_objects"]}
    guards = {k: aa[k] for k in model["guard_AA_ids"]}
    errors, warnings = [], []
    tree = STRtree(polygons)
    pairs = []
    for i, (obj, p) in enumerate(zip(objects, polygons, strict=True)):
        points = np.array(obj["layout_outline"])
        edges = np.roll(points, -1, axis=0) - points
        if (
            not p.is_valid
            or p.area <= 0
            or not np.all((abs(edges[:, 0]) < 1e-7) | (abs(edges[:, 1]) < 1e-7))
        ):
            errors.append(dict(id=obj["id"], reason="invalid_or_nonorthogonal"))
        for j in tree.query(p):
            if j > i and p.intersection(polygons[j]).area > 1e-6:
                pairs.append([obj["id"], objects[j]["id"]])
        if obj["AA_target"]:
            target = aa[obj["AA_target"]]
            if obj.get("relation_cross_section"):
                local = target.intersection(box(p.bounds[0], 0, p.bounds[2], model["canvas_wh"][1]))
                target = local
            if p.intersection(target).area <= 1e-6:
                errors.append(dict(id=obj["id"], reason="explicit_target_AA_missed"))
            extension = model["relative_budget"]["gate_extension_px"] - 1e-6
            if (
                target.bounds[1] - p.bounds[1] < extension
                or p.bounds[3] - target.bounds[3] < extension
            ):
                errors.append(dict(id=obj["id"], reason="explicit_target_extension_missing"))
            others = [
                k
                for k, other in aa.items()
                if k != obj["AA_target"] and k not in guards and p.intersection(other).area > 1e-6
            ]
            if others:
                errors.append(dict(id=obj["id"], reason="non_target_AA_overlap", AA_ids=others))
        elif "resistor" not in obj["kind"]:
            warnings.append(
                dict(
                    id=obj["id"],
                    group=obj["group_id"],
                    reason="AA_relation_not_explicitly_verified",
                )
            )
        hits = [k for k, g in guards.items() if p.intersection(g).area > 1e-6]
        if hits:
            warnings.append(
                dict(
                    id=obj["id"],
                    group=obj["group_id"],
                    reason="AA_guard_overlap_review_coordinates_and_material",
                    AA_ids=hits,
                )
            )
    return dict(
        objects=len(objects),
        superseded_records=len(model["supersession_ledger"]),
        retired_IDs=sum(
            x["action"] == "retired_scope_template" for x in model["supersession_ledger"]
        ),
        resistor_bodies=sum("resistor" in o["kind"] for o in objects),
        explicit_AA_targets=sum(o["AA_target"] is not None for o in objects),
        errors=errors,
        positive_area_overlap_pairs=pairs,
        warnings=warnings,
        geometry_status="PASS" if not errors and not pairs else "FAIL",
        polygon_geometry_status="FAIL"
        if pairs or any(e["reason"] == "invalid_or_nonorthogonal" for e in errors)
        else "PASS",
        release_status=(
            "READY_FOR_CT_working_baseline"
            if not errors and not pairs and not model["review_issues"]
            else "BLOCKED_until_new_issues_reviewed"
        ),
        fullframe_material_truth=False,
        CT_or_net_assignment=False,
        not_foundry_DRC=True,
        human_review_issues=copy.deepcopy(model["review_issues"]),
    )


def revise_feedback(parent, aa, settings, feedback, root):
    """Retire rejected scope candidates, preserving immutable parent records and source truth."""
    model = copy.deepcopy(parent)
    revision = settings["revision"]
    objects = model["objects"]
    old_ids = {o["id"] for o in objects}
    groups = {g for values in revision["replace_groups"].values() for g in values}
    retiring = [o for o in objects if o["group_id"] in groups]
    if any(
        o["id"] in settings["protected_source_ids"]
        or o["acceptance"]["joint_geometry"].startswith("human_accepted")
        for o in retiring
    ):
        raise ValueError("Feedback patch would retire an unrelated approved object")
    if set(revision["retire_AA_ids"]) != {feedback["decisions"]["Q4"]["AA_false_positive_id"]}:
        raise ValueError("AA retirement exceeds explicit human false-positive decision")
    model["objects"] = [o for o in objects if o["group_id"] not in groups]
    for obj in retiring:
        model["supersession_ledger"].append(
            dict(
                id=obj["id"],
                previous_record=obj,
                action="retired_scope_template",
                reason="new human feedback rejects count/geometry",
                feedback=settings["inputs"]["revision_feedback"],
            )
        )
    model["AA_retirements"] = []
    for key in revision["retire_AA_ids"]:
        obj = next(o for o in model["AA_objects"] if o["id"] == key)
        model["AA_retirements"].append(
            dict(
                id=key,
                previous_record=copy.deepcopy(obj),
                reason="human_confirmed_false_AA_extraction",
                feedback=feedback["decisions"]["Q4"],
            )
        )
    model["AA_objects"] = [
        o for o in model["AA_objects"] if o["id"] not in revision["retire_AA_ids"]
    ]
    active = {o["id"]: object_polygon(o) for o in model["AA_objects"]}
    locator = np.asarray(aa["projection_matrices"]["global"]["poly"])
    for patch in revision["patches"]:
        target = active[patch["AA_id"]]
        left, top, right, bottom = target.bounds
        count, width = patch["count"], patch["width_px"]
        margin, extension = patch["margin_px"], patch["extension_px"]
        centers = patch.get("centers_layout_x") or (
            np.linspace(left + margin + width / 2, right - margin - width / 2, count).tolist()
            if count > 1
            else [(left + right) / 2]
        )
        if len(centers) != count or width <= 0 or extension < 8:
            raise ValueError("Invalid feedback patch budget or count")
        for index, cx in enumerate(centers):
            slab = target.intersection(
                box(cx - width / 2, 0, cx + width / 2, model["canvas_wh"][1])
            )
            if slab.is_empty or slab.geom_type != "Polygon":
                raise ValueError("Ambiguous local AA cross-section; do not use its bbox")
            if not slab.equals(box(*slab.bounds)):
                raise ValueError("Gate slab crosses an AA step; reconsider slot positions")
            _, local_top, _, local_bottom = slab.bounds
            outline = [
                [cx - width / 2, local_top - extension],
                [cx + width / 2, local_top - extension],
                [cx + width / 2, local_bottom + extension],
                [cx - width / 2, local_bottom + extension],
            ]
            if patch.get("native_outlines"):
                native = patch["native_outlines"][index]
            elif patch.get("native_outline"):
                if count != 1:
                    raise ValueError("A single body observation cannot seed several new objects")
                native = patch["native_outline"]
            else:
                native = project(np.asarray(outline), locator).tolist()
            key = f"CL2-{patch['scope']}-{patch['tag']}-{index + 1:02}"
            if key in old_ids:
                raise ValueError("New count hypotheses must not silently reuse prior IDs")
            obj = dict(
                id=key,
                material="POLY",
                kind="MOS_gate_body_candidate",
                group_id=patch["scope"],
                source_scope=patch["scope"],
                native_outline=native,
                layout_outline=outline,
                source_record=dict(
                    evidence_AA_id=patch["AA_id"],
                    geometry_status=patch["source_geometry_status"],
                    feedback_ref=settings["inputs"]["revision_feedback"],
                ),
                acceptance=dict(
                    material="human_scope_feedback_plus_AI_geometry",
                    joint_geometry="AI_revised_candidate_not_exact_human_boundary",
                    electrical="unknown",
                ),
                AA_target=patch["AA_id"],
                relation_cross_section=True,
                relation_record=copy.deepcopy(patch),
                geometry_method="local_AA_cross_section",
                terminal_status="material_endcap_candidate_not_CT_assignment",
            )
            if patch["tag"] == "WIDE":
                obj["kind"] = "human_confirmed_wide_POLY_MOS_body"
                obj["acceptance"]["material"] = "human_confirmed_wide_POLY_MOS"
            if patch["tag"] == "RIGHT":
                obj["count_status"] = "AI_count_5; human only estimated greater_than_4"
            model["objects"].append(obj)
    model["parent_closeout_ref"] = settings["inputs"]["revision_parent"]
    model["human_feedback"] = copy.deepcopy(feedback)
    model["alternatives_adopted"] = True
    model["review_issues"] = copy.deepcopy(revision["pending_issues"])
    model["review_panels"] = copy.deepcopy(revision["review_panels"])
    model["profile_evidence"] = []
    for check in revision["profile_checks"]:
        image = np.asarray(
            Image.open(root / settings["inputs"][check["source"] + "_photo"]["path"]).convert("L"),
            dtype=np.float32,
        )
        left, top, right, bottom = check["roi"]
        mean = image[top:bottom, left:right].mean(axis=0)
        results = []
        for sigma in check["sigmas"]:
            smooth = cv2.GaussianBlur(mean.reshape(1, -1), (0, 0), sigma).ravel()
            sign = -1 if check["mode"] == "minima" else 1
            values = sign * smooth
            peaks = [
                i + left
                for i in range(1, len(values) - 1)
                if values[i] > values[i - 1] and values[i] >= values[i + 1]
            ]
            results.append(dict(sigma=sigma, positions_x=peaks, count=len(peaks)))
        model["profile_evidence"].append(
            dict(
                check,
                results=results,
                all_counts_match=all(r["count"] == check["expected_count"] for r in results),
                interpretation="count support only; not contact ownership or general detector",
            )
        )
    if len({o["id"] for o in model["objects"]}) != len(model["objects"]):
        raise ValueError("Duplicate IDs after revision")
    return model


def apply_count_approval(parent, aa, settings, approval):
    """Apply a human count correction without rewriting the failed algorithm evidence."""
    model = copy.deepcopy(parent)
    patch = settings["final_count_revision"]
    if patch["count"] != approval["right_MOS_count"]:
        raise ValueError("Count correction must match explicit human decision")
    by_id = {o["id"]: o for o in model["objects"]}
    old = [by_id[key] for key in patch["old_ids"]]
    if any(o["AA_target"] != patch["AA_id"] or o["group_id"] != "Q3" for o in old):
        raise ValueError("Count correction would replace an unrelated object")
    model["objects"] = [o for o in model["objects"] if o["id"] not in patch["old_ids"]]
    for obj in old:
        model["supersession_ledger"].append(
            dict(
                id=obj["id"],
                previous_record=obj,
                action="retired_scope_template",
                reason="human_corrected_AI_count_5_to_6",
                feedback=settings["inputs"]["count_approval"],
            )
        )
    target = next(object_polygon(o) for o in model["AA_objects"] if o["id"] == patch["AA_id"])
    left, top, right, bottom = target.bounds
    width, margin, extension = (patch[k] for k in ("width_px", "margin_px", "extension_px"))
    centers = np.linspace(left + margin + width / 2, right - margin - width / 2, patch["count"])
    if len(centers) > 1 and np.min(np.diff(centers)) <= width:
        raise ValueError("Human count cannot fit declared width and gap")
    for i, cx in enumerate(centers, 1):
        outline = [
            [cx - width / 2, top - extension],
            [cx + width / 2, top - extension],
            [cx + width / 2, bottom + extension],
            [cx - width / 2, bottom + extension],
        ]
        obj = copy.deepcopy(old[0])
        obj.update(
            id=f"{patch['id_prefix']}-{i:02}",
            layout_outline=outline,
            native_outline=project(
                np.asarray(outline), np.asarray(aa["projection_matrices"]["global"]["poly"])
            ).tolist(),
            count_status="human_confirmed_six_MOS; precise_new_boundaries_unknown",
            geometry_method="human_count_six_AA_relative_equal_pitch_candidate",
            relation_record=copy.deepcopy(patch),
            source_record=dict(
                geometry_status="derived_native_locator_not_exact_boundary",
                feedback_ref=settings["inputs"]["count_approval"],
            ),
            acceptance=dict(
                material="human_confirmed_MOS_count",
                joint_geometry="count_corrected_geometry_not_exact_boundary_approved",
                electrical="unknown",
            ),
        )
        model["objects"].append(obj)
    for obj in model["objects"]:
        if obj["group_id"] in patch["approved_scope_groups"]:
            obj["acceptance"]["joint_geometry"] = "human_accepted_displayed_relationship"
    model["count_approval"] = copy.deepcopy(approval)
    model["parent_closeout_ref"] = settings["inputs"]["revision_parent"]
    model["review_issues"] = []
    model["final_status"] = "POLY_v1_working_baseline; known_boundaries_and_photo_edges_unknown"
    model["algorithm_evaluation"] = copy.deepcopy(approval["evaluation_failure"])
    model["review_panels"][2]["finding"] = (
        "宽MOS及左侧四MOS保持；右侧按用户明确裁决由5改为6条。原五谷/六亮列记录保留为算法漏判。"
    )
    model["review_panels"][2]["question"] = (
        "六MOS数量已确认，不重复询问数量；新增几何按AA相对位置生成，精确边界与CT/连接待后续证据修订。"
    )
    return model


def svg(model, bounds):
    left, top, right, bottom = bounds
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{left} {top} '
        f'{right - left} {bottom - top}"><rect x="{left}" y="{top}" '
        f'width="{right - left}" height="{bottom - top}" fill="#111c28"/>'
    ]
    parts.append('<g data-layer="AA">')
    for o in model["AA_objects"]:
        p = object_polygon(o)
        path = " ".join(
            "M" + " L".join(f"{x},{y}" for x, y in ring.coords) + " Z"
            for ring in [p.exterior, *p.interiors]
        )
        parts.append(
            f'<path d="{path}" fill="#315548" stroke="#86b5a5" '
            f'stroke-width="1" fill-rule="evenodd"><title>{html.escape(o["id"])}</title></path>'
        )
    parts.append('</g><g data-layer="POLY">')
    for o in model["objects"]:
        color = (
            "#d89afa"
            if "resistor" in o["kind"]
            else ("#78c9ff" if "human_accepted" in o["acceptance"]["joint_geometry"] else "#f7bc5c")
        )
        points = " ".join(f"{x},{y}" for x, y in o["layout_outline"])
        parts.append(
            f'<polygon points="{points}" fill="{color}" fill-opacity=".48" '
            f'stroke="{color}" stroke-width="1.5"><title>{html.escape(o["id"])}</title>'
            "</polygon>"
        )
    return "".join(parts) + "</g></svg>"


def review_page(root, model, report, settings, output):
    """One entry for the unified model, twelve navigation tiles and new issues only."""
    width, height = model["canvas_wh"]
    columns, rows = settings["review_grid"]
    navigation = f'<button data-box="0 0 {width} {height}">全幅</button>'
    for row in range(rows):
        for col in range(columns):
            value = (
                f"{col * width / columns} {row * height / rows} {width / columns} {height / rows}"
            )
            navigation += f'<button data-box="{value}">F{row * columns + col + 1:02}</button>'
    cards = []
    issues = copy.deepcopy(model.get("review_panels", model["review_issues"]))
    aa_by_id = {o["id"]: o for o in model["AA_objects"]}
    source_aa = load_locked(root, settings["inputs"]["AA"])
    source_aa_by_id = {o["id"]: o for o in source_aa["objects"]}
    for issue in issues:
        ident = issue["id"]
        group_ids = set(issue["groups"])
        members = [o for o in model["objects"] if o["group_id"] in group_ids]
        for name in ("poly", "aa"):
            photo = Image.open(root / settings["inputs"][name + "_photo"]["path"]).convert("RGB")
            bounds = issue[name + "_bbox"]
            photo.crop(bounds).save(output / f"{ident}-{name}-raw.png")
            marked = photo.crop(bounds)
            draw = ImageDraw.Draw(marked)
            if name == "poly":
                for i, obj in enumerate(members, 1):
                    points = [(x - bounds[0], y - bounds[1]) for x, y in obj["native_outline"]]
                    draw.line(points + [points[0]], fill="#f7bc5c", width=2)
                    draw.text(points[0], str(i), fill="#ffdf78")
                if "unknown_poly_native_bbox" in issue:
                    left, top, right, bottom = issue["unknown_poly_native_bbox"]
                    draw.rectangle(
                        (left - bounds[0], top - bounds[1], right - bounds[0], bottom - bounds[1]),
                        outline="#d89afa",
                        width=3,
                    )
                    draw.text(
                        (left - bounds[0], top - bounds[1] - 14),
                        "UNKNOWN - not filled",
                        fill="#d89afa",
                    )
            elif issue.get("highlight_AA_ids"):
                for key in issue["highlight_AA_ids"]:
                    p = source_polygon(source_aa_by_id[key], source_aa)
                    points = [(x - bounds[0], y - bounds[1]) for x, y in p.exterior.coords]
                    draw.line(points, fill="#77d6ff", width=3)
                    draw.text(points[0], key, fill="#77d6ff")
            marked.save(output / f"{ident}-{name}-marked.png")
        issue["current_material_objects"] = len(members)
        (output / f"{ident}-layout.svg").write_text(svg(model, issue["work_bbox"]))
        if model.get("alternatives_adopted"):
            previous = load_locked(root, settings["inputs"]["revision_parent"])
            (output / f"{ident}-before.svg").write_text(svg(previous, issue["work_bbox"]))
        proposal = None
        if ident == "Q1" and not model.get("alternatives_adopted"):
            pairs = zip(issue["alternative_AA_ids"], issue["alternative_counts"], strict=True)
            proposal = [(k, n, issue["alternative_width_px"]) for k, n in pairs]
        elif ident == "Q2" and not model.get("alternatives_adopted"):
            proposal = [
                (f"AA2-MIDDLE-MOS-{key}-0", n, 30)
                for key, n in [("B1", 4), ("B2", 4), ("C0", 5), ("C1", 2), ("C2", 2), ("C3", 5)]
            ]
        if proposal:
            alt = copy.deepcopy(model)
            alt["objects"] = [o for o in alt["objects"] if o["group_id"] not in group_ids]
            if ident == "Q2":
                alt["objects"].extend(o for o in members if o["group_id"] in {"G29", "G30"})
            for key, count, gate_width in proposal:
                left, top, right, bottom = object_polygon(aa_by_id[key]).bounds
                centers = np.linspace(left + 8 + gate_width / 2, right - 8 - gate_width / 2, count)
                for index, cx in enumerate(centers):
                    alt["objects"].append(
                        dict(
                            id=f"ALT-{ident}-{key}-{index}",
                            kind="count_hypothesis_not_adopted",
                            acceptance={"joint_geometry": "candidate"},
                            layout_outline=[
                                [cx - gate_width / 2, top - 8],
                                [cx + gate_width / 2, top - 8],
                                [cx + gate_width / 2, bottom + 8],
                                [cx - gate_width / 2, bottom + 8],
                            ],
                        )
                    )
            (output / f"{ident}-alternative.svg").write_text(svg(alt, issue["work_bbox"]))
        image_options = '<option value="layout">当前统一候选</option>'
        if model.get("alternatives_adopted"):
            image_options += '<option value="before">修订前同位置</option>'
        if proposal:
            image_options += '<option value="alternative">数量替代假设（未采用）</option>'
        image_options += (
            '<option value="poly-marked">POLY原图与旧候选编号</option>'
            '<option value="poly-raw">POLY原图</option>'
            '<option value="aa-marked">AA原图与标记（独立原生坐标）</option>'
            '<option value="aa-raw">AA原图</option>'
        )
        default_view = (
            "aa-marked" if ident == "Q4" else "poly-marked" if ident == "Q3" else "layout"
        )
        if model.get("alternatives_adopted"):
            default_view = "layout"
        image_options = image_options.replace(
            f'value="{default_view}"', f'value="{default_view}" selected', 1
        )
        suffix = ".svg" if default_view == "layout" else ".png"
        cards.append(
            f'<section id="{ident}"><h2>{ident}：{html.escape(issue["title"])}</h2>'
            f'<p>{html.escape(issue["finding"])}</p><p class="question">'
            f"{html.escape(issue['question'])}</p>"
            f'<select class="issue-select" data-issue="{ident}">{image_options}</select>'
            f'<div class="scroll"><img id="image-{ident}" '
            f'src="{ident}-{default_view}{suffix}"></div>'
            "<p>原图模式各用原生坐标；没有把未经验证的跨层投影叠在照片上。"
            "替代数量图仅核对数量和分组，宽度及端部不代表新批准，不生成或退休有效对象。</p></section>"
        )
    save(output / "issues.json", model["review_issues"])
    save(output / "review-panels.json", issues)
    full = svg(model, [0, 0, width, height]).replace("<svg ", '<svg id="layout" ', 1)
    template = (Path(__file__).with_name("poly_closeout_review.html")).read_text()
    replacements = {
        "{{NAV}}": navigation,
        "{{SVG}}": full,
        "{{ISSUES}}": "".join(cards),
        "{{COUNT}}": str(report["objects"]),
        "{{TARGETS}}": str(report["explicit_AA_targets"]),
        "{{RETIRED}}": str(report["retired_IDs"]),
        "{{REVIEW_NOTICE}}": (
            "Q1、Q2、Q4已批准；Q3右侧已按用户确认改为6条。POLY v1可作为后续CT的工作基线，"
            "原图精确边界、工艺尺寸、CT与连接仍保留未知。"
            if model.get("count_approval")
            else (
                "Q1/Q2已按反馈修订，Q3左侧与宽MOS已补，Q4误提AA已退休。"
                "重点核对新图，尤其Q3右侧5条窄栅候选；尚未全幅定稿。"
                if model.get("alternatives_adopted")
                else "当前仍有下方Q1–Q4需要裁决，尚未全幅定稿。"
            )
        ),
        "{{AA_NOTE}}": (
            "原非目标AA冲突已依据用户的误提裁决解除，未通过缩栅隐藏。"
            if model.get("alternatives_adopted")
            else "其中1条仍与另一块AA冲突，见Q4。"
        ),
    }
    for key, value in replacements.items():
        template = template.replace(key, value)
    (output / "index.html").write_text(template)


def run(root, spec_path, output):
    if output.exists():
        raise ValueError("Use a new output directory")
    root = root.resolve()
    settings = json.loads(spec_path.read_text())
    inputs = settings["inputs"]
    data = {k: load_locked(root, ref) for k, ref in inputs.items() if not k.endswith("photo")}
    for name in ("aa_photo", "poly_photo"):
        if digest(root / inputs[name]["path"]) != inputs[name]["sha256"]:
            raise ValueError("Changed source photograph")
    if "final_count_revision" in settings:
        model = apply_count_approval(
            data["revision_parent"], data["AA"], settings, data["count_approval"]
        )
    elif "revision_parent" in data:
        model = revise_feedback(
            data["revision_parent"], data["AA"], settings, data["revision_feedback"], root
        )
    else:
        model = consolidate(
            data["parent"],
            data["inventory"],
            data["AA"],
            data["small_joint"],
            data["lower_joint"],
            data["wide_review"],
            settings,
            data["wide_match"],
            data["U05_review"],
        )
    report = audit(model)
    output.mkdir(parents=True)
    save(output / "model.json", model)
    save(output / "report.json", report)
    save(output / "spec.json", settings)
    width, height = model["canvas_wh"]
    (output / "full.svg").write_text(svg(model, [0, 0, width, height]))
    preview = Image.new("RGB", (1465, 1147), "#111c28")
    draw = ImageDraw.Draw(preview)
    for obj in model["AA_objects"]:
        p = object_polygon(obj)
        draw.polygon([(x / 4, y / 4) for x, y in p.exterior.coords], fill="#315548")
        for h in p.interiors:
            draw.polygon([(x / 4, y / 4) for x, y in h.coords], fill="#111c28")
    for obj in model["objects"]:
        color = "#d89afa" if "resistor" in obj["kind"] else "#f7bc5c"
        draw.polygon([(x / 4, y / 4) for x, y in obj["layout_outline"]], outline=color)
    preview.save(output / "overview.png")
    source_preview = Image.open(root / inputs["poly_photo"]["path"]).convert("RGB")
    source_draw = ImageDraw.Draw(source_preview)
    for obj in model["objects"]:
        points = [tuple(p) for p in obj["native_outline"]]
        source_draw.line(points + [points[0]], fill="#32cdff", width=2)
    source_preview.resize((1428, 1071)).save(output / "source-overview.png")
    review_page(root, model, report, settings, output)
    return model, report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    _, report = run(args.root, args.spec, args.output)
    print(json.dumps({k: v for k, v in report.items() if k != "warnings"}, ensure_ascii=False))
