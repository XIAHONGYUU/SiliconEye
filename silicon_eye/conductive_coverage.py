"""Reconcile a frozen source ledger with current reviewed conductor geometry.

Run: python -m silicon_eye.conductive_coverage --request FILE --output NEW_DIR
Requires existing project dependencies. This audits declared records, not pixels,
physical absence, complete networks, or new source identities.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

from shapely.geometry import box

from .conductive_inventory import audit as inventory_audit
from .conductive_inventory import require
from .conductive_workflow import prepare
from .geometry_reconstruction import digest
from .metal_reconstruction import feature_polygon
from .metal_via_pilot import group_via_budget, interface_audit, regular_group_cuts
from .review_package import Inputs


def reconcile(root, request):
    root, inputs = Path(root).resolve(), Inputs(root)
    require(
        request.get("kind") == "conductive_coverage_reconciliation"
        and request.get("schema_version") == 1,
        "Unsupported coverage request",
    )
    inventory = inputs.document(request["inventory"])
    require(
        set(inventory["scope"]["frames"]) == {"m2", "m3"},
        "Only the M2/V2/M3 continuous scope is qualified",
    )
    historical, files = inventory_audit(root, inventory)
    inputs.files.update(files)
    model, _, sample, snapshot, files = prepare(root, inputs.document(request["workflow_request"]))
    inputs.files.update(files)
    require(model == inputs.document(request["work_model"]), "Current model replay differs")
    baseline = inputs.document(request["qualitative_baseline"])
    inputs.human(baseline["human_review"])
    accepted = inputs.document(baseline["geometry_model"])
    previous = {o["id"]: o for layer in accepted["objects_by_layer"].values() for o in layer}
    features = {f["id"]: f for layer in sample["features_by_layer"].values() for f in layer}
    objects = {o["id"]: o for layer in model["objects_by_layer"].values() for o in layer}
    observations = {o["id"]: o for o in inventory["metal_observations"]}
    mapping = sample["inventory_geometry_mapping"]
    require(
        len(mapping) == len(observations)
        and {m["observation_id"] for m in mapping} == set(observations)
        and {m["metal_id"] for m in mapping} == set(features),
        "Mapping is not bijective",
    )
    require(set(features) <= set(baseline["accepted_metal_ids"]), "Missing qualitative baseline")
    for frame, scope in inventory["scope"]["frames"].items():
        require(scope["photo"] == snapshot["source_photos"][frame], "Photo scope changed")
    extent = inputs.document(sample["source_extent_evidence"])
    extents = {row["metal_id"]: row for row in extent["metals"]}
    claims = {c["id"]: c for c in sample["interfaces"]}
    require(
        all(c["layer"] == "V2" and c["layer_pair"] == ["M2", "M3"] for c in claims.values()),
        "Only M2/V2/M3 interfaces are qualified",
    )
    reviewed = {c["id"]: c for c in model["reviewed_local_connections"]}
    require(
        set(claims) == set(reviewed) and not model["pending_interface_ids"],
        "Coverage closeout requires scoped carrier verdicts for every represented interface",
    )
    interfaces, crossing = [], set()
    for key, claim in claims.items():
        approval = reviewed[key]
        scope = inventory["scope"]["frames"][claim["source_frame"]]
        native = box(*claim["native_bounds"])
        domain = box(*scope["native_bounds"])
        require(domain.intersection(native).area > 0, "Interface does not intersect scope")
        contained = domain.covers(native)
        if not contained:
            crossing.add(key)
            evidence = request.get("boundary_interfaces", {}).get(key, {})
            require(
                bool(evidence.get("reason"))
                and evidence.get("human_review") == approval["human_review"],
                "Boundary interface needs its original scoped review and explicit reason",
            )
            inputs.human(evidence["human_review"])
        budget = group_via_budget(claim, sample["via_budget"])
        require(bool(claim.get("cut_array_candidate")), "Proxy is not a complete declared array")
        cuts = regular_group_cuts(claim, budget)
        lower = feature_polygon(features[claim["lower_metal_id"]])
        upper = feature_polygon(features[claim["upper_metal_id"]])
        audit = interface_audit(
            cuts,
            lower,
            upper,
            budget,
            layer_stack=(claim["layer_pair"][0], claim["layer"], claim["layer_pair"][1]),
        )
        envelope = box(*claim["bounds"]).buffer(budget["enclosure_px"], join_style="mitre")
        require(
            audit["status"] == "PASS" and lower.covers(envelope) and upper.covers(envelope),
            "Whole declared group enclosure failed",
        )
        interfaces.append(
            dict(
                id=key,
                layer=claim["layer"],
                source_frame=claim["source_frame"],
                native_bounds=claim["native_bounds"],
                lower_metal_id=claim["lower_metal_id"],
                upper_metal_id=claim["upper_metal_id"],
                human_review=approval["human_review"],
                physical_cut_count=approval["physical_cut_count"],
                design_cut_count=len(cuts),
                scope_relation="CONTAINED" if contained else "STRADDLES_SOURCE_SCOPE",
                entire_source_group_within_scope=contained,
                full_declared_design_enclosure="PASS",
                source_array_geometry="NOT_QUALIFIED",
            )
        )
    require(
        set(request.get("boundary_interfaces", {})) == crossing,
        "Boundary declarations missing or stale",
    )
    metals, endpoints = [], []
    for link in mapping:
        key = link["metal_id"]
        observation, feature = observations[link["observation_id"]], features[key]
        visible = extents.get(key, {}).get("visible_native_path", feature["native_path"])
        require(
            visible == observation["native_path"], "Source extent/anchor correspondence changed"
        )
        require(feature["source_frame"] == observation["source_frame"], "Wrong source layer")
        native_path = feature["native_path"]
        require(native_path == previous[key]["native_path"], "Native baseline anchor changed")
        same = objects[key]["geometry"] == previous[key]["geometry"]
        known = [c["id"] for c in interfaces if key in (c["lower_metal_id"], c["upper_metal_id"])]
        metals.append(
            dict(
                source_observation_id=observation["id"],
                metal_id=key,
                source_frame=feature["source_frame"],
                native_path=visible,
                native_anchor_path=native_path,
                design_path=feature["design_path"],
                working_geometry_status="QUALITATIVE_BASELINE_RETAINED"
                if same
                else "LOCAL_REVISION_CANDIDATE_NOT_HUMAN_GEOMETRY_APPROVED",
                reviewed_interface_ids=known,
                interface_completeness="NOT_PROVEN",
            )
        )
        for i, endpoint in enumerate(observation["endpoints"]):
            endpoints.append(
                dict(
                    metal_id=key,
                    source_observation_id=observation["id"],
                    source_frame=feature["source_frame"],
                    endpoint_index=i,
                    native_xy=endpoint["native_xy"],
                    state=endpoint["state"],
                    design_xy=feature["design_path"][0 if i == 0 else -1],
                    coordinate_relation="DECLARED_ENDPOINT_ROLE_NOT_MEASURED_PROJECTION",
                )
            )
    no_interface = {
        m["metal_id"]
        for m in metals
        if m["source_frame"] == "m2" and not m["reviewed_interface_ids"]
    }
    dispositions = request.get("unresolved_metals", {})
    require(set(dispositions) == no_interface, "Unreviewed M2 needs a source disposition")
    for key, disposition in dispositions.items():
        doc = inputs.document(disposition["evidence"])
        matches = [o for o in doc["observations"] if o["id"] == disposition["observation_id"]]
        require(len(matches) == 1, "Disposition observation missing or duplicated")
        observation = matches[0]
        require(
            disposition.get("physical_absence_confirmed") is False
            and observation.get("actor") == "AI"
            and observation.get("lower_metal_id") == key
            and observation.get("source_photo") == snapshot["source_photos"]["m2"]
            and observation.get("physical_no_via_claim") is False
            and observation.get("V2_present_human_confirmed") is None,
            "AI non-detection cannot become physical absence",
        )
    unknowns = inputs.document(request["unknown_dispositions"])["rows"]
    original = {o["id"]: o for o in inventory["unknown_observations"]}
    require(
        len(unknowns) == len(original) and {u["id"] for u in unknowns} == set(original),
        "Historical unknown disposition omitted or duplicated",
    )
    for unknown in unknowns:
        require(
            unknown["original_native_bounds"] == original[unknown["id"]]["native_bounds"],
            "Unknown source scope changed",
        )
        inputs.document(unknown["basis"])
    exit_count = sum(e["state"] == "exits_scope" for e in endpoints)
    require(exit_count == historical["boundary_exits"], "Source exit count drift")
    coverage = dict(
        status="DECLARED_SCOPE_RECONCILED_PHYSICAL_QUALIFICATION_OPEN",
        date=request["date"],
        source_metal_counts=dict(Counter(m["source_frame"] for m in metals)),
        declared_metal_count=len(metals),
        mapped_metal_count=len(features),
        declaration_mapping_complete=True,
        photo_coverage_fraction=None,
        retained_qualitative_geometries=sum(
            m["working_geometry_status"] == "QUALITATIVE_BASELINE_RETAINED" for m in metals
        ),
        revised_candidate_metal_ids=[
            m["metal_id"]
            for m in metals
            if m["working_geometry_status"] != "QUALITATIVE_BASELINE_RETAINED"
        ],
        source_endpoint_count=len(endpoints),
        scope_exit_endpoints=exit_count,
        physical_network_terminal_count=None,
        reviewed_interfaces=len(interfaces),
        candidate_design_cuts=sum(c["design_cut_count"] for c in interfaces),
        whole_declared_groups_checked=len(interfaces),
        fully_contained_source_interface_windows=len(interfaces) - len(crossing),
        boundary_interface_ids=sorted(crossing),
        human_physical_counts_known=sum(c["physical_cut_count"] is not None for c in interfaces),
        M2_with_reviewed_interface=len({c["lower_metal_id"] for c in interfaces}),
        M2_without_identified_interface=sorted(no_interface),
        M3_with_reviewed_interface=len({c["upper_metal_id"] for c in interfaces}),
        actual_interface_total=None,
        interface_photo_coverage_fraction=None,
        M1_V1_continuous_scope="NOT_EVALUATED",
        source_to_design_transform=None,
        physical_inventory_exhaustiveness="NOT_INDEPENDENTLY_VERIFIED",
        complete_network=False,
        canonical_geometry_adopted=False,
        pending_identity_or_carrier_questions=list(model["pending_interface_ids"]),
    )
    return dict(
        coverage=coverage,
        metals=metals,
        interfaces=interfaces,
        endpoints=endpoints,
        unknowns=unknowns,
        unresolved_metals=dispositions,
    ), inputs.files


def run(root, request_path, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    require(not output.exists() and output.is_relative_to(root), "Output must be new inside root")
    data, files = reconcile(root, json.loads(Path(request_path).read_text()))
    output.mkdir(parents=True)
    for name, value in data.items():
        (output / (name + ".json")).write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n"
        )
        if isinstance(value, list) and value:
            columns = list(dict.fromkeys(k for row in value for k in row))
            with (output / (name + ".csv")).open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
                writer.writeheader()
                writer.writerows(
                    {
                        k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
                        for k, v in row.items()
                    }
                    for row in value
                )
    manifest = dict(inputs=files, artifacts={p.name: digest(p) for p in output.iterdir()})
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(Path.cwd(), args.request, args.output)


if __name__ == "__main__":
    main()
