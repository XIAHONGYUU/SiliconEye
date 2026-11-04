"""Behavior checks for the fixed acceptance sheet and its archive contract."""

import copy
import hashlib
import json
import re
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from silicon_eye.review_sheet import DecisionError, build, check


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def image(path, color=(20, 40, 70)):
    path.parent.mkdir(parents=True, exist_ok=True)
    picture = Image.new("RGB", (96, 64), color)
    draw = ImageDraw.Draw(picture)
    draw.rectangle((12, 12, 74, 30), fill=(190, 220, 245))
    picture.save(path)


def make_spec(root, stage="METAL", items=None):
    image(root / "assets" / "wide.png")
    image(root / "assets" / "detail.png", (40, 70, 100))
    if items is None:
        items = [
            {
                "id": "M2-S01",
                "type": "metal_fragment",
                "title": "M2 主干",
                "prompt": "该片段几何是否合理？",
                "facts": {"来源帧": "m2", "原生路径": [[1, 2], [3, 4]]},
                "evidence": [
                    {
                        "path": "assets/wide.png",
                        "label": "M2 宽图",
                        "role": "source",
                    }
                ],
            },
            {
                "id": "M2-V01",
                "type": "via_interface",
                "title": "W3-U",
                "prompt": "该孔组身份与承载是否正确？",
                "facts": {"孔层": "V2"},
                "evidence": [
                    {
                        "path": "assets/detail.png",
                        "label": "M2 放大图",
                        "role": "detail",
                    }
                ],
            },
        ]
    return {
        "schema_version": 1,
        "kind": "silicon_eye_review_sheet",
        "stage": stage,
        "package_id": "TEST-" + stage,
        "title": "固定确认单测试",
        "date": "2026-11-03",
        "summary": "测试用确认单",
        "scope": {"frame": "m2", "native_bounds": [0, 0, 100, 100], "note": "测试范围"},
        "items": items,
    }


def write_spec(root, document):
    path = root / "review-spec.json"
    path.write_text(json.dumps(document, ensure_ascii=False))
    return path


def build_pkg(root):
    spec_path = write_spec(root, make_spec(root))
    output = root / "package"
    summary = build(root, spec_path, output)
    manifest = json.loads((output / "manifest.json").read_text())
    spec = json.loads((output / "review-spec.json").read_text())
    return summary, output, manifest, spec


def make_decision(root, output, manifest, spec, **overrides):
    decision = {
        "schema_version": 1,
        "kind": "silicon_eye_review_decision",
        "package_id": spec["package_id"],
        "build_id": manifest["build_id"],
        "stage": spec["stage"],
        "actor": "human",
        "date": "2026-11-03",
        "statement": "测试通过",
        "limits_acknowledged": True,
        "answers": [
            {
                "item_id": item["id"],
                "verdict": "accepted",
                "checks": {check["id"]: True for check in item["checks"]},
                "notes": "",
            }
            for item in spec["items"]
        ],
        "questions": [
            {"question_id": question["id"], "verdict": "accepted", "notes": ""}
            for question in spec["questions"]
        ],
    }
    decision.update(overrides)
    path = root / "decision.json"
    path.write_text(json.dumps(decision, ensure_ascii=False))
    return path, decision


