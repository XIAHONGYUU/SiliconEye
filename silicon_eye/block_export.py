"""Export one resolved block state; no case names or review interpretation here."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from .block_review import resolve_block, verify_sources
from .local_schematic import Canvas
from .schemas.block_case import BlockCase


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def render_block(state: dict, out: Path) -> None:
    c = Canvas(max(1250, len(state["devices"]) * 430), 760)
    c.text(f"{state['case_id']} / RESOLVED BLOCK REVIEW", (25, 15), size=27)
    c.text(
        "Same label = reviewed same net only. Distinct labels do not prove isolation.",
        (25, 57),
        size=19,
    )
    c.text(
        "Green: reviewed relation/mapping. Amber: unknown. No physical W/L or model implied.",
        (25, 87),
        size=18,
    )
    palette = {"confirmed": "#63e7b2", "unknown": "#ffcb6b"}
    for i, d in enumerate(state["devices"]):
        left, cx, cy = i * 430, i * 430 + 225, 315
        c.text(d["id"], (left + 100, 144), size=23)
        if d["existence"] is not True:
            existence = "unreviewed" if d["existence"] is None else str(d["existence"])
            c.text(f"Existence: {existence}", (left + 18, 613), "#ffcb6b", 18)
        for a, b in [(cy - 37, cy - 17), (cy - 10, cy + 10), (cy + 17, cy + 37)]:
            c.line((cx, a), (cx, b), "#edf3fa", width=4)
        c.line((cx - 25, cy - 40), (cx - 25, cy + 40), "#edf3fa")
        c.line((cx - 55, cy), (cx - 25, cy), "#edf3fa")
        for label, point in [
            ("G", (cx - 48, cy + 9)),
            ("A", (cx + 12, cy - 70)),
            ("B", (cx + 12, cy + 62)),
        ]:
            c.text(label, point, size=17)
        terminals = {t["role"]: t for t in state["terminals"] if t["device_id"] == d["id"]}
        for role, a, b, point in [
            ("G", (left + 25, cy), (cx - 55, cy), (left + 24, cy - 28)),
            ("A", (cx, cy - 37), (cx, 220), (cx - 65, 190)),
            ("B", (cx, cy + 37), (cx, 435), (cx - 65, 444)),
            ("Bulk", (cx + 2, cy), (cx + 125, cy), (cx + 10, cy + 18)),
        ]:
            t = terminals[role]
            color = palette[t["render_status"]]
            c.line(a, b, color, t["render_status"] != "confirmed")
            text = (
                t["display_label"]
                if t["confirmed_net_id"] or t["conductor_ids"]
                else (f"{role} ? ({t['display_label']})")
            )
            c.text(text, point, color, 16)
        c.text(
            "A/B: unoriented diffusion; Bulk separate unless reviewed.", (left + 12, 512), size=13
        )
        ms = [m for m in state["measurements"] if m["entity_id"] == d["id"]]
        if ms:
            m = ms[0]
            c.text(
                f"Visible support {m['span']:g} px / run {m['run_median']:g} px",
                (left + 18, 550),
                size=16,
            )
            c.text(
                f"Window clipped: {m['window_clipped']}; not physical W/L",
                (left + 18, 580),
                "#ffcb6b",
                15,
            )
    c.text(
        f"Mode: {state['mode']}; structure draft only; simulation_ready=false",
        (25, 650),
        "#ffcb6b",
        18,
    )
    c.text("state_id: " + state["state_id"], (25, 703), size=14)
    c.save(out)


def export_state(state: dict, out: Path) -> None:
    write_json(out / "resolved-state.json", state)
    report = [
        "# 局部器件组统一复核状态",
        "",
        f"state_id: `{state['state_id']}`",
        "",
        f"案例：{state['case_id']}；修订：{state['case_revision']}；模式：{state['mode']}；"
        f"结果：{state['status']}。",
        "",
        "本输出只消费同一份ResolvedBlock。来源核验不代表物理连接已全部验收；"
        "不同分量/标签不证明隔离，no_evidence保持未知。",
        "",
    ]
    if state["conflicts"]:
        report += [
            "存在冲突：不导出电路图或连接表作为正常结果。",
            "",
            "```json",
            json.dumps(state["conflicts"], ensure_ascii=False, indent=2),
            "```",
        ]
    else:
        render_block(state, out)
        fields = [
            "state_id",
            "id",
            "device_id",
            "role",
            "confirmed_net_id",
            "display_label",
            "mapping_status",
            "conductor_ids",
        ]
        with (out / "terminals.csv").open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            for t in state["terminals"]:
                writer.writerow(
                    dict(
                        state_id=state["state_id"],
                        **{
                            k: ";".join(v) if isinstance(v, list) else v
                            for k, v in t.items()
                            if k in fields
                        },
                    )
                )
        with (out / "connection-matrix.csv").open("w", newline="") as f:
            writer = csv.writer(f, lineterminator="\n")
            writer.writerow(["state_id", "terminal"] + state["matrix"]["terminals"])
            for t, row in zip(state["matrix"]["terminals"], state["matrix"]["values"], strict=True):
                writer.writerow([state["state_id"], t] + row)
        report += [
            "![统一状态原理图](local-schematic.png)",
            "",
            "[SVG](local-schematic.svg) · [端子表](terminals.csv) · "
            "[同网矩阵](connection-matrix.csv)",
            "",
            "| 端子 | 展示名 | 确认同网分量 | 金属对应 |",
            "| --- | --- | --- | --- |",
        ]
        for t in state["terminals"]:
            report.append(
                f"| {t['id']} | {t['display_label']} | "
                f"{t['confirmed_net_id'] or '未分配同网'} | "
                f"{', '.join(t['conductor_ids']) or '未知'} |"
            )
    report += [
        "",
        "## 逐命题裁决状态",
        "",
        "| 命题 | 类型/范围 | 状态 | 当前事件 |",
        "| --- | --- | --- | --- |",
    ]
    for claim in state["claims"]:
        report.append(
            f"| {claim['id']} | {claim['predicate']}={claim['value']} / {claim['scope_id']} | "
            f"{claim['status']} ({', '.join(claim['reasons'])}) | "
            f"{', '.join(claim['active_event_ids'])} |"
        )
    report += [
        "",
        "完整局部拓扑、四端和仿真验收均未自动通过。"
        "新复核必须登记到当前案例清单；本入口不扫描其他目录寻找“最新”文件。",
    ]
    (out / "report.md").write_text("\n".join(report) + "\n")


def run_block(case_path: str, output: str, root: str = ".") -> dict:
    """Validate before writing; failed sources never fall back to older state."""
    out = Path(output)
    if out.exists():
        raise ValueError("Output directory already exists")
    case_file = Path(case_path)
    input_bytes = case_file.read_bytes()
    case = BlockCase.model_validate_json(input_bytes)
    verify_sources(case, Path(root))
    state = resolve_block(case, evidence_checked=True)
    out.mkdir(parents=True)
    export_state(state, out)
    write_json(
        out / "manifest.json",
        dict(
            state_id=state["state_id"],
            sources_verified=True,
            input_file_sha256=hashlib.sha256(input_bytes).hexdigest(),
            registered_inventory_digest=state["inventory_digest"],
            resolver_sha256=hashlib.sha256(
                Path(__file__).with_name("block_review.py").read_bytes()
            ).hexdigest(),
            schema_sha256=hashlib.sha256(
                Path(__file__).parent.joinpath("schemas/block_case.py").read_bytes()
            ).hexdigest(),
            canvas_helper_sha256=hashlib.sha256(
                Path(__file__).with_name("local_schematic.py").read_bytes()
            ).hexdigest(),
            exporter_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            outputs={
                p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir())
            },
            physical_truth_verified_by_script=False,
            runtime_ai_used=False,
            status=state["status"],
        ),
    )
    return state
