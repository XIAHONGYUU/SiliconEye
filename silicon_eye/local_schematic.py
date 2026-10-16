"""Render a partial MOS schematic as standalone SVG and PNG, without EDA software.

Same net labels denote joins; explicit unresolved relations are not proven opens.
Source/drain direction, bulk and NMOS/PMOS remain unspecified.
"""

from __future__ import annotations

import math
from html import escape
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


class Canvas:
    def __init__(self, width, height):
        self.image = Image.new('RGB', (width, height), '#101b2b')
        self.draw = ImageDraw.Draw(self.image)
        self.parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
                      f'height="{height}" viewBox="0 0 {width} {height}">',
                      '<rect width="100%" height="100%" fill="#101b2b"/>']
        self.font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

    def line(self, a, b, color, dashed=False, width=3):
        dash = ' stroke-dasharray="7 5"' if dashed else ''
        self.parts.append(f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" '
                          f'stroke="{color}" stroke-width="{width}"{dash}/>')
        if dashed:
            length = math.dist(a, b)
            for start in range(0, int(length), 12):
                end = min(start+7, length)
                p = tuple(a[i]+(b[i]-a[i])*start/length for i in [0, 1])
                q = tuple(a[i]+(b[i]-a[i])*end/length for i in [0, 1])
                self.draw.line([p, q], fill=color, width=width)
        else:
            self.draw.line([a, b], fill=color, width=width)

    def text(self, value, point, color='#edf3fa', size=18):
        self.parts.append(f'<text x="{point[0]}" y="{point[1]+size}" '
                          f'font-family="DejaVu Sans, sans-serif" font-size="{size}" '
                          f'fill="{color}">{escape(value)}</text>')
        font = (ImageFont.truetype(self.font_path, size) if Path(self.font_path).exists()
                else ImageFont.load_default(size=size))
        self.draw.text(point, value, fill=color, font=font)

    def save(self, output):
        (output / 'local-schematic.svg').write_text('\n'.join(self.parts+['</svg>'])+'\n')
        self.image.save(output / 'local-schematic.png')


def render_schematic(output: Path, devices: list, dimensions: dict,
                     unresolved_relations=None) -> None:
    canvas = Canvas(max(1200, len(devices)*400), 650)
    canvas.text('LOCAL MOS CIRCUIT - PARTIAL TOPOLOGY', (28, 16), size=27)
    canvas.text('Same net label = connected. Green: reviewed relation; blue dashed: candidate.',
                (28, 58), size=18)
    canvas.text('A/B are unoriented diffusion terminals. Generic MOS symbol: N/P and bulk unknown.',
                (28, 88), size=18)
    reviewed = {'N3_G', 'N3_M', 'N3_GM'}
    for index, device in enumerate(devices):
        left = index*400
        cx, cy = left+220, 300
        canvas.text(device['id'], (left+110, 133), size=25)
        white, green, blue, amber = '#edf3fa', '#63e7b2', '#70b8ff', '#ffcb6b'
        # Three channel segments, insulated gate, fourth bulk stub; no polarity arrow.
        for a, b in [(cy-37, cy-17), (cy-10, cy+10), (cy+17, cy+37)]:
            canvas.line((cx, a), (cx, b), white, width=4)
        canvas.line((cx-25, cy-40), (cx-25, cy+40), white)
        canvas.line((cx-55, cy), (cx-25, cy), white)
        for field, yend, label in [('diffusion_A', 200, 'A'), ('diffusion_B', 410, 'B')]:
            color = green if device[field] in reviewed else blue
            start_y = cy-37 if label == 'A' else cy+37
            canvas.line((cx, start_y), (cx, yend), color, device[field] not in reviewed)
            canvas.line((cx-12, yend), (cx+12, yend), color)
            canvas.text(label, (cx+12, (start_y+yend)//2-8), size=17)
            canvas.text(device[field], (cx-65, yend-28 if label == 'A' else yend+5), color, 20)
        color = green if device['G'] in reviewed else blue
        canvas.line((left+25, cy), (cx-55, cy), color, device['G'] not in reviewed)
        canvas.text(device['G'], (left+24, cy-29), color, 20)
        canvas.text('G', (cx-48, cy+8), size=17)
        canvas.line((cx+2, cy), (cx+110, cy), amber, True)
        canvas.text('Bulk ?', (cx+30, cy-28), amber, 17)
        d = dimensions.get(device['id'], {})
        canvas.text('N/P ?   S/D orientation ?', (left+45, 471), amber, 16)
        canvas.text(f"Image span {d.get('W_span_px', '?')} px / run "
                    f"{d.get('L_run_median_px', '?')} px", (left+30, 500), size=16)
    if unresolved_relations is None or unresolved_relations:
        canvas.text('UNRESOLVED: N3_G <-> N3_M. Separate labels here do NOT prove isolation.',
                    (28, 551), '#ffcb6b', 22)
    else:
        canvas.text('REVIEWED: common gate and shared diffusion connected as N3_GM.',
                    (28, 551), '#63e7b2', 22)
    canvas.text('No simulator model or physical W/L implied. Rendered from reviewed topology JSON.',
                (28, 594), size=18)
    canvas.save(output)
