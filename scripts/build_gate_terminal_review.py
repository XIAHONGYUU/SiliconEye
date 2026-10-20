"""Build a photo-only terminal review; never modify material/contact geometry.

Run with project Python: scripts/build_gate_terminal_review.py --spec SPEC --output NEW_DIR.
Requires OpenCV, NumPy, Pillow and the editable project install. The input records are
AI locator hypotheses. Bright peaks and candidate registration are not contact assignments.
"""

import argparse
import html
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

from silicon_eye.geometry_reconstruction import digest
from silicon_eye.guided_materials import ct_support
from silicon_eye.scene_geometry import load_locked


def write(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def localize_bottom_contacts(source, materials, paths, recipe):
    """Locate measured end-row peaks between named, previously matched diffusion columns."""
    gray = cv2.cvtColor(source, cv2.COLOR_BGR2GRAY)
    smooth = cv2.GaussianBlur(gray, (5, 5), 1).astype(float)
    residual = smooth - cv2.GaussianBlur(smooth, (0, 0), 4)
    materials = {o["id"]: o for o in materials["objects"]}
    paths = {r["id"]: r for r in paths["profile_rows"]}
    results = []
    for request in recipe["gates"]:
        gate = materials[request["gate_id"]]
        side = request.get("side", "bottom")
        if side not in {"top", "bottom"}:
            raise ValueError("Terminal side must be top or bottom")
        endpoint_ys = [y for x, y in gate["native_outline"]]
        previous_y = min(endpoint_ys) if side == "top" else max(endpoint_ys)

        def column_x(key, endpoint_y=previous_y):
            points = np.asarray(paths[key]["source_path"])
            return float(np.interp(endpoint_y, points[:, 1], points[:, 0]))

        left, right = column_x(request["left_column"]), column_x(request["right_column"])
        center = (left + right) / 2
        ring_key = request.get("ring_row", request.get("lower_ring"))
        ring = np.asarray(paths[ring_key]["source_path"])
        ring_y = float(np.interp(center, ring[:, 0], ring[:, 1]))
        y1 = int(previous_y - recipe["search_above"])
        y2 = int(previous_y + recipe["search_below"])
        if side == "bottom":
            y2 = int(min(y2, ring_y - recipe["ring_margin"]))
        else:
            y1 = int(max(y1, ring_y + recipe["ring_margin"]))
        x1, x2 = int(left + recipe["column_inset"]), int(right - recipe["column_inset"])
        if x1 >= x2 or y1 >= y2 or min(x1, y1) < 0:
            raise ValueError("Invalid terminal search region")
        yp = smooth[y1:y2, int(center - 9) : int(center + 10)].mean(axis=1).astype("float32")
        y = y1 + int(cv2.GaussianBlur(yp[None, :], (0, 0), 1.3).argmax())
        xp = smooth[y - 2 : y + 3, x1:x2].mean(axis=0).astype("float32")
        xp = cv2.GaussianBlur(xp[None, :], (0, 0), 1)[0]
        maxima = [
            i
            for i in range(2, len(xp) - 2)
            if xp[i] >= recipe["profile_min_gray"]
            and xp[i] > max(xp[i - 2 : i].max(), xp[i + 1 : i + 3].max())
        ]
        chosen = []
        for i in sorted(maxima, key=lambda i: -xp[i]):
            if all(abs(i - j) >= recipe["peak_min_distance"] for j in chosen):
                chosen.append(i)
        observed = []
        for i in sorted(chosen):
            x = x1 + i
            supported = (
                smooth[y, x] >= request.get("min_gray", recipe["min_gray"])
                and residual[y, x] >= recipe["min_residual"]
            )
            observed.append(
                dict(
                    native_center=[x, y],
                    peak_gray=float(smooth[y, x]),
                    local_residual=float(residual[y, x]),
                    profile_gray=float(xp[i]),
                    supported=bool(supported),
                )
            )
        results.append(
            dict(
                request,
                source_roi=[x1, y1, x2, y2],
                source_row_bbox=[x1, y - 6, x2, y + 7],
                prior_derived_endpoint_y=previous_y,
                observations=observed,
                retained_peaks=[o for o in observed if o["supported"]],
                weaker_peaks_not_deleted=[o for o in observed if not o["supported"]],
                interpretation="AI_CT_location_candidates_after_human_bottom_region_confirmation",
            )
        )
    return results


def run(root, spec_path, output):
    root, output = Path(root).resolve(), Path(output)
    if output.exists():
        raise ValueError("Output must be new")
    spec = json.loads(Path(spec_path).read_text())
    refs = spec["inputs"]
    for ref in refs.values():
        if digest(root / ref["path"]) != ref["sha256"]:
            raise ValueError("Input changed: " + ref["path"])
    material = load_locked(root, refs["materials"])
    parent = load_locked(root, refs["contacts"])
    source_spec = load_locked(root, refs["source_paths"])
    source = cv2.imread(str(root / refs["poly_photo"]["path"]))
    m1 = cv2.imread(str(root / refs["m1_photo"]["path"]))
    if source is None or m1 is None:
        raise ValueError("Missing photo")
    output.mkdir(parents=True)
    if spec.get("operation") == "terminal_row_measurement":
        localized = localize_bottom_contacts(
            source, material, source_spec, spec["bottom_localization"]
        )
        for ref in refs.values():
            if digest(root / ref["path"]) != ref["sha256"]:
                raise ValueError("Input changed during terminal measurement")
        report = dict(
            gates=len(localized),
            retained_peaks=sum(len(g["retained_peaks"]) for g in localized),
            weaker_peaks=sum(len(g["weaker_peaks_not_deleted"]) for g in localized),
            parent_CT_count=len(parent["objects"]),
            exported_new_CT=0,
            implementation_sha256=digest(Path(__file__)),
        )
        write(output / "measurements.json", dict(gates=localized))
        write(output / "report.json", report)
        write(output / "spec.json", spec)
        return report
    gates = [o for o in material["objects"] if o.get("group_id") == spec["group_id"]]
    gates.sort(key=lambda o: o["id"])
    inventory, region_reports, cards = [], {}, []
    for key, region in spec["regions"].items():
        x1, y1, x2, y2 = region["poly_bbox"]
        crop = source[y1:y2, x1:x2]
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        smooth = cv2.GaussianBlur(gray, (5, 5), 1).astype(float)
        residual = smooth - cv2.GaussianBlur(smooth, (0, 0), 4)
        maxima = (
            (smooth == cv2.dilate(smooth, np.ones((7, 7))))
            & (smooth >= spec["peak_gray"])
            & (residual >= spec["peak_residual"])
        )
        num, _, _, centers = cv2.connectedComponentsWithStats(maxima.astype("uint8"))
        compact_support = ct_support(crop, profile="legacy")
        peaks = []
        for i in range(1, num):
            px, py = centers[i]
            rx, ry = round(px), round(py)
            peaks.append(
                dict(
                    id=f"{key}-PEAK-{i:04}",
                    native_xy=[px + x1, py + y1],
                    peak_gray=float(smooth[ry, rx]),
                    residual=float(residual[ry, rx]),
                    status="optical_peak_only_not_CT",
                    compact_optical_support=bool(compact_support[ry, rx]),
                )
            )
        marked = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(marked)
        for gate in gates:
            if not gate["id"].startswith(tuple(region["gate_prefixes"])):
                continue
            pts = np.asarray(gate["native_outline"])
            left, top = pts.min(axis=0)
            right, bottom = pts.max(axis=0)
            alias = f"QG{gates.index(gate) + 1:02}"
            boxes = {
                "TOP": [left - 5, top - 16, right + 5, top + 16],
                "BOTTOM": [left - 5, bottom - 16, right + 5, bottom + 16],
                "LEFT": [left - 18, top + 16, left - 5, bottom - 16],
                "RIGHT": [right + 5, top + 16, right + 18, bottom - 16],
            }
            observations = {}
            for mode, box in boxes.items():
                zl, zt, zr, zb = box
                observations[mode] = [
                    p
                    for p in peaks
                    if zl <= p["native_xy"][0] <= zr and zt <= p["native_xy"][1] <= zb
                ]
                if mode in {"TOP", "BOTTOM"}:
                    draw.rectangle((zl - x1, zt - y1, zr - x1, zb - y1), outline="#ffbd55", width=1)
                    draw.text(
                        (zl - x1, max(0, zt - y1 - 10)), alias + " " + mode[0], fill="#ffdd88"
                    )
            draw.line(
                [(float(x - x1), float(y - y1)) for x, y in [*pts, pts[0]]], fill="#c7a4ff", width=1
            )
            inventory.append(
                dict(
                    id=alias,
                    gate_id=gate["id"],
                    region=key,
                    source_locator_status="derived_locator_not_exact_boundary",
                    zones=boxes,
                    observations=observations,
                    CT_assignment="unknown",
                    electrical_connection="unknown",
                )
            )
        # Draw only actually measured end-zone maxima, not holes on a synthetic grid.
        relevant = {
            p["id"]: p
            for g in inventory
            if g["region"] == key
            for mode in ["TOP", "BOTTOM"]
            for p in g["observations"][mode]
        }
        marked.save(output / f"{key}-zones.png")
        for p in relevant.values():
            if not p["compact_optical_support"]:
                continue
            x, y = p["native_xy"]
            x -= x1
            y -= y1
            draw.line((x - 2, y, x + 2, y), fill="#6ce5ff", width=1)
            draw.line((x, y - 2, x, y + 2), fill="#6ce5ff", width=1)
        marked.save(output / f"{key}-marked.png")
        cv2.imwrite(str(output / f"{key}-poly.png"), crop)
        pq = np.asarray(region["poly_quad"], np.float32)
        mq = np.asarray(region["m1_quad"], np.float32)
        matrix = cv2.getPerspectiveTransform(mq, pq)
        offset = np.array([[1, 0, -x1], [0, 1, -y1], [0, 0, 1]], float)
        warped = cv2.warpPerspective(m1, offset @ matrix, (x2 - x1, y2 - y1))
        cv2.imwrite(str(output / f"{key}-m1-candidate.png"), warped)
        cv2.imwrite(
            str(output / f"{key}-blend-candidate.png"), cv2.addWeighted(crop, 0.5, warped, 0.5, 0)
        )
        ml, mt = np.floor(mq.min(axis=0) - 50).astype(int)
        mr, mb = np.ceil(mq.max(axis=0) + 50).astype(int)
        cv2.imwrite(str(output / f"{key}-m1-raw.png"), m1[mt:mb, ml:mr])
        lead_view = Image.fromarray(cv2.cvtColor(m1[mt:mb, ml:mr], cv2.COLOR_BGR2RGB))
        lead_draw = ImageDraw.Draw(lead_view)
        for lead in region.get("m1_lead_rois", []):
            ll, tt, rr, bb = lead["native_bbox"]
            lead_draw.rectangle((ll - ml, tt - mt, rr - ml, bb - mt), outline="#ffbd55", width=2)
            lead_draw.text((ll - ml, tt - mt - 12), lead["id"], fill="#ffdd88")
        lead_view.save(output / f"{key}-m1-leads.png")
        checks = []
        warped_gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
        for row in source_spec["profile_rows"]:
            if "-SD-" not in row["id"] or not row["id"].startswith("Q2-" + key):
                continue
            path = np.asarray(row["source_path"])
            ym = (path[0, 1] + path[-1, 1]) / 2
            xp = float(np.interp(ym, path[:, 1], path[:, 0]))
            yy = round(ym - y1)
            xx = round(xp - x1)
            profile = warped_gray[yy - 45 : yy + 46, xx - 12 : xx + 13].mean(0).astype("float32")
            peak = int(cv2.GaussianBlur(profile[None, :], (0, 0), 1.5).argmax()) - 12
            checks.append(dict(source_column=row["id"], delta_x=peak))
        max_error = max(abs(c["delta_x"]) for c in checks)
        median = float(np.median([abs(c["delta_x"]) for c in checks]))
        precise = max_error <= spec["max_column_error_px"]
        region_reports[key] = dict(
            m1_to_poly=matrix.tolist(),
            poly_quad=region["poly_quad"],
            m1_quad=region["m1_quad"],
            independent_column_checks=checks,
            max_abs_x_error_px=max_error,
            median_abs_x_error_px=median,
            x_alignment_gate="PASS" if precise else "FAIL",
            precise_terminal_projection="BLOCKED",
            control_points="AI photo correspondences, not human accepted",
            y_alignment="not independently qualified for contact assignment",
            M1_lead_region_candidates=region.get("m1_lead_rois", []),
        )
        options = [
            ("zones", "POLY上下端搜索范围（默认）"),
            ("marked", "搜索范围＋紧凑光学峰（非CT结论）"),
            ("poly", "POLY纯原图"),
            ("m1-raw", "M1原图（独立坐标）"),
            ("m1-leads", "M1原图＋引出候选区域（待对应）"),
            ("m1-candidate", "M1局部配准候选"),
            ("blend-candidate", "候选叠图：禁止据此确定CT"),
        ]
        cards.append(
            f'<section id="{key}"><h2>{key} {html.escape(region["title"])}</h2>'
            f"<p>独立源漏列横向误差：中位{median:g}px，最大{max_error}px。"
            f"精确栅CT投影：{'通过横向检查' if precise else '未通过'}；纵向未独立验收。</p>"
            f"<select onchange=\"document.getElementById('{key}-img').src=this.value\">"
            + "".join(
                f'<option value="{key}-{mode}.png">{label}</option>' for mode, label in options
            )
            + f'</select><img id="{key}-img" src="{key}-zones.png" '
            'ondblclick="window.open(this.src)"></section>'
        )
    rows = "".join(
        f"<tr><td>{g['id']}</td><td>{g['gate_id']}</td><td>{g['region']}</td>"
        f"<td>{len(g['observations']['TOP'])}</td>"
        f"<td>{len(g['observations']['BOTTOM'])}</td>"
        f"<td>{len(g['observations']['LEFT']) + len(g['observations']['RIGHT'])}</td>"
        "<td>CT归属未知</td></tr>"
        for g in inventory
    )
    (output / "index.html").write_text(
        """<!doctype html><html lang="zh"><meta charset="utf-8">
<title>Q2栅端及引出专项检查</title><style>body{max-width:1500px;margin:24px auto;background:#111c28;
color:#eee;font:17px sans-serif}section{border:1px solid #567;margin:24px 0;padding:16px}
img{width:100%;max-height:85vh;object-fit:contain}select{padding:10px}
td,th{padding:5px;border:1px solid #567}
a{color:#7de}</style><h1>30条栅极：上下端及侧向引出专项检查</h1>
<p>紫线是原有POLY派生定位，橙框为上下端搜索范围；可切换的蓝色十字仅表示紧凑光学峰，
不是已识别CT。宽松亮峰中混有拍屏网格和材料亮边，完整记录留在台账，不当作孔。
侧向观察收在逐栅台账。原1825个CT、AA/POLY模型不改。</p>
<p>候选M1配准未通过精确端口投影质量门，仅用于对照区域走线；不会据此生成接触孔或连接。
M1原图有独立坐标，切换不能当作像素级对齐。双击图像可放大。</p>
<p>请集中判断：A／B下端的亮短条是否包含栅CT，还是仅材料边缘？C的上端/下端何处是实际栅引出？
目前不将任何一组栅判为共栅或独立栅。</p>
<p><a href="observations.json">60端部及60侧向搜索区台账</a> ·
<a href="report.json">范围与质量门</a></p>"""
        + "".join(cards)
        + "<details><summary>30条栅极的光学峰数量（不是孔数）</summary><table><tr>"
        "<th>图中编号</th><th>稳定ID</th><th>区域</th><th>上端峰</th><th>下端峰</th>"
        "<th>侧向峰</th><th>状态</th></tr>" + rows + "</table></details></html>"
    )
    for ref in refs.values():
        if digest(root / ref["path"]) != ref["sha256"]:
            raise ValueError("Input changed during audit")
    report = dict(
        gates=len(inventory),
        top_bottom_zones=2 * len(inventory),
        lateral_zones=2 * len(inventory),
        exported_new_CT=0,
        parent_CT_count=len(parent["objects"]),
        source_and_material_hashes_unchanged=True,
        regions=region_reports,
        result="terminal_and_lead_candidates_need_human_judgment",
        peak_counts_are_not_contact_counts=True,
        implementation_sha256=digest(Path(__file__)),
    )
    if "bottom_localization" in spec:
        localized = localize_bottom_contacts(
            source, material, source_spec, spec["bottom_localization"]
        )
        write(
            output / "bottom-localization.json",
            dict(
                gates=localized,
                interpretation="measured candidate locations, not exact human point annotations",
            ),
        )
    write(output / "report.json", report)
    write(output / "observations.json", dict(gates=inventory))
    write(output / "spec.json", spec)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--spec", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = run(args.root, args.spec, args.output)
    print(json.dumps({k: v for k, v in result.items() if k != "regions"}, ensure_ascii=False))