def test_builds_fixed_package_and_binds_hashes(tmp_path):
    summary, output, manifest, spec = build_pkg(tmp_path)

    assert summary["status"] == "BUILT"
    assert {path.name for path in output.iterdir()} == {
        "assets",
        "index.html",
        "manifest.json",
        "review-spec.json",
    }
    assert manifest["kind"] == "silicon_eye_review_sheet_manifest"
    assert manifest["page_sha256"] == digest(output / "index.html")
    assert manifest["spec_sha256"] == digest(output / "review-spec.json")
    assert {asset["source_sha256"] for asset in manifest["assets"]} == {
        digest(tmp_path / "assets" / "wide.png"),
        digest(tmp_path / "assets" / "detail.png"),
    }
    for asset in manifest["assets"]:
        assert (output / asset["output_path"]).is_file()
        assert asset["output_sha256"] == digest(output / asset["output_path"])

    # METAL preset fills Q1/Q2 for fragments and Q3 only because a via item exists.
    assert [question["id"] for question in spec["questions"]] == ["Q1", "Q2", "Q3"]
    assert spec["items"][0]["checks"][0]["id"] == "endpoints_correct"
    assert spec["items"][1]["checks"][0]["id"] == "via_present"

    payload = re.search(
        r'<script id="payload" type="application/json">(.*?)</script>',
        (output / "index.html").read_text(),
        re.S,
    )
    assert payload
    page = json.loads(payload.group(1))
    assert page["build"]["build_id"] == manifest["build_id"]
    assert page["spec"]["items"][0]["evidence"][0]["url"].startswith("assets/")
    assert "__PAYLOAD__" not in (output / "index.html").read_text()


def test_template_keeps_fixed_sections_and_escapes_payload(tmp_path):
    template = (
        Path(__file__).parents[1] / "silicon_eye" / "review_sheet.html"
    ).read_text()
    assert template.count("__PAYLOAD__") == 1
    for label in ["总览", "逐项确认", "整体问题", "边界与未批准", "导出"]:
        assert label in template

    document = make_spec(tmp_path)
    document["title"] = "</script><script>alert(1)</script>"
    build(tmp_path, write_spec(tmp_path, document), tmp_path / "package")
    page = (tmp_path / "package" / "index.html").read_text()
    assert "</script><script>alert(1)</script>" not in page
    payload = re.search(
        r'<script id="payload" type="application/json">(.*?)</script>', page, re.S
    )
    assert payload
    assert json.loads(payload.group(1))["spec"]["title"] == document["title"]


def test_build_refuses_existing_output_and_outside_evidence(tmp_path):
    spec_path = write_spec(tmp_path, make_spec(tmp_path))
    (tmp_path / "package").mkdir()
    with pytest.raises(ValueError, match="new directory"):
        build(tmp_path, spec_path, tmp_path / "package")

    document = make_spec(tmp_path)
    document["items"][0]["evidence"][0]["path"] = "../outside.png"
    with pytest.raises(ValueError, match="outside root"):
        build(tmp_path, write_spec(tmp_path, document), tmp_path / "outside")


def test_build_rejects_duplicate_and_unknown_question_items(tmp_path):
    document = make_spec(tmp_path)
    document["items"].append(copy.deepcopy(document["items"][0]))
    with pytest.raises(ValueError, match="Duplicate item id"):
        build(tmp_path, write_spec(tmp_path, document), tmp_path / "package")

    document = make_spec(tmp_path)
    document["questions"] = [
        {"id": "Q1", "prompt": "覆盖不存在项？", "item_ids": ["MISSING"]}
    ]
    with pytest.raises(ValueError, match="unknown items"):
        build(tmp_path, write_spec(tmp_path, document), tmp_path / "package-2")


