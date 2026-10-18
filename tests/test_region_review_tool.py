"""Behavior checks for the skill's shared region-review renderer."""
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from PIL import Image

SCRIPT = (Path(__file__).resolve().parents[1] / 'skills' /
          'silicon-eye-region-planning/scripts/build_review.py')
spec = importlib.util.spec_from_file_location('region_review_skill_tool', SCRIPT)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


@pytest.fixture
def sample(tmp_path):
    source = tmp_path / 'data/frame.jpg'
    source.parent.mkdir()
    Image.new('RGB', (100, 80), 'gray').save(source)
    plan = {
        'sources': {'a': {'path': 'data/frame.jpg',
                          'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                          'width': 100, 'height': 80}},
        'regions': [{'region_id': 'r1', 'label': 'R1', 'category': 'UNKNOWN',
                     'status': 'candidate', 'observation': '<untrusted text>',
                     'views': [{'source_layer': 'a', 'bbox_xyxy': [10, 10, 40, 50]}]}],
    }
    path = tmp_path / 'plan.json'
    path.write_text(json.dumps(plan))
    return tmp_path, path, plan


def test_renderer_preserves_state_and_refuses_overwrite(sample):
    root, path, plan = sample
    out = root / 'review'
    before = (root / 'data/frame.jpg').read_bytes()
    result = tool.render(root, path, out)
    assert (out / 'plan.json').read_bytes() == path.read_bytes()
    assert result['physical_classification_verified'] is False
    page = (out / 'index.html').read_text()
    assert '&lt;untrusted text&gt;' in page
    assert '<untrusted text>' not in page
    assert 'candidate' in page and 'native context' in page
    written = (out / 'index.html').read_bytes()
    with pytest.raises(ValueError, match='Output exists'):
        tool.render(root, path, out)
    assert (out / 'index.html').read_bytes() == written
    assert (root / 'data/frame.jpg').read_bytes() == before
    assert plan['regions'][0]['status'] == 'candidate'


@pytest.mark.parametrize('error', ['hash', 'bounds', 'duplicate', 'escape', 'nonfinite'])
def test_invalid_input_publishes_nothing(sample, error):
    root, path, plan = sample
    if error == 'hash':
        plan['sources']['a']['sha256'] = '0' * 64
    elif error == 'bounds':
        plan['regions'][0]['views'][0]['bbox_xyxy'][2] = 101
    elif error == 'duplicate':
        plan['regions'].append(plan['regions'][0])
    elif error == 'escape':
        plan['sources']['a']['path'] = '../outside.jpg'
    else:
        plan['regions'][0]['views'][0]['bbox_xyxy'][0] = float('nan')
    path.write_text(json.dumps(plan))
    out = root / 'invalid-output'
    with pytest.raises(ValueError):
        tool.render(root, path, out)
    assert not out.exists()


def test_output_inside_raw_data_is_rejected(sample):
    root, path, _plan = sample
    out = root / 'data/output'
    with pytest.raises(ValueError, match='immutable data'):
        tool.render(root, path, out)
    assert not out.exists()
