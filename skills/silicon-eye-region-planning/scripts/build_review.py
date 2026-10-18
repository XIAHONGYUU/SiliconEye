"""Validate native region records and render an offline, switchable review page.

Usage: python build_review.py --root REPO --plan PLAN.json --output NEW_DIRECTORY
Requires Pillow. Reads AI/human records; does not recognize or approve materials.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import html
import io
import json
import math
import os
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

COLORS = {
    'MOS': '#4de18b', 'CAP': '#69c8ff', 'RES': '#ffbf55',
    'INTERCONNECT': '#c69cff', 'DUMMY': '#d4d998',
    'SUBSTRATE_RING': '#ff829c', 'EXCLUDED_UI': '#d5dce3', 'UNKNOWN': '#ff829c',
}


def inside(root, relative):
    path = (root / relative).resolve()
    if Path(relative).is_absolute() or not path.is_relative_to(root):
        raise ValueError('Input path escapes repository')
    return path


def bbox(box, size):
    if not isinstance(box, list) or len(box) != 4:
        raise ValueError('bbox_xyxy requires four numbers')
    if any(isinstance(x, bool) or not isinstance(x, (int, float))
           or not math.isfinite(x) for x in box):
        raise ValueError('Non-finite or non-numeric coordinates')
    a, b, c, d = box
    if not (0 <= a < c <= size[0] and 0 <= b < d <= size[1]):
        raise ValueError('Region outside native image')
    return box


def data_url(image):
    stream = io.BytesIO()
    image.save(stream, format='JPEG', quality=92)
    return 'data:image/jpeg;base64,' + base64.b64encode(stream.getvalue()).decode()


def render(root, plan_path, output):
    root = Path(root).resolve()
    output = Path(output).absolute()
    if output.exists() or output.is_symlink():
        raise ValueError('Output exists; choose a new directory')
    if output.resolve().is_relative_to(root / 'data'):
        raise ValueError('Output may not be inside immutable data/')
    payload = Path(plan_path).read_bytes()
    plan = json.loads(payload)
    sources, regions = plan['sources'], plan['regions']
    if not sources or not regions:
        raise ValueError('Empty sources or regions')
    images = {}
    for layer, source in sources.items():
        path = inside(root, source['path'])
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != source['sha256']:
            raise ValueError('Source hash mismatch: ' + layer)
        with Image.open(io.BytesIO(raw)) as im:
            im.load()
            if (source.get('width', im.width), source.get('height', im.height)) != im.size:
                raise ValueError('Source size mismatch: ' + layer)
            images[layer] = im.convert('RGB')
    ids = set()
    for region in regions:
        if region['region_id'] in ids:
            raise ValueError('Duplicate region ID')
        ids.add(region['region_id'])
        if not region.get('status'):
            raise ValueError('Missing review status')
        for view in region['views']:
            layer = view['source_layer']
            if layer not in images:
                raise ValueError('View references missing frame')
            bbox(view['bbox_xyxy'], images[layer].size)
    # All source and geometry checks precede output publication.
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.region-review-', dir=output.parent) as temp:
        stage = Path(temp)
        panels, options = [], []
        for number, (layer, image) in enumerate(images.items()):
            preview = image.copy()
            preview.thumbnail((1600,1200))
            draw = ImageDraw.Draw(preview)
            sx, sy = preview.width / image.width, preview.height / image.height
            details = []
            for region in regions:
                for view in region['views']:
                    if view['source_layer'] != layer:
                        continue
                    a, b, c, d = view['bbox_xyxy']
                    color = COLORS.get(region['category'], '#ff829c')
                    draw.rectangle((a*sx, b*sy, c*sx, d*sy), outline=color, width=3)
                    label = region.get('label', region['region_id'])
                    draw.text((a*sx+4, b*sy+4), label, fill=color,
                              stroke_width=1, stroke_fill='#000000')
                    # Context includes neighboring structures; not a registered projection.
                    px, py = max(250, (c-a)*0.7), max(200, (d-b)*0.7)
                    window = (max(0, int(a-px)), max(0, int(b-py)),
                              min(image.width, math.ceil(c+px)),
                              min(image.height, math.ceil(d+py)))
                    crop = image.crop(window)
                    crop.thumbnail((1600,1000))
                    details.append('<h3>' + html.escape(label) + ' — native context '
                                   + html.escape(str(window)) + '</h3><img src="'
                                   + data_url(crop) + '" alt="unregistered wide source context">')
            options.append(f'<option value="p{number}">{html.escape(layer)}</option>')
            original = os.path.relpath(inside(root, sources[layer]['path']), output)
            panels.append(f'<section id="p{number}" class="frame"'
                          + ('' if number == 0 else ' hidden') + '><h2>'
                          + html.escape(layer) + '</h2><a href="'
                          + html.escape(original, quote=True)
                          + '" target="_blank">Open original photo</a><h3>Full native frame</h3>'
                          + '<img src="' + data_url(preview) + '" alt="native overview">'
                          + ''.join(details) + '</section>')
        rows = []
        for region in regions:
            fields = [region['region_id'], region['category'], region['status'],
                      region.get('title', ''), region.get('observation', ''),
                      region.get('alternative_explanations'), region.get('next_check', '')]
            rows.append('<tr>' + ''.join('<td>' + html.escape(str(v or '')) + '</td>'
                                        for v in fields) + '</tr>')
        page = ('<!doctype html><html lang="zh-CN"><meta charset="utf-8">'
                '<title>Regional planning review</title><style>'
                'body{font:18px/1.6 sans-serif;background:#14202b;color:#eef3f7;'
                'margin:24px}img{max-width:100%;height:auto}a{color:#70d6ff}'
                'select{font:inherit;padding:8px}table{border-collapse:collapse;'
                'width:100%}td,th{border:1px solid #678;padding:8px;vertical-align:top}'
                '</style><h1>区域规划：独立原生视图</h1><p>保持输入的候选/人审状态；'
                '切层不代表精确配准。宽局部图保留空间上下文。</p><select id="layer">'
                + ''.join(options) + '</select>' + ''.join(panels)
                + '<h2>区域清单</h2><table><tr><th>ID</th><th>Category</th>'
                '<th>Status</th><th>Title</th><th>Evidence</th><th>Alternatives</th>'
                '<th>Next check</th></tr>' + ''.join(rows) + '</table><script>'
                'document.querySelector("#layer").onchange=function(){'
                'document.querySelectorAll(".frame").forEach(p=>p.hidden=p.id!==this.value)'
                '};</script></html>')
        (stage / 'index.html').write_text(page)
        (stage / 'plan.json').write_bytes(payload)
        result = {
            'kind': 'region_review_render_validation',
            'plan_sha256': hashlib.sha256(payload).hexdigest(),
            'renderer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'source_frames': len(images), 'region_count': len(regions),
            'native_windows': sum(len(i['views']) for i in regions),
            'physical_classification_verified': False,
            'browser_interaction_tested': False,
            'outputs': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in sorted(stage.iterdir())},
        }
        (stage / 'validation.json').write_text(json.dumps(result, indent=2) + '\n')
        if output.exists():
            raise ValueError('Output appeared while rendering')
        stage.rename(output)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--plan', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    try:
        result = render(args.root, args.plan, args.output)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, 'Region review failed: ' + str(error) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