def test_complete_decision_is_archived_idempotently(tmp_path):
    _, output, manifest, spec = build_pkg(tmp_path)
    decision_path, _ = make_decision(tmp_path, output, manifest, spec)

    summary = check(tmp_path, output, decision_path, archive=True)
    assert summary["status"] == "VALID"
    assert summary["answers"] == 2
    assert summary["verdicts"] == {"accepted": 2}
    assert summary["questions"] == {"accepted": 3}
    assert (output / "review-decision.json").is_file()
    record = (output / "review-record.md").read_text()
    assert "# 验收确认记录" in record
    assert "M2 主干（M2-S01）" in record
    assert "照片精确投影或跨帧配准" in record
    saved = json.loads((output / "review-decision.json").read_text())
    assert saved["sources"]["submitted_page"]["sha256"] == manifest["page_sha256"]

    again = check(tmp_path, output, decision_path, archive=True)
    assert again["status"] == "VALID"


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda d: d["answers"].pop(0), "Required item is unanswered"),
        (
            lambda d: d["answers"][0]["checks"].update({"endpoints_correct": False}),
            "unchecked required checks",
        ),
        (
            lambda d: d["answers"][0].update(
                {"verdict": "needs_revision", "checks": {"endpoints_correct": False}}
            ),
            "requires a note for verdict needs_revision",
        ),
        (lambda d: d.update({"limits_acknowledged": False}), "explicitly acknowledged"),
        (lambda d: d.update({"build_id": "wrong"}), "not made against this package build"),
        (lambda d: d["answers"].append(copy.deepcopy(d["answers"][0])), "Duplicate answer"),
        (lambda d: d["answers"][0].update({"item_id": "UNKNOWN"}), "Unknown item id"),
        (lambda d: d["answers"][0]["checks"].update({"bogus": True}), "unknown checks"),
        (lambda d: d["answers"][0].update({"verdict": "maybe"}), "invalid verdict"),
        (lambda d: d["questions"].pop(0), "Required question is unanswered"),
        (lambda d: d.update({"actor": "AI"}), "actor must be human"),
    ],
)
def test_invalid_decisions_are_rejected(tmp_path, mutate, message):
    _, output, manifest, spec = build_pkg(tmp_path)
    decision_path, decision = make_decision(tmp_path, output, manifest, spec)
    mutate(decision)
    decision_path.write_text(json.dumps(decision, ensure_ascii=False))
    with pytest.raises(DecisionError, match=message):
        check(tmp_path, output, decision_path)


def test_accepted_question_cannot_hide_a_blocked_item(tmp_path):
    _, output, manifest, spec = build_pkg(tmp_path)
    decision_path, decision = make_decision(tmp_path, output, manifest, spec)
    decision["answers"][0].update(
        {"verdict": "needs_revision", "notes": "主干下段需要核对"}
    )
    decision_path.write_text(json.dumps(decision, ensure_ascii=False))
    with pytest.raises(DecisionError, match="cannot be accepted while covered items"):
        check(tmp_path, output, decision_path)


def test_page_tamper_is_rejected(tmp_path):
    _, output, manifest, spec = build_pkg(tmp_path)
    decision_path, _ = make_decision(tmp_path, output, manifest, spec)
    page = output / "index.html"
    page.write_text(page.read_text() + "\n")
    with pytest.raises(ValueError, match="page hash changed"):
        check(tmp_path, output, decision_path)


def test_archive_refuses_a_different_existing_record(tmp_path):
    _, output, manifest, spec = build_pkg(tmp_path)
    decision_path, _ = make_decision(tmp_path, output, manifest, spec)
    (output / "review-decision.json").write_text("{}\n")
    with pytest.raises(ValueError, match="refusing to overwrite"):
        check(tmp_path, output, decision_path, archive=True)


@pytest.mark.parametrize(
    ("stage", "item_type", "question_ids", "check_id"),
    [
        ("AA", "aa_polygon", ["Q1", "Q2"], "shape_reasonable"),
        ("POLY", "poly_fragment", ["Q1", "Q2"], "routing_reasonable"),
        ("CT", "ct_array", ["Q1", "Q2"], "array_regular"),
        ("REGION", "region_boundary", ["Q1", "Q2"], "covers_visible"),
        ("VIA", "via_interface", ["Q1", "Q2"], "via_present"),
    ],
)
def test_stage_presets_fill_fixed_questions(tmp_path, stage, item_type, question_ids, check_id):
    document = make_spec(tmp_path, stage=stage)
    document["items"] = [
        {
            "id": "ITEM-1",
            "type": item_type,
            "title": item_type,
            "prompt": "该结构是否合理？",
        }
    ]
    build(
        tmp_path,
        write_spec(tmp_path, document),
        tmp_path / ("package-" + stage),
    )
    spec = json.loads(
        (tmp_path / ("package-" + stage) / "review-spec.json").read_text()
    )
    assert [question["id"] for question in spec["questions"]] == question_ids
    assert spec["items"][0]["checks"][0]["id"] == check_id


