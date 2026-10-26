"""QA geometry sheets; run with --output NEW_DIR in the project environment.
Reuses the existing polygon plotter and the versioned snapshot view configuration.
This does not test browser interaction or identify photo pixels.
"""

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import Polygon, box

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "scripts"))
from build_portfolio import plot  # noqa: E402

parser = argparse.ArgumentParser(
    description="Static comparisons via the existing polygon plotter; no browser or photo editing."
)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--request", type=Path,
                    default=root / "configs/conductive-work-baseline-v1.json")
parser.add_argument("--layers", nargs="+", choices=["M1", "M2", "M3", "V1", "V2"],
                    default=["M1", "M2", "M3", "V1", "V2"])
parser.add_argument("--focus", help="Optional focus ID; omit to draw all domains")
args = parser.parse_args()
config = json.loads(args.request.read_text())
out = args.output
if out.exists():
    raise ValueError("Output must be a new directory")
out.mkdir(parents=True)
font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 27)
small = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 20)
colors = {"M1": "#80e6b0", "M2": "#6ad8ff", "M3": "#d28cff", "V1": "#ffb04f", "V2": "#fff4bd"}
for d in config["domains"]:
    if args.focus and d["focus"]["id"] != args.focus:
        continue
    models = []
    for ref in [d["comparison_parent"], d["package"]]:
        models.append(json.loads((root / Path(ref["path"]).parent / "model.json").read_text()))
    canvas = Image.new("RGB", (1540, 1530), "#101a27")
    draw = ImageDraw.Draw(canvas)
    title = d["focus"]["id"] + " · " + d["focus"]["label"] + "：反馈前 / 当前候选"
    draw.text((25, 20), title, font=font, fill="white")
    for row, bounds in enumerate([d["focus"]["viewbox"], d["focus"]["zoom_viewbox"]]):
        x, y, w, h = bounds
        scale = min(700 / w, 620 / h)
        size = (int(w * scale), int(h * scale))
        for column, model in enumerate(models):
            groups = []
            for layer in ["M1", "M2", "M3", "V1", "V2"]:
                if layer not in args.layers:
                    continue
                polys = []
                for obj in model["objects_by_layer"][layer]:
                    if obj.get("candidate_cut_bounds"):
                        polys.extend(box(*bb) for bb in obj["candidate_cut_bounds"])
                    else:
                        polys.append(
                            Polygon(obj["geometry"]["outer_xy"], obj["geometry"]["holes_xy"])
                        )
                groups.append(
                    (
                        colors[layer],
                        90 if layer.startswith("M") else (180 if layer == "V1" else 80),
                        polys,
                    )
                )
            image = plot(groups, [x, y, x + w, y + h], size)
            origin = (25 + column * 770 + (700 - size[0]) // 2, 105 + row * 690)
            canvas.paste(image, origin)
            overlay = ImageDraw.Draw(canvas)
            for layer in ["V1", "V2"]:
                if layer not in args.layers:
                    continue
                for obj in model["objects_by_layer"][layer]:
                    for a, b, c, e in obj.get("candidate_cut_bounds", []):
                        if x <= a < c <= x + w and y <= b < e <= y + h:
                            overlay.rectangle(
                                [
                                    origin[0] + (a - x) * scale,
                                    origin[1] + (b - y) * scale,
                                    origin[0] + (c - x) * scale,
                                    origin[1] + (e - y) * scale,
                                ],
                                outline=colors[layer],
                                width=2,
                            )
                            cx = origin[0] + ((a+c)/2-x)*scale
                            cy = origin[1] + ((b+e)/2-y)*scale
                            overlay.line((cx-4, cy, cx+4, cy), fill="white", width=1)
                            overlay.line((cx, cy-4, cx, cy+4), fill="white", width=1)
            draw.text(
                (25 + column * 770, 70 + row * 690),
                ("反馈前" if column == 0 else "当前候选")
                + (" · 上下文" if row == 0 else " · 完整孔组放大"),
                font=small,
                fill="#c9d8e8",
            )
    draw.text(
        (25, 1470),
        "设计相对坐标；不是照片投影。连接已审，具体新几何待复核。",
        font=small,
        fill="#ffcf95",
    )
    canvas.save(out / (d["focus"]["id"] + "-comparison.png"))
print("Static geometry sheets rendered")
