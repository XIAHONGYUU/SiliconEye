"""Apply source-only decisions with explicit semantics; do not infer transitive approval."""

import copy


def apply(groups, rules, answers):
    """Return candidate groups plus exact approved relations and excluded edge records."""
    groups = copy.deepcopy(groups)
    known = {f for g in groups for f in g["fragments"]}
    relations, edges = [], []
    for rule in rules:
        answer = answers[rule["item_id"]]
        if answer["verdict"] != "accepted":
            continue
        if answer.get("notes", "").strip():
            raise ValueError("Accepted notes require semantic reconciliation")
        ids = rule["fragments"]
        if len(ids) != 2 or len(set(ids)) != 2 or not set(ids) <= known:
            raise ValueError("Unknown or duplicate fragment in review rule")
        if rule["action"] == "same_source_path":
            relations.append(
                dict(
                    fragments=ids,
                    review_item=rule["item_id"],
                    status="human_confirmed_local_source_relation",
                )
            )
            matching = [g for g in groups if set(g["fragments"]) & set(ids)]
            if len(matching) > 1:
                merged = dict(
                    id="REVIEW-" + rule["item_id"],
                    fragments=list(dict.fromkeys(f for g in matching for f in g["fragments"])),
                    physical_identity="unknown",
                    group_human_approved=False,
                )
                groups = [g for g in groups if g not in matching] + [merged]
        elif rule["action"] == "wide_metal_edge":
            edges.extend(
                dict(
                    fragment_id=f,
                    review_item=rule["item_id"],
                    classification="human_confirmed_wide_metal_edge",
                )
                for f in ids
            )
            for g in groups:
                g["fragments"] = [f for f in g["fragments"] if f not in ids]
            groups = [g for g in groups if g["fragments"]]
        else:
            raise ValueError("Unsupported source review action")
    for g in groups:
        g["group_human_approved"] = False
    return dict(
        groups=groups,
        reviewed_relations=relations,
        reviewed_edges=edges,
        electrical_identity="unknown",
        geometry_adopted=False,
    )