def test_metal_fragment_only_drops_interface_question(tmp_path):
    document = make_spec(tmp_path)
    document["items"] = [
        {
            "id": "M1-S01",
            "type": "metal_fragment",
            "title": "M1 片段",
            "prompt": "几何是否合理？",
        }
    ]
    build(tmp_path, write_spec(tmp_path, document), tmp_path / "package")
    spec = json.loads((tmp_path / "package" / "review-spec.json").read_text())
    assert [question["id"] for question in spec["questions"]] == ["Q1", "Q2"]


def test_context_is_read_only_and_excluded_from_questions(tmp_path):
    document = make_spec(tmp_path)
    document['items'][1]['review_mode'] = 'context'
    document['items'][0]['change_summary'] = 'Only this extent is revised'
    output = tmp_path / 'package'
    build(tmp_path, write_spec(tmp_path, document), output)
    manifest = json.loads((output / 'manifest.json').read_text())
    spec = json.loads((output / 'review-spec.json').read_text())
    context = spec['items'][1]
    assert context['required'] is False and context['checks'] == []
    assert all(context['id'] not in q['item_ids'] for q in spec['questions'])
    assert [q['id'] for q in spec['questions']] == ['Q1', 'Q2']
    decision_path, decision = make_decision(tmp_path, output, manifest, spec)
    with pytest.raises(DecisionError, match='Context item cannot receive'):
        check(tmp_path, output, decision_path)
    decision['answers'] = [a for a in decision['answers'] if a['item_id'] != context['id']]
    decision_path.write_text(json.dumps(decision))
    assert check(tmp_path, output, decision_path)['answers'] == 1


@pytest.mark.parametrize('explicit_question', [False, True])
def test_context_cannot_be_required_or_reapproved_in_a_question(tmp_path, explicit_question):
    document = make_spec(tmp_path)
    item = document['items'][0]
    item['review_mode'] = 'context'
    if explicit_question:
        document['questions'] = [{'id': 'Q1', 'prompt': 'Review?', 'item_ids': [item['id']]}]
        message = 'cannot re-review context'
    else:
        item['required'] = True
        message = 'Context cannot require'
    with pytest.raises(ValueError, match=message):
        build(tmp_path, write_spec(tmp_path, document), tmp_path / 'package')


def test_overall_acceptance_cannot_hide_unanswered_optional_item(tmp_path):
    document = make_spec(tmp_path)
    document['items'][0]['required'] = False
    output = tmp_path / 'package'
    build(tmp_path, write_spec(tmp_path, document), output)
    manifest = json.loads((output / 'manifest.json').read_text())
    spec = json.loads((output / 'review-spec.json').read_text())
    decision_path, decision = make_decision(tmp_path, output, manifest, spec)
    decision['answers'].pop(0)
    decision_path.write_text(json.dumps(decision))
    with pytest.raises(DecisionError, match='unanswered covered'):
        check(tmp_path, output, decision_path)


def test_all_not_applicable_cannot_become_overall_accepted(tmp_path):
    _, output, manifest, spec = build_pkg(tmp_path)
    decision_path, decision = make_decision(tmp_path, output, manifest, spec)
    for answer in decision['answers']:
        answer.update(verdict='not_applicable', notes='Outside the declared decision scope')
    decision_path.write_text(json.dumps(decision))
    with pytest.raises(DecisionError, match='no applicable accepted items'):
        check(tmp_path, output, decision_path)


