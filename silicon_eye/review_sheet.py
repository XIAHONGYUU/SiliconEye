"""Build and validate the fixed SiliconEye human acceptance sheet.

Run:
    python -m silicon_eye.review_sheet build --spec FILE --output NEW_DIR
    python -m silicon_eye.review_sheet check --package DIR --decision FILE [--archive]
    python -m silicon_eye.review_sheet preset --stage METAL

The sheet renders declared evidence and records human verdicts. It performs no
image recognition, geometry generation, projection, or connection inference.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import shutil
import tempfile
import uuid
from collections import Counter
from datetime import UTC, date, datetime
from pathlib import Path

from PIL import Image

SCHEMA_VERSION = 1
SHEET_KIND = "silicon_eye_review_sheet"
DECISION_KIND = "silicon_eye_review_decision"
MANIFEST_KIND = "silicon_eye_review_sheet_manifest"

STAGES = ("AA", "POLY", "CT", "METAL", "VIA", "REGION", "OTHER")
VERDICTS = ("accepted", "needs_revision", "uncertain", "not_applicable")
QUESTION_VERDICTS = ("accepted", "needs_revision", "uncertain")
VERDICT_LABELS = {
    "accepted": "通过",
    "needs_revision": "需修改",
    "uncertain": "不确定",
    "not_applicable": "不适用",
}
ITEM_TYPES = (
    "aa_polygon",
    "poly_fragment",
    "ct_array",
    "metal_fragment",
    "via_interface",
    "region_boundary",
    "other",
)
ROLES = ("source", "marked", "design", "overlay", "paired", "detail", "other")
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,79}$")

COMMON_NOT_APPROVED = [
    "照片精确投影或跨帧配准",
    "PDK、实测工艺尺寸或 DRC",
    "物理孔数、孔径与节距的真值",
    "完整网表或自动网表导出",
    "共同几何采用、GDS 发布或全幅完成声明",
    "本声明范围之外的导体、器件与连接",
]

STAGE_PRESETS = {
    "AA": {
        "label": "AA 材料层",
        "questions": [
            {
                "id": "Q1",
                "prompt": "本范围 AA 几何形状、台阶/凹角、相对位置与间隙是否合理，无明显形状错误？",
                "item_types": ["aa_polygon"],
            },
            {
                "id": "Q2",
                "prompt": "本范围可见 AA 片段是否无明显遗漏（截口只表示范围出口，不是物理断点）？",
                "item_types": ["aa_polygon"],
            },
        ],
        "checks": {
            "aa_polygon": [
                {"id": "shape_reasonable", "label": "形状、台阶与凹角合理", "required": True},
                {"id": "spacing_correct", "label": "相邻间隙与相对位置合理", "required": True},
                {"id": "no_missing_segment", "label": "无明显漏段", "required": True},
            ]
        },
        "limits": ["本确认单只覆盖声明的原生窗口，不代表全幅 AA 覆盖或物理尺寸。"],
        "not_approved": COMMON_NOT_APPROVED + ["材料身份之外的电学结论"],
    },
    "POLY": {
        "label": "POLY 材料层",
        "questions": [
            {
                "id": "Q1",
                "prompt": "本范围 POLY 走向、折线转折、相对宽度及与 AA 的关系是否合理，"
                "无明显形状错误？",
                "item_types": ["poly_fragment"],
            },
            {
                "id": "Q2",
                "prompt": "本范围可见 POLY 片段是否无明显遗漏"
                "（截口只表示范围出口，不是物理断点）？",
                "item_types": ["poly_fragment"],
            },
        ],
        "checks": {
            "poly_fragment": [
                {"id": "routing_reasonable", "label": "走向与折线转折合理", "required": True},
                {"id": "relative_width_correct", "label": "相对宽度合理", "required": True},
                {"id": "aa_relation_correct", "label": "与 AA 的相对关系合理", "required": True},
                {"id": "no_missing_segment", "label": "无明显漏段", "required": True},
            ]
        },
        "limits": ["本确认单只覆盖声明的原生窗口，不代表全幅 POLY 覆盖或精确尺寸。"],
        "not_approved": COMMON_NOT_APPROVED + ["栅极电气身份或完整器件归属"],
    },
    "CT": {
        "label": "CT/端子",
        "questions": [
            {
                "id": "Q1",
                "prompt": "本范围 CT 阵列的行列、节距、相对位置与覆盖是否合理，无明显排列错误？",
                "item_types": ["ct_array"],
            },
            {
                "id": "Q2",
                "prompt": "本范围可见 CT 阵列/端子是否无明显遗漏（不把 AI 未检出当作物理不存在）？",
                "item_types": ["ct_array"],
            },
        ],
        "checks": {
            "ct_array": [
                {"id": "array_regular", "label": "行列与节距规律合理", "required": True},
                {"id": "coverage_complete", "label": "阵列覆盖无明显遗漏", "required": True},
                {"id": "carrier_correct", "label": "上下材料/端子关系合理", "required": True},
            ]
        },
        "limits": ["本确认单不把 AI 未检出当作物理不存在，也不批准逐孔实际数量。"],
        "not_approved": COMMON_NOT_APPROVED + ["逐孔物理数量或电气连接"],
    },
    "METAL": {
        "label": "金属",
        "questions": [
            {
                "id": "Q1",
                "prompt": "本范围金属几何是否合理，无明显漏段？",
                "item_types": ["metal_fragment"],
            },
            {
                "id": "Q2",
                "prompt": "本范围可见金属片段、端点与细支路是否无明显遗漏？",
                "item_types": ["metal_fragment"],
            },
            {
                "id": "Q3",
                "prompt": "新增/待确认的孔组身份、层对与上下承载是否正确？",
                "item_types": ["via_interface"],
            },
        ],
        "checks": {
            "metal_fragment": [
                {"id": "endpoints_correct", "label": "端点/范围出口状态正确", "required": True},
                {"id": "no_missing_segment", "label": "无明显漏段", "required": True},
                {
                    "id": "native_path_matches",
                    "label": "原图对应与相对走向合理（允许畸变校正）",
                    "required": True,
                },
            ],
            "via_interface": [
                {"id": "via_present", "label": "孔组在照片中可见", "required": True},
                {"id": "layer_pair_correct", "label": "孔层与上下金属层对正确", "required": True},
                {"id": "lower_carrier_correct", "label": "下金属承载正确", "required": True},
                {"id": "upper_carrier_correct", "label": "上金属承载正确", "required": True},
            ],
        },
        "limits": [
            "本确认单只覆盖声明的原生窗口和已列对象，不代表全幅金属或五层穷尽覆盖。",
            "范围出口不是物理终点；旧批准、孔中心与未列对象保持不变。",
        ],
        "not_approved": COMMON_NOT_APPROVED,
    },
    "VIA": {
        "label": "层间孔",
        "questions": [
            {
                "id": "Q1",
                "prompt": "孔组身份、层对与上下金属承载是否正确？",
                "item_types": ["via_interface"],
            },
            {
                "id": "Q2",
                "prompt": "声明孔组的落点与上下金属相对位置是否合理（不要求逐孔计数）？",
                "item_types": ["via_interface"],
            },
        ],
        "checks": {
            "via_interface": [
                {"id": "via_present", "label": "孔组在照片中可见", "required": True},
                {"id": "layer_pair_correct", "label": "孔层与上下金属层对正确", "required": True},
                {"id": "lower_carrier_correct", "label": "下金属承载正确", "required": True},
                {"id": "upper_carrier_correct", "label": "上金属承载正确", "required": True},
            ]
        },
        "limits": ["本确认单只判断声明的孔组，不把 AI 未检出当作物理不存在。"],
        "not_approved": COMMON_NOT_APPROVED,
    },
    "REGION": {
        "label": "范围规划",
        "questions": [
            {
                "id": "Q1",
                "prompt": "本范围边界是否覆盖所有可见结构，且没有把范围出口当作物理终点？",
                "item_types": ["region_boundary"],
            },
            {
                "id": "Q2",
                "prompt": "本范围是否适合作为下一轮连续重建的固定范围？",
                "item_types": ["region_boundary"],
            },
        ],
        "checks": {
            "region_boundary": [
                {"id": "covers_visible", "label": "覆盖全部可见结构", "required": True},
                {"id": "exit_state_correct", "label": "范围出口状态正确", "required": True},
            ]
        },
        "limits": ["范围选择不证明照片穷尽，也不等于几何或连接已通过。"],
        "not_approved": ["范围外结构完整性", "精确投影或配准", "电气连接或完整网表"],
    },
    "OTHER": {
        "label": "其他",
        "questions": [],
        "checks": {},
        "limits": [],
        "not_approved": [],
    },
}


class DecisionError(ValueError):
    """A human decision did not satisfy the fixed review-sheet contract."""

    def __init__(self, errors):
        self.errors = list(errors)
        super().__init__("\n".join(self.errors))


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def now_utc():
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def parse_iso8601(value, label):
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{label} must be an ISO 8601 string or null")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO 8601 timestamp") from exc
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def display_path(path, root):
    path, root = Path(path).resolve(), Path(root).resolve()
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def safe_name(path):
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(path).name) or "asset"
    return name[:80].lstrip(".") or "asset"


def validate_id(value, label):
    require(isinstance(value, str) and ID_PATTERN.fullmatch(value), f"Invalid {label}: {value!r}")


def image_size(path):
    if path.suffix.lower() == ".svg":
        return None
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            return list(image.size)
    except Exception as error:  # PIL raises several concrete exception types
        raise ValueError(f"Evidence is not a readable image: {path}") from error


def preset_questions(stage, items):
    questions = []
    for question in STAGE_PRESETS[stage]["questions"]:
        item_ids = [
            item["id"] for item in items
            if item["type"] in question["item_types"]
            and item.get("review_mode", "decision") != "context"
        ]
        if item_ids:
            questions.append(
                {
                    "id": question["id"],
                    "prompt": question["prompt"],
                    "item_ids": item_ids,
                    "required": True,
                }
            )
    return questions


def normalize_spec(root, raw):
    root = Path(root).resolve()
    require(isinstance(raw, dict), "Review spec must be a JSON object")
    require(raw.get("kind", SHEET_KIND) == SHEET_KIND, "Unsupported review spec kind")
    require(raw.get("schema_version", SCHEMA_VERSION) == SCHEMA_VERSION, "Unsupported schema")

    stage = str(raw.get("stage", "")).upper()
    require(stage in STAGES, f"Unsupported stage: {raw.get('stage')!r}")
    preset = STAGE_PRESETS[stage]
    package_id = raw.get("package_id")
    validate_id(package_id, "package_id")
    title = raw.get("title", package_id)
    require(isinstance(title, str) and title.strip(), "title must be a non-empty string")

    sheet_date = raw.get("date") or date.today().isoformat()
    try:
        date.fromisoformat(sheet_date)
    except (TypeError, ValueError) as error:
        raise ValueError(f"Invalid date: {sheet_date!r}") from error

    scope = raw.get("scope", {})
    require(isinstance(scope, dict), "scope must be an object")
    frame = scope.get("frame")
    require(isinstance(frame, str) and frame.strip(), "scope.frame is required")
    bounds = scope.get("native_bounds")
    if bounds is not None:
        require(
            isinstance(bounds, list)
            and len(bounds) == 4
            and all(isinstance(value, (int, float)) for value in bounds)
            and bounds[0] < bounds[2]
            and bounds[1] < bounds[3],
            "scope.native_bounds must be [left, top, right, bottom]",
        )
    note = scope.get("note", "")
    require(isinstance(note, str), "scope.note must be a string")
    summary = raw.get("summary", "")
    require(isinstance(summary, str), "summary must be a string")

    items_raw = raw.get("items")
    require(isinstance(items_raw, list) and items_raw, "items must be a non-empty list")
    items, item_ids = [], set()
    for item in items_raw:
        require(isinstance(item, dict), "Each item must be an object")
        item_id = item.get("id")
        validate_id(item_id, "item id")
        require(item_id not in item_ids, f"Duplicate item id: {item_id}")
        item_ids.add(item_id)
        item_type = item.get("type")
        require(item_type in ITEM_TYPES, f"Unsupported item type: {item_type!r}")
        item_title = item.get("title", item_id)
        require(isinstance(item_title, str) and item_title.strip(), "Item title is empty")
        prompt = item.get("prompt")
        require(isinstance(prompt, str) and prompt.strip(), f"Item {item_id} has no prompt")
        review_mode = item.get("review_mode", "decision")
        require(review_mode in {"decision", "context"}, "Invalid item.review_mode")
        required = item.get("required", review_mode != "context")
        require(isinstance(required, bool), "item.required must be boolean")
        require(not (review_mode == "context" and required), "Context cannot require a verdict")
        change_summary = item.get("change_summary", "")
        require(isinstance(change_summary, str), "item.change_summary must be a string")
        facts = item.get("facts", {})
        require(isinstance(facts, dict), f"Item {item_id} facts must be an object")

        evidence_raw = item.get("evidence", [])
        require(isinstance(evidence_raw, list), f"Item {item_id} evidence must be a list")
        evidence = []
        for entry in evidence_raw:
            require(isinstance(entry, dict), "Evidence entry must be an object")
            source = entry.get("path")
            require(isinstance(source, str) and source, f"Item {item_id} evidence path missing")
            source_path = (root / source).resolve()
            require(
                source_path.is_relative_to(root) and source_path.is_file(),
                f"Evidence outside root or missing: {source}",
            )
            require(
                source_path.suffix.lower() in IMAGE_SUFFIXES,
                f"Unsupported evidence type: {source}",
            )
            role = entry.get("role", "source")
            require(role in ROLES, f"Unsupported evidence role: {role!r}")
            label = entry.get("label", source_path.name)
            require(isinstance(label, str) and label.strip(), "Evidence label is empty")
            caption = entry.get("caption", "")
            require(isinstance(caption, str), "Evidence caption must be a string")
            evidence_frame = entry.get("frame", "")
            require(isinstance(evidence_frame, str), "Evidence frame must be a string")
            evidence.append(
                {
                    "path": display_path(source_path, root),
                    "label": label,
                    "role": role,
                    "caption": caption,
                    "frame": evidence_frame,
                    "sha256": digest(source_path),
                    "width_height": image_size(source_path),
                }
            )

        if review_mode == "context":
            checks = []
        elif "checks" in item:
            checks_raw = item["checks"]
            require(isinstance(checks_raw, list), f"Item {item_id} checks must be a list")
            checks = copy.deepcopy(checks_raw)
        else:
            checks = copy.deepcopy(preset["checks"].get(item_type, []))
        check_ids = set()
        for check in checks:
            require(isinstance(check, dict), "Each check must be an object")
            check_id = check.get("id")
            validate_id(check_id, "check id")
            require(check_id not in check_ids, f"Duplicate check id in {item_id}: {check_id}")
            check_ids.add(check_id)
            require(
                isinstance(check.get("label"), str) and check["label"].strip(),
                f"Check {check_id} has no label",
            )
            check["required"] = bool(check.get("required", False))

        note_required_on = item.get("note_required_on", ["needs_revision", "not_applicable"])
        require(isinstance(note_required_on, list), "note_required_on must be a list")
        require(
            all(value in VERDICTS for value in note_required_on),
            f"Item {item_id} has an unsupported note_required_on verdict",
        )
        items.append(
            {
                "id": item_id,
                "type": item_type,
                "title": item_title,
                "prompt": prompt,
                "required": required,
                "review_mode": review_mode,
                "change_summary": change_summary,
                "facts": facts,
                "evidence": evidence,
                "checks": checks,
                "note_required_on": note_required_on,
            }
        )

    if "questions" in raw:
        questions_raw = raw["questions"]
        require(isinstance(questions_raw, list), "questions must be a list")
        questions = []
        for question in questions_raw:
            require(isinstance(question, dict), "Each question must be an object")
            question_id = question.get("id")
            validate_id(question_id, "question id")
            prompt = question.get("prompt")
            require(
                isinstance(prompt, str) and prompt.strip(),
                f"Question {question_id} has no prompt",
            )
            if "item_ids" in question:
                covered = question["item_ids"]
                require(
                    isinstance(covered, list) and covered,
                    f"Question {question_id} must cover items",
                )
                require(
                    all(isinstance(value, str) for value in covered),
                    f"Question {question_id} item_ids must be strings",
                )
            else:
                item_types = question.get("item_types", [])
                require(
                    isinstance(item_types, list)
                    and all(value in ITEM_TYPES for value in item_types),
                    f"Question {question_id} has invalid item_types",
                )
                covered = [
                    item["id"] for item in items
                    if item["type"] in item_types and item["review_mode"] != "context"
                ]
                require(covered, f"Question {question_id} covers no items")
            require(
                len(set(covered)) == len(covered),
                f"Question {question_id} repeats an item id",
            )
            require(
                set(covered) <= item_ids,
                f"Question {question_id} references unknown items: "
                + ", ".join(sorted(set(covered) - item_ids)),
            )
            context_ids = {item["id"] for item in items if item["review_mode"] == "context"}
            require(not (set(covered) & context_ids), "Questions cannot re-review context items")
            questions.append(
                {
                    "id": question_id,
                    "prompt": prompt,
                    "item_ids": covered,
                    "required": bool(question.get("required", True)),
                }
            )
    else:
        questions = preset_questions(stage, items)
    question_ids = [question["id"] for question in questions]
    require(len(set(question_ids)) == len(question_ids), "Duplicate question id")

    limits = raw.get("limits", preset["limits"])
    not_approved = raw.get("not_approved", preset["not_approved"])
    for name, values in (("limits", limits), ("not_approved", not_approved)):
        require(
            isinstance(values, list) and all(isinstance(value, str) for value in values),
            f"{name} must be a list of strings",
        )

    sources = raw.get("sources", {})
    require(isinstance(sources, dict), "sources must be an object")
    checked_sources = {}
    for key, ref in sources.items():
        require(isinstance(key, str) and key, "Source names must be non-empty strings")
        require(isinstance(ref, dict), f"Source {key} must be an object")
        path, expected = ref.get("path"), ref.get("sha256")
        require(isinstance(path, str) and isinstance(expected, str), f"Source {key} is incomplete")
        source_path = (root / path).resolve()
        require(
            source_path.is_relative_to(root) and source_path.is_file(),
            f"Source {key} is outside root or missing",
        )
        actual = digest(source_path)
        require(actual == expected, f"Source {key} hash changed")
        checked_sources[key] = {"path": display_path(source_path, root), "sha256": actual}

    return {
        "schema_version": SCHEMA_VERSION,
        "kind": SHEET_KIND,
        "package_id": package_id,
        "stage": stage,
        "stage_label": preset["label"],
        "title": title.strip(),
        "date": sheet_date,
        "summary": summary,
        "scope": {"frame": frame, "native_bounds": bounds, "note": note},
        "items": items,
        "questions": questions,
        "limits": limits,
        "not_approved": not_approved,
        "sources": checked_sources,
    }


def _copy_assets(spec, root, stage):
    assets_dir = stage / "assets"
    assets_dir.mkdir()
    seen, assets, page_items = {}, [], []
    for item in spec["items"]:
        page_evidence = []
        for entry in item["evidence"]:
            source = (root / entry["path"]).resolve()
            if entry["path"] not in seen:
                name = f"{entry['sha256'][:10]}-{safe_name(source)}"
                destination = assets_dir / name
                shutil.copyfile(source, destination)
                record = {
                    "source_path": entry["path"],
                    "source_sha256": entry["sha256"],
                    "output_path": f"assets/{name}",
                    "output_sha256": digest(destination),
                    "width_height": entry["width_height"],
                }
                seen[entry["path"]] = record
                assets.append(record)
            record = seen[entry["path"]]
            page_evidence.append(
                {
                    "label": entry["label"],
                    "role": entry["role"],
                    "caption": entry["caption"],
                    "frame": entry["frame"],
                    "url": record["output_path"],
                    "width_height": record["width_height"],
                    "source_path": entry["path"],
                    "sha256": entry["sha256"],
                }
            )
        page_items.append({**item, "evidence": page_evidence})
    return page_items, assets


def build(root, spec_path, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    spec_path = Path(spec_path).resolve()
    require(
        output.is_relative_to(root) and not output.exists(),
        "Output must be a new directory inside the project root",
    )
    require(
        spec_path.is_relative_to(root) and spec_path.is_file(),
        "Review spec must be inside the project root",
    )
    spec = normalize_spec(root, json.loads(spec_path.read_text()))

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".review-sheet-", dir=output.parent) as tmp:
        stage = Path(tmp) / "package"
        stage.mkdir()
        page_items, assets = _copy_assets(spec, root, stage)
        spec_out = stage / "review-spec.json"
        spec_out.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n")
        build_id = uuid.uuid4().hex
        created_at = now_utc()
        spec_sha = digest(spec_out)
        payload = {
            "spec": {**spec, "items": page_items},
            "build": {
                "build_id": build_id,
                "package_id": spec["package_id"],
                "stage": spec["stage"],
                "stage_label": spec["stage_label"],
                "created_at": created_at,
                "spec_sha256": spec_sha,
            },
            "labels": {
                "verdicts": VERDICT_LABELS,
                "question_verdicts": {key: VERDICT_LABELS[key] for key in QUESTION_VERDICTS},
                "roles": {
                    "source": "原图",
                    "marked": "标记图",
                    "design": "规则图",
                    "overlay": "叠加图",
                    "paired": "分层并列（独立坐标）",
                    "detail": "放大图",
                    "other": "其他",
                },
                "types": {
                    "aa_polygon": "AA 多边形",
                    "poly_fragment": "POLY 片段",
                    "ct_array": "CT 阵列",
                    "metal_fragment": "金属片段",
                    "via_interface": "孔组接口",
                    "region_boundary": "范围边界",
                    "other": "其他",
                },
            },
        }
        encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        encoded = encoded.replace("<", "\\u003c").replace(">", "\\u003e")
        template = Path(__file__).with_suffix(".html").read_text()
        page = template.replace("__PAYLOAD__", encoded)
        (stage / "index.html").write_text(page)

        manifest = {
            "schema_version": SCHEMA_VERSION,
            "kind": MANIFEST_KIND,
            "build_id": build_id,
            "package_id": spec["package_id"],
            "stage": spec["stage"],
            "created_at": created_at,
            "spec_sha256": spec_sha,
            "page_sha256": digest(stage / "index.html"),
            "template_sha256": digest(Path(__file__).with_suffix(".html")),
            "code_sha256": digest(Path(__file__)),
            "assets": assets,
            "sources": spec["sources"],
            "counts": {
                "items": len(spec["items"]),
                "required_items": sum(item["required"] for item in spec["items"]),
                "questions": len(spec["questions"]),
                "required_questions": sum(
                    question["required"] for question in spec["questions"]
                ),
                "evidence": len(assets),
            },
        }
        (stage / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
        )
        stage.rename(output)

    return {
        "status": "BUILT",
        "package_id": spec["package_id"],
        "stage": spec["stage"],
        "build_id": build_id,
        "output": display_path(output, root),
        "counts": manifest["counts"],
        "open": display_path(output / "index.html", root),
    }


def load_package(package):
    package = Path(package).resolve()
    require(package.is_dir(), "Review package directory is missing")
    manifest_path = package / "manifest.json"
    spec_path = package / "review-spec.json"
    page_path = package / "index.html"
    for path in (manifest_path, spec_path, page_path):
        require(path.is_file(), f"Review package is incomplete: {path.name}")
    manifest = json.loads(manifest_path.read_text())
    require(manifest.get("kind") == MANIFEST_KIND, "Not a review-sheet package")
    require(manifest.get("schema_version") == SCHEMA_VERSION, "Unsupported package version")
    require(digest(page_path) == manifest.get("page_sha256"), "Review page hash changed")
    require(digest(spec_path) == manifest.get("spec_sha256"), "Review spec hash changed")
    for asset in manifest.get("assets", []):
        path = package / asset["output_path"]
        require(path.is_file(), f"Review asset is missing: {asset['output_path']}")
        require(digest(path) == asset["output_sha256"], f"Review asset hash changed: {path.name}")
    spec = json.loads(spec_path.read_text())
    require(spec.get("package_id") == manifest.get("package_id"), "Package id mismatch")
    return manifest, spec


def normalize_decision(manifest, spec, raw):
    errors = []
    if not isinstance(raw, dict):
        raise DecisionError(["Decision must be a JSON object"])
    if raw.get("kind") != DECISION_KIND:
        errors.append(f"Decision kind must be {DECISION_KIND}")
    if raw.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"Decision schema_version must be {SCHEMA_VERSION}")
    if raw.get("build_id") != manifest.get("build_id"):
        errors.append("Decision was not made against this package build")
    if raw.get("package_id") != spec.get("package_id"):
        errors.append("Decision package_id mismatch")
    if raw.get("stage") != spec.get("stage"):
        errors.append("Decision stage mismatch")
    if raw.get("actor") != "human":
        errors.append("Decision actor must be human")
    try:
        date.fromisoformat(raw.get("date", ""))
    except (TypeError, ValueError):
        errors.append("Decision date must be YYYY-MM-DD")
    if raw.get("limits_acknowledged") is not True:
        errors.append("The declared boundaries must be explicitly acknowledged")
    review_started_at = review_exported_at = review_seconds = None
    try:
        review_started_at = parse_iso8601(raw.get("review_started_at"), "review_started_at")
        review_exported_at = parse_iso8601(raw.get("review_exported_at"), "review_exported_at")
    except ValueError as exc:
        errors.append(str(exc))
    if review_started_at and review_exported_at:
        if review_exported_at < review_started_at:
            errors.append("review_exported_at must not be before review_started_at")
        else:
            review_seconds = round(
                (review_exported_at - review_started_at).total_seconds(), 3
            )
    statement = raw.get("statement", "")
    if not isinstance(statement, str):
        errors.append("Decision statement must be a string")
        statement = ""

    items = {item["id"]: item for item in spec["items"]}
    answers_raw = raw.get("answers")
    if not isinstance(answers_raw, list):
        raise DecisionError(errors + ["Decision answers must be a list"])
    provided = {}
    for answer in answers_raw:
        if not isinstance(answer, dict):
            errors.append("Each answer must be an object")
            continue
        item_id = answer.get("item_id")
        if item_id not in items:
            errors.append(f"Unknown item id: {item_id!r}")
            continue
        if item_id in provided:
            errors.append(f"Duplicate answer for item: {item_id}")
            continue
        if items[item_id].get("review_mode") == "context":
            errors.append(f"Context item cannot receive a new verdict: {item_id}")
            continue
        provided[item_id] = answer

    answers = []
    for item in spec["items"]:
        item_id = item["id"]
        if item_id not in provided:
            if item["required"]:
                errors.append(f"Required item is unanswered: {item_id}")
            continue
        answer = provided[item_id]
        verdict = answer.get("verdict")
        if verdict not in VERDICTS:
            errors.append(f"Item {item_id} has an invalid verdict: {verdict!r}")
            continue
        checks_raw = answer.get("checks", {})
        if not isinstance(checks_raw, dict):
            errors.append(f"Item {item_id} checks must be an object")
            checks_raw = {}
        checks = {}
        for check in item["checks"]:
            value = checks_raw.get(check["id"], False)
            if not isinstance(value, bool):
                errors.append(f"Item {item_id} check {check['id']} must be boolean")
                value = False
            checks[check["id"]] = value
        unknown_checks = set(checks_raw) - {check["id"] for check in item["checks"]}
        if unknown_checks:
            errors.append(
                f"Item {item_id} has unknown checks: " + ", ".join(sorted(unknown_checks))
            )
        if verdict == "accepted":
            missing = [
                check["id"]
                for check in item["checks"]
                if check["required"] and not checks[check["id"]]
            ]
            if missing:
                errors.append(
                    f"Item {item_id} cannot be accepted with unchecked required checks: "
                    + ", ".join(missing)
                )
        notes = answer.get("notes", "")
        if not isinstance(notes, str):
            errors.append(f"Item {item_id} notes must be a string")
            notes = ""
        if verdict in item["note_required_on"] and not notes.strip():
            errors.append(f"Item {item_id} requires a note for verdict {verdict}")
        answers.append(
            {"item_id": item_id, "verdict": verdict, "checks": checks, "notes": notes.strip()}
        )

    questions = {question["id"]: question for question in spec["questions"]}
    questions_raw = raw.get("questions", [])
    if not isinstance(questions_raw, list):
        errors.append("Decision questions must be a list")
        questions_raw = []
    provided_questions = {}
    for answer in questions_raw:
        if not isinstance(answer, dict):
            errors.append("Each question answer must be an object")
            continue
        question_id = answer.get("question_id")
        if question_id not in questions:
            errors.append(f"Unknown question id: {question_id!r}")
            continue
        if question_id in provided_questions:
            errors.append(f"Duplicate answer for question: {question_id}")
            continue
        provided_questions[question_id] = answer

    question_answers = []
    for question in spec["questions"]:
        question_id = question["id"]
        if question_id not in provided_questions:
            if question["required"]:
                errors.append(f"Required question is unanswered: {question_id}")
            continue
        answer = provided_questions[question_id]
        verdict = answer.get("verdict")
        if verdict not in QUESTION_VERDICTS:
            errors.append(f"Question {question_id} has an invalid verdict: {verdict!r}")
            continue
        notes = answer.get("notes", "")
        if not isinstance(notes, str):
            errors.append(f"Question {question_id} notes must be a string")
            notes = ""
        question_answers.append(
            {"question_id": question_id, "verdict": verdict, "notes": notes.strip()}
        )

    by_item = {answer["item_id"]: answer for answer in answers}
    for answer in question_answers:
        if answer["verdict"] != "accepted":
            continue
        covered = questions[answer["question_id"]]["item_ids"]
        blocked = [
            f"{item_id}={by_item[item_id]['verdict']}"
            for item_id in covered
            if item_id in by_item
            and by_item[item_id]["verdict"] in {"needs_revision", "uncertain"}
        ]
        if blocked:
            errors.append(
                f"Question {answer['question_id']} cannot be accepted while covered items "
                "are not: " + ", ".join(blocked)
            )
        missing = [item_id for item_id in covered if item_id not in by_item]
        if missing:
            errors.append(
                f"Question {answer['question_id']} cannot be accepted with unanswered covered "
                "items: " + ", ".join(missing)
            )
        if not any(by_item.get(item_id, {}).get("verdict") == "accepted" for item_id in covered):
            errors.append(f"Question {answer['question_id']} has no applicable accepted items")

    if errors:
        raise DecisionError(errors)

    return {
        "schema_version": SCHEMA_VERSION,
        "kind": DECISION_KIND,
        "package_id": spec["package_id"],
        "build_id": manifest["build_id"],
        "stage": spec["stage"],
        "actor": "human",
        "date": raw["date"],
        "statement": statement.strip(),
        "limits_acknowledged": True,
        "review_started_at": (
            review_started_at.isoformat() if review_started_at is not None else None
        ),
        "review_exported_at": (
            review_exported_at.isoformat() if review_exported_at is not None else None
        ),
        "review_seconds": review_seconds,
        "answers": answers,
        "questions": question_answers,
        "sources": {},
        "recorded_scope": spec["scope"],
        "not_approved": spec["not_approved"],
    }


def render_record(record, spec):
    def cell(value):
        return str(value).replace("|", "\\|").replace("\n", "<br>") or "—"

    item_by_id = {item["id"]: item for item in spec["items"]}
    lines = [
        "# 验收确认记录",
        "",
        f"- 送审包：{spec['package_id']}",
        f"- 阶段：{spec['stage_label']}（{spec['stage']}）",
        f"- 日期：{record['date']}",
        f"- 送审版本：{record['build_id']}",
        "- 范围："
        + spec["scope"]["frame"]
        + (f" 原生窗口 {spec['scope']['native_bounds']}" if spec["scope"]["native_bounds"] else ""),
    ]
    if record["statement"]:
        lines.append(f"- 总体意见：{record['statement']}")
    if record.get("review_started_at") or record.get("review_exported_at"):
        started = record.get("review_started_at") or "未记录"
        exported = record.get("review_exported_at") or "未记录"
        seconds = record.get("review_seconds")
        elapsed = f"{seconds / 60:.1f} 分钟" if seconds is not None else "未计算"
        lines.append(f"- 复核计时：开始 {started}；导出 {exported}；墙钟用时 {elapsed}")
    lines += [
        "",
        "## 逐项确认",
        "",
        "| 项目 | 类型 | 结论 | 检查 | 备注 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for answer in record["answers"]:
        item = item_by_id[answer["item_id"]]
        labels = {check["id"]: check["label"] for check in item["checks"]}
        checks = "；".join(
            f"{labels[key]}={'是' if value else '否'}" for key, value in answer["checks"].items()
        )
        lines.append(
            f"| {cell(item['title'])}（{cell(item['id'])}） | {cell(item['type'])} | "
            f"{VERDICT_LABELS[answer['verdict']]} | {cell(checks)} | {cell(answer['notes'])} |"
        )
    if record["questions"]:
        lines += ["", "## 整体问题", ""]
        for answer in record["questions"]:
            question = next(
                value for value in spec["questions"] if value["id"] == answer["question_id"]
            )
            lines.append(
                f"- **{answer['question_id']} {question['prompt']}** → "
                f"{VERDICT_LABELS[answer['verdict']]}"
                + (f"；{answer['notes']}" if answer["notes"] else "")
            )
    lines += ["", "## 未批准边界", ""]
    lines += [f"- {value}" for value in spec["not_approved"]] or ["- 无"]
    lines += ["", "## 来源绑定", ""]
    for name, ref in record["sources"].items():
        value = ref.get("sha256") or ref.get("manifest_sha256") or ""
        lines.append(f"- {name}：{ref['path']} · {value}")
    lines += [
        "",
        "## 声明",
        "",
        "本记录只记录对送审内容的判断，不自动批准精确尺寸、物理孔数、PDK/DRC、"
        "完整网表或共同几何采用。",
        "",
    ]
    return "\n".join(lines)


def check(root, package, decision_path, archive=False):
    root, package = Path(root).resolve(), Path(package).resolve()
    manifest, spec = load_package(package)
    raw = json.loads(Path(decision_path).read_text())
    record = normalize_decision(manifest, spec, raw)
    package_ref = display_path(package, root)
    record["sources"] = {
        "submitted_package": {
            "path": package_ref,
            "manifest_sha256": digest(package / "manifest.json"),
        },
        "submitted_page": {
            "path": f"{package_ref}/index.html",
            "sha256": manifest["page_sha256"],
        },
        "submitted_spec": {
            "path": f"{package_ref}/review-spec.json",
            "sha256": manifest["spec_sha256"],
        },
    }
    summary = {
        "status": "VALID",
        "package_id": spec["package_id"],
        "stage": spec["stage"],
        "build_id": manifest["build_id"],
        "date": record["date"],
        "review_started_at": record["review_started_at"],
        "review_exported_at": record["review_exported_at"],
        "review_seconds": record["review_seconds"],
        "answers": len(record["answers"]),
        "required_answers": sum(item["required"] for item in spec["items"]),
        "verdicts": dict(Counter(answer["verdict"] for answer in record["answers"])),
        "questions": dict(Counter(answer["verdict"] for answer in record["questions"])),
        "limits_acknowledged": True,
    }
    if archive:
        decision_out = package / "review-decision.json"
        record_out = package / "review-record.md"
        decision_text = json.dumps(record, ensure_ascii=False, indent=2) + "\n"
        record_text = render_record(record, spec)
        if decision_out.exists():
            require(
                decision_out.read_text() == decision_text,
                "Existing review-decision.json differs; refusing to overwrite",
            )
        if record_out.exists():
            require(
                record_out.read_text() == record_text,
                "Existing review-record.md differs; refusing to overwrite",
            )
        decision_out.write_text(decision_text)
        record_out.write_text(record_text)
        summary["archive"] = {
            "decision": display_path(decision_out, root),
            "record": display_path(record_out, root),
        }
    return summary


def _dispatch(args):
    try:
        if args.review_action == "build":
            summary = build(args.root, args.spec, args.output)
        elif args.review_action == "check":
            summary = check(args.root, args.package, args.decision, args.archive)
        elif args.review_action == "preset":
            stage = args.stage.upper()
            require(stage in STAGES, f"Unsupported stage: {args.stage!r}")
            preset = copy.deepcopy(STAGE_PRESETS[stage])
            preset["stage"] = stage
            summary = preset
        else:
            raise ValueError("Unknown review-sheet action")
    except (ValueError, OSError, KeyError, TypeError) as error:
        raise SystemExit(f"Review sheet failed: {error}") from error
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def _add_commands(commands):
    build_parser = commands.add_parser("build", help="Build a fixed acceptance sheet")
    build_parser.add_argument("--spec", type=Path, required=True)
    build_parser.add_argument("--output", type=Path, required=True)
    build_parser.add_argument("--root", type=Path, default=Path.cwd())
    build_parser.set_defaults(func=_dispatch)

    check_parser = commands.add_parser("check", help="Validate a returned decision file")
    check_parser.add_argument("--package", type=Path, required=True)
    check_parser.add_argument("--decision", type=Path, required=True)
    check_parser.add_argument("--root", type=Path, default=Path.cwd())
    check_parser.add_argument("--archive", action="store_true")
    check_parser.set_defaults(func=_dispatch)

    preset_parser = commands.add_parser("preset", help="Print the fixed stage preset")
    preset_parser.add_argument("--stage", required=True)
    preset_parser.set_defaults(func=_dispatch)


def add_cli(subparsers):
    parser = subparsers.add_parser("review", help="Build/check the fixed acceptance sheet")
    commands = parser.add_subparsers(dest="review_action", required=True)
    _add_commands(commands)
    return parser


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="review_action", required=True)
    _add_commands(commands)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
