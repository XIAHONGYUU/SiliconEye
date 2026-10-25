"""Build a small, source-bound portfolio from existing Silicon Eye outputs.

Run: .venv/bin/python scripts/build_portfolio.py
Requires project dependencies; first replay device_request into device_bundle.
Regenerates only site/assets and site/provenance.json; never edits evidence/photos.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from portfolio_quality import audit_catalog
from shapely.geometry import Polygon, box

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from silicon_eye.conductive_layers import COLORS, svg_layers  # noqa: E402
from silicon_eye.geometry_reconstruction import digest, object_polygon  # noqa: E402
from silicon_eye.joint_layers import load_snapshot  # noqa: E402
from silicon_eye.layer_review import model_svg, records  # noqa: E402


def read(path):
    return json.loads((ROOT / path).read_text())


def plot(groups, bounds, size):
    """Plot data geometry, preserving polygon holes and clipping to the chosen view."""
    x, y, r, b = bounds
    sx, sy = size[0] / (r - x), size[1] / (b - y)
    image = Image.new("RGBA", size, "#0e1928")
    for color, alpha, polygons in groups:
        overlay = Image.new("RGBA", size)
        draw = ImageDraw.Draw(overlay)
        rgb = tuple(bytes.fromhex(color.lstrip("#")))
        for polygon in polygons:
            if not polygon.intersects(box(*bounds)):
                continue
            draw.polygon(
                [((u - x) * sx, (v - y) * sy) for u, v in polygon.exterior.coords],
                fill=rgb + (alpha,),
            )
            for hole in polygon.interiors:
                draw.polygon(
                    [((u - x) * sx, (v - y) * sy) for u, v in hole.coords], fill=(0, 0, 0, 0)
                )
        image = Image.alpha_composite(image, overlay)
    return image.convert("RGB")


def build():
    config = read("configs/portfolio.json")
    quality = audit_catalog(ROOT)
    output = ROOT / "site/assets"
    output.mkdir(parents=True, exist_ok=True)
    snapshot = load_snapshot(ROOT, ROOT / config["snapshot"])
    material_snapshot = dict(snapshot)
    material_snapshot.pop("conductors", None)
    material = model_svg(material_snapshot, config["material_window"])
    (output / "materials.svg").write_text(material)
    palette = [("AA", "#68dcb0", 180), ("POLY", "#ffb45f", 210), ("CT", "#e4f7ff", 255)]
    groups = [
        (
            color,
            alpha,
            [
                object_polygon(o) if layer == "AA" else Polygon(o["layout_outline"])
                for o in records(snapshot, layer)
            ],
        )
        for layer, color, alpha in palette
    ]
    material_plot = plot(groups, config["material_window"], (800, 680))
    material_plot.save(output / "materials.webp", quality=90)
    source = snapshot["manifest"]["source_photos"]["poly"]["path"]
    with Image.open(ROOT / source) as photo:
        photo.crop(config["material_source_window"]).resize((800, 714)).save(
            output / "source.webp", quality=88
        )
    metal = read(config["metal_model"])
    bounds = config["metal_window"]
    x, y, r, b = bounds
    metal_svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {r - x} {b - y}">'
        '<style>[data-layer="V1"] path{fill-opacity:.65}'
        '[data-layer="V2"] path{fill-opacity:.25}</style>' + svg_layers(metal, bounds) + "</svg>"
    )
    (output / "metals.svg").write_text(metal_svg)
    metal_groups = []
    for layer in ("M1", "M2", "M3", "V1", "V2"):
        polygons = []
        for obj in metal["objects_by_layer"][layer]:
            if obj.get("candidate_cut_bounds"):
                polygons.extend(box(*bb) for bb in obj["candidate_cut_bounds"])
            else:
                polygons.append(Polygon(obj["geometry"]["outer_xy"], obj["geometry"]["holes_xy"]))
        metal_groups.append((COLORS[layer], 115 if layer.startswith("M") else 190, polygons))
    metal_plot = plot(metal_groups, bounds, (650, 665))
    metal_plot.save(output / "metals.webp", quality=90)
    device_path = Path(config["device_bundle"])
    index = read(device_path / "device-index.json")
    for window in index["windows"]:
        x, y, w, h = window["xywh"]
        with Image.open(ROOT / window["photo"]["path"]) as photo:
            photo.crop((x, y, x + w, y + h)).resize((w * 3, h * 3)).save(
                output / ("device-" + window["id"] + ".webp"), quality=92
            )
    schematic = device_path / "circuit/local-schematic.svg"
    shutil.copyfile(ROOT / schematic, output / "schematic.svg")
    font_path = Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
    # A bundled/system font affects the presentation only, never source geometry.
    font = (
        ImageFont.truetype(str(font_path), 26) if font_path.exists() else ImageFont.load_default()
    )
    small = (
        ImageFont.truetype(str(font_path), 18) if font_path.exists() else ImageFont.load_default()
    )
    hero = Image.new("RGB", (1500, 670), "#0c1523")
    draw = ImageDraw.Draw(hero)
    for i, (image, title, subtitle) in enumerate(
        [
            (Image.open(output / "source.webp"), "01  原始逐层照片", "同一颗芯片 · 保留原生坐标"),
            (material_plot, "02  规则材料重建", "AA / POLY / CT · 局部工作层"),
            (metal_plot, "03  跨层连接复核", "M1 → V1 → M2 → V2 → M3"),
        ]
    ):
        left = 28 + i * 494
        thumb = image.copy()
        thumb.thumbnail((458, 495))
        hero.paste(thumb, (left + (458 - thumb.width) // 2, 30 + (495 - thumb.height) // 2))
        draw.text((left, 550), title, fill="#f1f6fd", font=font)
        draw.text((left, 602), subtitle, fill="#9eafc5", font=small)
    hero.save(output / "overview.webp", quality=91)
    data = dict(
        device_index=index,
        material_counts=dict(
            AA=len(snapshot["materials"]["AA_objects"]),
            POLY=len(snapshot["materials"]["objects"]),
            CT=len(snapshot["contacts"]),
        ),
        source_photo_count=len(snapshot["manifest"]["source_photos"]),
        metal_geometry_status="candidate",
        network_complete=False,
    )
    (output / "data.js").write_text(
        "window.SILICON_EYE = "
        + json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        + ";\n"
    )
    (output / "views.js").write_text(
        "window.SE_VIEWS = "
        + json.dumps(dict(materials=material, metals=metal_svg), ensure_ascii=False)
        + ";\n"
    )
    # Preserve old and corrected geometry as distinct, source-bound views.
    correction_bounds = config["quality_case_window"]
    cx, cy, cr, cb = correction_bounds
    for name, ref in [("before", "metal_before"), ("after", "metal_after")]:
        model = read(quality["evidence"][ref]["path"])
        focused = dict(model)
        focused["objects_by_layer"] = {
            layer: objects if layer in {"M1", "V1", "M2"} else []
            for layer, objects in model["objects_by_layer"].items()
        }
        drawing = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{cx} {cy} {cr - cx} {cb - cy}">'
            + svg_layers(focused, correction_bounds)
            + '<g fill="white" font-family="system-ui" font-size="10" text-anchor="middle">'
            '<text x="300" y="235">A</text><text x="370" y="235">B</text></g></svg>'
        )
        (output / f"carrier-{name}.svg").write_text(drawing)
    for frame in ("m1", "m2"):
        with Image.open(ROOT / quality["evidence"][frame + "_photo"]["path"]) as photo:
            photo.thumbnail((1000, 1000))
            photo.convert("RGB").save(output / f"carrier-{frame}.webp", quality=90)
    (ROOT / "site/quality-report.json").write_text(
        json.dumps(quality, ensure_ascii=False, indent=2) + "\n"
    )
    (output / "quality.js").write_text(
        "window.SE_QUALITY = " + json.dumps(quality, ensure_ascii=False) + ";\n"
    )
    sources = [
        config["snapshot"],
        config["metal_model"],
        config["metal_report"],
        str(device_path / "device-index.json"),
        str(schematic),
        config["device_request"],
    ]
    sources += [ref["path"] for ref in snapshot["manifest"]["source_photos"].values()]
    sources += [ref["path"] for ref in snapshot["manifest"]["inputs"].values()]
    sources += [ref["path"] for ref in quality["evidence"].values()]
    sources += ["benchmarks/portfolio-quality-v1/suite.json"]
    manifest = dict(
        snapshot_commit="fa3e1c7",
        sources={p: digest(ROOT / p) for p in sources},
        artifacts={
            str(p.relative_to(ROOT / "site")): digest(p)
            for p in sorted([*output.iterdir(), ROOT / "site/quality-report.json"])
            if p.is_file()
        },
        scope="Curated presentation of one chip; reviewed relations and candidate geometry "
        "remain distinct. No online AI inference or complete netlist claim.",
    )
    (ROOT / "site/provenance.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    )
    print("Portfolio assets:", sum(p.stat().st_size for p in output.iterdir()), "bytes")
    return manifest


if __name__ == "__main__":
    build()