def test_frame_and_independent_paired_evidence_are_preserved(tmp_path):
    document = make_spec(tmp_path)
    document['items'][0]['evidence'][0].update(frame='m1 / m2', role='paired')
    output = tmp_path / 'package'
    build(tmp_path, write_spec(tmp_path, document), output)
    page = (output / 'index.html').read_text()
    payload = json.loads(re.search(r'type="application/json">(.*?)</script>', page, re.S)[1])
    assert payload['spec']['items'][0]['evidence'][0]['frame'] == 'm1 / m2'
    assert payload['labels']['roles']['paired'] == '分层并列（独立坐标）'


def test_demo_v2_context_uses_v2_source_not_v1_north_images():
    root = Path(__file__).parents[1]
    demo = json.loads((root / 'configs/review-sheet-demo-m2.json').read_text())
    via_items = [item for item in demo['items'] if item['type'] == 'via_interface']
    assert len(via_items) == 2
    for item in via_items:
        assert item['review_mode'] == 'context'
        assert all('-N-' not in e['path'] for e in item['evidence'])
        assert any(e['frame'] == 'm2' and e['role'] == 'source' for e in item['evidence'])
        assert any(e['frame'] == 'm3' for e in item['evidence'])


def test_draft_reader_restores_exact_state_and_rejects_cross_build_or_unknown_ids(tmp_path):
    # Exercise the pure JavaScript draft parser without launching or mocking a browser.
    import shutil
    import subprocess

    node = shutil.which('node')
    if not node:
        pytest.skip('Node is optional; browser validation covers the interactive draft flow')
    document = make_spec(tmp_path)
    document['items'][1]['review_mode'] = 'context'
    output = tmp_path / 'package'
    build(tmp_path, write_spec(tmp_path, document), output)
    page = (output / 'index.html').read_text()
    payload = json.loads(re.search(r'type="application/json">(.*?)</script>', page, re.S)[1])
    start = page.index('  function readDraft(document){')
    end = page.index('  function toast(', start)
    js = r'''
const vm=require('node:vm'), assert=require('node:assert/strict');
const payload=PAYLOAD;
const context={SPEC:payload.spec,BUILD:payload.build,LABELS:payload.labels,
  isContext:item=>item.review_mode==='context'};
vm.createContext(context); vm.runInContext(SOURCE,context);
const spec=payload.spec, build=payload.build;
const answers=Object.fromEntries(spec.items.map(item=>[item.id,{verdict:null,
  checks:Object.fromEntries(item.checks.map(c=>[c.id,false])),notes:''}]));
const draft={schema_version:1,kind:'silicon_eye_review_draft',build_id:build.build_id,
  package_id:spec.package_id,stage:spec.stage,spec_sha256:build.spec_sha256,
  state:{answers,questions:Object.fromEntries(spec.questions.map(q=>[q.id,{verdict:null,notes:''}])),statement:'partial',limitsAck:false}};
const clean=context.readDraft(draft);
assert.equal(JSON.stringify(clean),JSON.stringify(draft.state));
assert.equal(clean.answers[spec.items[0].id].checks.endpoints_correct,false);
const clone=()=>JSON.parse(JSON.stringify(draft));
let bad=clone();bad.build_id='old';assert.throws(()=>context.readDraft(bad),/送审版本/);
bad=clone();bad.spec_sha256='changed';assert.throws(()=>context.readDraft(bad),/送审版本/);
bad=clone();bad.state.answers.UNKNOWN={};assert.throws(()=>context.readDraft(bad),/未知编号/);
bad=clone();bad.state.answers[spec.items[1].id].verdict='accepted';assert.throws(()=>context.readDraft(bad),/新裁决/);
bad=clone();bad.state.answers[spec.items[0].id].checks.endpoints_correct='true';assert.throws(()=>context.readDraft(bad),/布尔值/);
bad=clone();bad.state.answers[spec.items[0].id].verdict='maybe';assert.throws(()=>context.readDraft(bad),/非法结论/);
console.log('draft parser: exact restore plus six invalid inputs rejected');
'''.replace('PAYLOAD', json.dumps(payload)).replace('SOURCE', json.dumps(page[start:end]))
    result = subprocess.run([node], input=js, text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
