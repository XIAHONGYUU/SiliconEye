"""A leftward viewport must not move old design sites or weaken extension gates."""
import copy
import json
import tempfile
from pathlib import Path

import pytest

from silicon_eye.conductive_workflow import page, prepare
from silicon_eye.geometry_reconstruction import digest
from silicon_eye.metal_reconstruction import geometry_audit

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'benchmarks/BR-R-return-work-v3/next-request.json'


def read(path):
    return json.loads(path.read_text())


def write(folder, name, value):
    path = folder / name
    path.write_text(json.dumps(value))
    return dict(path=str(path.relative_to(ROOT)), sha256=digest(path))


def left_request(folder):
    request = copy.deepcopy(read(BASE))
    sample = read(ROOT / request['sample']['path'])
    sample.update(canvas_wh=[2280, 1440], canvas_bounds=[-1500, 0, 780, 1440])
    request['sample'] = write(folder, 'sample.json', sample)
    evidence = dict(kind='conductive_canvas_extension', actor='AI', reason='New left source',
                    parent=request['parent'], from_canvas_wh=[780, 1440],
                    to_canvas_wh=sample['canvas_wh'], from_canvas_bounds=[0, 0, 780, 1440],
                    to_canvas_bounds=sample['canvas_bounds'], direction='LEFT_ONLY',
                    origin_xy=[0, 0], scale_xy=[1, 1], translation_xy=[0, 0],
                    geometry_human_approved=False)
    request['canvas_extension_evidence'] = write(folder, 'evidence.json', evidence)
    return request, sample, evidence


def test_left_viewport_preserves_records_and_renders_signed_design_coordinates():
    with tempfile.TemporaryDirectory(dir=ROOT / 'runs') as temporary:
        folder = Path(temporary)
        request, *_ = left_request(folder)
        model, report, sample, *_ = prepare(ROOT, request)
        old = read(ROOT / 'docs/assets/BR-R-return-work-v3/work/model.json')
        for key in ('objects_by_layer', 'candidate_interfaces', 'reviewed_local_connections',
                    'review_sources', 'review_decisions'):
            assert model[key] == old[key]
        assert model['canvas_bounds'] == [-1500, 0, 780, 1440]
        assert len(model['canvas_extension_history']) == 2
        assert report['audits']['canvas_extension']['status'] == 'LEFT_ONLY_CANVAS_EXTENSION_PASS'
        assert not model['geometry_adopted'] and not model['net_edges']
        document = page(model, report, sample, request, folder, ROOT)
        assert 'viewBox="-1500 0 2280 1440"' in document


@pytest.mark.parametrize('mutation', ['undeclared', 'wrong_bounds', 'translation',
                                    'mixed_geometry', 'top_shift', 'fractional', 'root'])
def test_left_extension_rejects_unauthorized_coordinate_changes(mutation):
    with tempfile.TemporaryDirectory(dir=ROOT / 'runs') as temporary:
        folder = Path(temporary)
        request, sample, evidence = left_request(folder)
        if mutation == 'undeclared':
            request.pop('canvas_extension_evidence')
        elif mutation == 'wrong_bounds':
            evidence['to_canvas_bounds'][0] = -1499
        elif mutation == 'translation':
            evidence['translation_xy'] = [1500, 0]
        elif mutation == 'mixed_geometry':
            sample['features_by_layer']['M1'][0]['design_path'][0][0] += 1
        elif mutation == 'top_shift':
            sample['canvas_bounds'] = [-1500, -1, 780, 1439]
            evidence['to_canvas_bounds'] = sample['canvas_bounds']
        elif mutation == 'fractional':
            sample['canvas_bounds'][0] = -1500.5
            sample['canvas_wh'][0] = 2280.5
            evidence['to_canvas_bounds'] = sample['canvas_bounds']
            evidence['to_canvas_wh'] = sample['canvas_wh']
        else:
            request.pop('parent')
        request['sample'] = write(folder, 'sample.json', sample)
        if 'canvas_extension_evidence' in request:
            request['canvas_extension_evidence'] = write(folder, 'evidence.json', evidence)
        with pytest.raises(ValueError):
            prepare(ROOT, request)


def test_negative_geometry_requires_a_matching_explicit_viewport():
    feature = dict(id='negative', design_path=[[-40, 20], [-20, 20]], design_width=6)
    budget = dict(minimum_width_px=3, minimum_gap_px=3)
    assert geometry_audit([feature], budget, [100, 100])[0]['status'] == 'FAIL'
    assert geometry_audit([feature], budget, [150, 100], [-50, 0, 100, 100])[0][
        'status'] == 'PASS'
    with pytest.raises(ValueError, match='canvas bounds'):
        geometry_audit([feature], budget, [100, 100], [-50, 0, 100, 100])
