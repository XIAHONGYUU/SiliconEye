"""Build a source-bound block/registration/material review package.

Run: silicon-eye annotate review-package --spec request.json --root . -o new-dir
Requires existing Pillow/OpenCV dependencies; performs no recognition or new decisions.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Literal

import cv2
import numpy as np
from PIL import Image, ImageDraw, PngImagePlugin
from pydantic import Field

from .block_export import run_block, write_json
from .block_review import fingerprint, resolve_block, verify_sources
from .device_index import DeviceViewRequest, build_device_index, render_device_index
from .schemas.block_case import BlockCase, Record, Source
from .terminal_highlight import prepare_highlight, render_highlights


class Approval(Record):
    record: Source
    pointer: str
    value: Literal["accepted"]


class RegistrationInput(Record):
    profile: Source
    approval: Approval
    frozen_matrix_pointer: str


class PackageRequest(Record):
    schema_version: Literal[1]
    document_kind: Literal["block_review_package"]
    case: Source
    registrations: list[RegistrationInput] = Field(default_factory=list)
    materials: list[Source] = Field(default_factory=list)
    observation_adaptations: list[Source] = Field(default_factory=list)
    device_view: DeviceViewRequest | None = None
    terminal_highlights: list[Source] = Field(default_factory=list)


def pointer(document, path):
    if not path.startswith("/"):
        raise ValueError("Evidence pointer must start with /")
    for part in path[1:].split("/"):
        key = part.replace("~1", "/").replace("~0", "~")
        document = document[int(key)] if isinstance(document, list) else document[key]
    return document


class Inputs:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.files = {}

    def read(self, ref):
        ref = Source(path=ref["path"], sha256=ref["sha256"]) if isinstance(ref, dict) else ref
        relative = Path(ref.path)
        path = (self.root / relative).resolve()
        if relative.is_absolute() or not path.is_relative_to(self.root) or not path.is_file():
            raise ValueError("Missing or outside-root package source: " + ref.path)
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != ref.sha256:
            raise ValueError("Package source hash changed: " + ref.path)
        if ref.path in self.files and self.files[ref.path] != ref.sha256:
            raise ValueError("Contradictory source hashes")
        self.files[ref.path] = ref.sha256
        return content

    def document(self, ref):
        doc = json.loads(self.read(ref))
        if not isinstance(doc, dict):
            raise ValueError("Package evidence must be a JSON object")
        return doc

    def evidence(self, doc):
        # Verify declared immediate evidence, not arbitrary historical JSON recursion.
        for ref in doc.get("sources", {}).values():
            if isinstance(ref, dict) and {"path", "sha256"} <= ref.keys():
                self.read(ref)

    def human(self, ref):
        doc = self.document(ref)
        if doc.get("actor") != "human" or not doc.get("statement"):
            raise ValueError("Missing bound human review statement")
        self.evidence(doc)
        return doc


def matrix(value):
    m = np.asarray(value, dtype=float)
    if m.shape != (3, 3) or not np.isfinite(m).all() or abs(np.linalg.det(m)) < 1e-12:
        raise ValueError("Invalid/singular registration matrix")
    return m


def polygon(value, size):
    p = np.asarray(value, dtype=float)
    if p.ndim != 2 or p.shape[1] != 2 or len(p) < 3 or not np.isfinite(p).all():
        raise ValueError("Invalid support polygon")
    if (p < 0).any() or (p >= np.array(size)).any() or cv2.contourArea(p.astype("float32")) == 0:
        raise ValueError("Polygon outside native frame or degenerate")
    return p


def prepare(request, inputs):
    case = BlockCase.model_validate_json(inputs.read(request.case))
    verify_sources(case, inputs.root)
    for source in case.sources.values():
        inputs.read(source)
    frames = {f.id: f for f in case.frames}

    def photo(ref):
        inputs.read(ref)
        matches = [
            f for f in case.frames
            if case.sources[f.source_ref].path == ref["path"]
            and case.sources[f.source_ref].sha256 == ref["sha256"]
        ]
        if len(matches) != 1:
            raise ValueError("Registration/material photo does not match one case frame")
        return matches[0]

    registrations, materials = [], []
    for entry in request.registrations:
        doc = inputs.document(entry.profile)
        review = inputs.human(entry.approval.record)
        if doc["decision_source"] != entry.approval.record.model_dump():
            raise ValueError("Registration approval bound to a different record")
        if pointer(review, entry.approval.pointer) != entry.approval.value:
            raise ValueError("Registration approval assertion not accepted")
        gate = inputs.document(review["sources"]["review_gate"])
        if gate["case_id"] != case.case_id:
            raise ValueError("Registration review belongs to another case")
        if gate["sources"]["frozen_transform"] != doc["frozen_transform_source"]:
            raise ValueError("Transform is not the one presented for human review")
        if doc["acceptance"]["macro_overlay"] is not True:
            raise ValueError("Profile has no macro acceptance")
        if doc["mapping_direction"] != "target_native_to_reference_native":
            raise ValueError("Unsupported matrix direction")
        frozen = inputs.document(doc["frozen_transform_source"])
        h = matrix(doc["matrix"])
        if not np.array_equal(h, matrix(pointer(frozen, entry.frozen_matrix_pointer))):
            raise ValueError("Registration matrix differs from frozen evidence")
        ref, target = photo(doc["reference"]), photo(doc["target"])
        t = matrix(doc["reference_native_to_output_crop"])
        if not np.array_equal(t[:2, :2], np.eye(2)) or not np.array_equal(t[2], [0, 0, 1]):
            raise ValueError("Output crop must be native-pixel translation")
        origin = -t[:2, 2]
        size = np.array(doc["output_crop_size_wh"], dtype=float)
        if (
            size.shape != (2,) or not np.isfinite(size).all() or (size <= 0).any()
            or not np.equal(size, np.floor(size)).all()
            or (origin < 0).any() or not np.equal(origin, np.floor(origin)).all()
            or (origin + size > ref.size_wh).any()
        ):
            raise ValueError("Invalid output crop bounds")
        polygons = [polygon(p, ref.size_wh) for p in doc["reviewed_reference_frame_polygons_xy"]]
        if not polygons:
            raise ValueError("Registration needs explicit reviewed scope")
        for p in polygons:
            q = cv2.perspectiveTransform(p.reshape(-1, 1, 2), np.linalg.inv(h)).reshape(-1, 2)
            denominators = np.c_[p, np.ones(len(p))] @ np.linalg.inv(h)[2]
            if not np.isfinite(q).all() or min(denominators) * max(denominators) <= 0:
                raise ValueError("Registration horizon crosses reviewed scope")
        registrations.append(dict(
            profile=doc, reference_frame=ref.id, target_frame=target.id,
            acceptance=dict(macro_overlay=True, contact_landing=False, dimensions=False),
        ))
    for entry in request.materials:
        doc = inputs.document(entry)
        if doc["case_id"] != case.case_id:
            raise ValueError("Material observations belong to another case")
        inputs.evidence(doc)
        if "registration" in doc:
            inputs.read(doc["registration"])
        accepted = "review_source" in doc
        if accepted:
            review = inputs.human(doc["review_source"])
            candidate = inputs.document(review["sources"]["candidate_spec"])
            originals = {r["id"]: r for r in candidate["regions"]}
            if candidate["case_id"] != case.case_id:
                raise ValueError("Reviewed material candidate belongs to another case")
            decisions = {d["entity_id"]: d for d in review["decisions"]}
            if len(decisions) != len(review["decisions"]):
                raise ValueError("Duplicate material decisions")
        elif (
            doc.get("status") not in {"candidate", "candidate_pending_material_identity_review"}
            or doc.get("actor") not in {"reasoning_model", "vision_model"}
        ):
            raise ValueError("Unreviewed material must explicitly declare model candidate status")
        region_ids = set()
        for region in doc["regions"]:
            if accepted:
                for key in ["material", "frame", "native_source", "core_polygon_xy",
                            "envelope_polygon_xy"]:
                    if region[key] != originals[region["id"]][key]:
                        raise ValueError(
                            "Material geometry/identity differs from reviewed candidate"
                        )
            if region["id"] in region_ids:
                raise ValueError("Duplicate material regions")
            region_ids.add(region["id"])
            f = frames[region["frame"]]
            source = case.sources[f.source_ref]
            if source.path != region["native_source"]:
                raise ValueError("Material native source/frame mismatch")
            inputs.read(source)
            if region["material"] not in {"aa", "poly"}:
                raise ValueError("Unsupported material")
            decision = decisions[region["id"]] if accepted else None
            if accepted and (
                decision["material"] != region["material"]
                or decision["material_identity"] != "human_confirmed"
                or decision["coarse_location"] != "human_confirmed"
            ):
                raise ValueError("Material identity/location lacks matching human decision")
            core = polygon(region["core_polygon_xy"], f.size_wh)
            envelope = polygon(region["envelope_polygon_xy"], f.size_wh)
            support = np.vstack([core, envelope])
            lo, hi = np.floor(support.min(axis=0)), np.ceil(support.max(axis=0))
            w, h = (hi - lo + 1).astype(int)
            masks = []
            for p in [core, envelope]:
                mask = np.zeros((h, w), np.uint8)
                cv2.fillPoly(mask, [np.rint(p - lo).astype("int32")], 1)
                masks.append(mask)
            if (masks[0] > masks[1]).any():
                raise ValueError("Material core extends outside candidate envelope")
            crop = np.array(doc["crop_windows_native_xywh"][region["material"]], dtype=float)
            if (
                crop.shape != (4,) or not np.isfinite(crop).all()
                or not np.equal(crop, np.floor(crop)).all() or (crop[:2] < 0).any()
                or (crop[2:] <= 0).any() or (crop[:2] + crop[2:] > f.size_wh).any()
                or (envelope < crop[:2]).any() or (envelope >= crop[:2] + crop[2:]).any()
            ):
                raise ValueError("Material crop does not contain the envelope")
        materials.append(dict(
            observations=doc, identity_status="human_confirmed" if accepted else "candidate",
            geometry_status="candidate_not_pixel_truth", dimensions_status="unknown",
        ))
    return case, registrations, materials


def save_image(path, array, bundle_id):
    meta = PngImagePlugin.PngInfo()
    meta.add_text("bundle_id", bundle_id)
    Image.fromarray(array).save(path, pnginfo=meta)


def render_assets(state, inputs, out):
    links = []
    for i, record in enumerate(state["registrations"], 1):
        p = record["profile"]
        ref = cv2.imread(str(inputs.root / p["reference"]["path"]))
        target = cv2.imread(str(inputs.root / p["target"]["path"]))
        h, t = matrix(p["matrix"]), matrix(p["reference_native_to_output_crop"])
        w, height = p["output_crop_size_wh"]
        x, y = (-t[:2, 2]).astype(int)
        raw_ref = ref[y:y+height, x:x+w]
        warped = cv2.warpPerspective(target, t @ h, (w, height))
        valid = cv2.warpPerspective(
            np.full(target.shape[:2], 255, np.uint8), t @ h, (w, height),
            flags=cv2.INTER_NEAREST,
        )
        scope = np.zeros_like(valid)
        for polygon in p["reviewed_reference_frame_polygons_xy"]:
            points = cv2.perspectiveTransform(np.array(polygon, float).reshape(-1, 1, 2), t)
            cv2.fillPoly(scope, [np.rint(points).astype("int32")], 255)
        scope &= valid
        a, b = (cv2.cvtColor(im, cv2.COLOR_BGR2GRAY) for im in [raw_ref, warped])
        overlay = np.dstack([a, b, b])
        overlay[scope == 0] = (overlay[scope == 0].astype(float) * .28).astype("uint8")
        prefix = f"registration-{i:03}"
        for name, arr in [("aligned", cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)),
                          ("overlay", overlay), ("valid", valid), ("reviewed-scope", scope)]:
            save_image(out / f"{prefix}-{name}.png", arr, state["bundle_id"])
        links.append(f"![宏观叠图；非精细配准]({prefix}-overlay.png)")
    for i, record in enumerate(state["materials"], 1):
        doc = record["observations"]
        for material in sorted({r["material"] for r in doc["regions"]}):
            regions = [r for r in doc["regions"] if r["material"] == material]
            x, y, w, h = doc["crop_windows_native_xywh"][material]
            if len({r["native_source"] for r in regions}) != 1:
                raise ValueError("Material crop groups must share one native source")
            raw = Image.open(inputs.root / regions[0]["native_source"]).convert("RGB")
            raw = raw.crop((x, y, x+w, y+h))
            marked = raw.copy()
            drawing = ImageDraw.Draw(marked)
            color = "#f54949" if material == "aa" else "#4187ff"
            for region in regions:
                for key, width in [("envelope_polygon_xy", 1), ("core_polygon_xy", 2)]:
                    points = [tuple(np.array(p) - [x, y]) for p in region[key]]
                    drawing.line(points + [points[0]], fill=color, width=width)
            prefix = f"material-{i:03}-{material}"
            save_image(out / f"{prefix}-raw.png", np.array(raw), state["bundle_id"])
            save_image(out / f"{prefix}-support.png", np.array(marked), state["bundle_id"])
            identity = "已确认" if record["identity_status"] == "human_confirmed" else "候选待复核"
            links.append(f"![{material}身份{identity}；轮廓为候选]({prefix}-support.png)")
            links.append(f"[原生像素裁剪]({prefix}-raw.png)；与其他材料图分开保留原图坐标。")
    return links


def run_package(spec_path, output, root="."):
    """Preflight all evidence, stage exports, publish only a complete new directory."""
    out, inputs = Path(output), Inputs(root)
    if out.exists():
        raise ValueError("Output directory already exists")
    request_bytes = Path(spec_path).read_bytes()
    request = PackageRequest.model_validate_json(request_bytes)
    try:
        case, registrations, materials = prepare(request, inputs)
    except (KeyError, TypeError, IndexError) as error:
        raise ValueError(f"Invalid review package evidence: {error}") from error
    block = resolve_block(case, evidence_checked=True)
    state = dict(
        schema_version=1, case_id=case.case_id, block_state_id=block["state_id"],
        status=block["status"], registrations=registrations, materials=materials,
        input_files=dict(sorted(inputs.files.items())),
        precise_registration_accepted=False, pixel_material_truth_accepted=False,
        runtime_ai_used=False, electrical_acceptance=block["acceptance"],
    )
    if request.observation_adaptations:
        from .observation_adapter import validate_adaptation

        state["observation_adaptations"] = [
            validate_adaptation(inputs, entry, case) for entry in request.observation_adaptations
        ]
        state["input_files"] = dict(sorted(inputs.files.items()))
    if request.device_view is not None:
        state["device_index"] = build_device_index(case, block, registrations, request.device_view)
    if request.terminal_highlights:
        state["terminal_highlights"] = [
            prepare_highlight(inputs, entry, case, block, registrations)
            for entry in request.terminal_highlights
        ]
        state["input_files"] = dict(sorted(inputs.files.items()))
    state["bundle_id"] = fingerprint(state)
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".review-package-", dir=out.parent) as tmp:
        stage = Path(tmp) / "package"
        stage.mkdir()
        replay = run_block(str(inputs.root / request.case.path), str(stage / "circuit"), root)
        if replay["state_id"] != block["state_id"]:
            raise ValueError("Case changed during package export")
        links = [] if block["conflicts"] else render_assets(state, inputs, stage)
        if not block["conflicts"] and request.observation_adaptations:
            from .observation_cards import render_observation_cards

            links += render_observation_cards(state, inputs, stage)
        if not block["conflicts"] and request.device_view is not None:
            links += render_device_index(state, inputs, stage)
        if not block["conflicts"] and request.terminal_highlights:
            links += render_highlights(state, inputs, stage)
        write_json(stage / "bundle-state.json", state)
        report = [
            "# 局部器件组统一复核包", "", f"案例：{case.case_id}", "",
            f"bundle_id: `{state['bundle_id']}`", f"block_state_id: `{block['state_id']}`", "",
            "[电路状态/四端表/矩阵](circuit/report.md) · [统一数据](bundle-state.json) · "
            "[来源及产物哈希](manifest.json)", "",
            "配准仅采用已绑定的宏观批准；材料逐记录保留候选或身份/大致位置确认。"
            "候选轮廓不是像素真值，未批准CT落点/W/L/新连接。不同标签不证明隔离。", "",
            "宏观叠图框外变暗处不在本次已复核范围；有效mask与已复核范围mask分别保存。", "",
        ]
        if block["conflicts"]:
            report += ["存在电气裁决冲突：只导出诊断，不生成正常叠图/材料图。"]
        else:
            report += ["![同状态电路图](circuit/local-schematic.png)", ""] + links
        for record in materials:
            report += ["", "材料观察中的未知项："]
            report += ["- " + item for item in record["observations"].get("unknowns", [])]
        (stage / "report.md").write_text("\n".join(report) + "\n")
        for path, sha in inputs.files.items():
            inputs.read(Source(path=path, sha256=sha))
        write_json(stage / "manifest.json", dict(
            bundle_id=state["bundle_id"], block_state_id=block["state_id"],
            request_sha256=hashlib.sha256(request_bytes).hexdigest(), inputs=inputs.files,
            evidence_scope="case declared sources; selected records and immediate review evidence; "
                           "not recursive recovery of all historical files",
            code_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [
                Path(__file__), Path(__file__).with_name("block_export.py"),
                Path(__file__).with_name("block_review.py"),
                Path(__file__).parent / "schemas/block_case.py",
            ] + ([Path(__file__).with_name("observation_adapter.py"),
                  Path(__file__).with_name("observation_cards.py"),
                  Path(__file__).parent / "schemas/agent_observation.py"]
                 if request.observation_adaptations else [])
                + ([Path(__file__).with_name("device_index.py")]
                   if request.device_view is not None else [])
                + ([Path(__file__).with_name("terminal_highlight.py")]
                   if request.terminal_highlights else [])},
            outputs={str(p.relative_to(stage)): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in sorted(stage.rglob("*")) if p.is_file()},
            status=state["status"], physical_truth_verified_by_script=False,
        ))
        if out.exists():
            raise ValueError("Output directory already exists")
        stage.rename(out)
    return state
