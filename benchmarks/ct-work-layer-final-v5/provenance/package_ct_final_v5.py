"""Package engineering closeout, whole-frame views and preserved source limitations.
Invocation: PYTHONPATH=. .venv/bin/python /tmp/package_ct_final_v5.py
Audit packaging only; does not modify raw photographs or frozen parent versions.
"""
from pathlib import Path
import copy
import hashlib
import html
import json
import shutil
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

import numpy as np
from PIL import Image,ImageDraw,ImageFont
from shapely.geometry import Polygon,box
from shapely.ops import unary_union

from silicon_eye.ct_transfer import render_case
from silicon_eye.geometry_reconstruction import object_polygon
from silicon_eye.poly_closeout import svg

B=Path('benchmarks/ct-work-layer-final-v5');P=Path('benchmarks/ct-work-layer-reviewed-v4')
A=Path('docs/assets/ct-work-layer-final-v5');R=Path('runs/ct-work-layer-final-v5a')
def rd(p):return json.loads(Path(p).read_text())
def wr(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
assert not (B/'freeze-manifest-v1.json').exists()
A.mkdir(exist_ok=True)
spec=rd(B/'spec-v1.json');mat=rd(R/'material-model.json');model=rd(R/'model.json');objects=model['objects'];report=rd(R/'report.json');access=rd(R/'terminal-access.json')
parent=rd(P/'model-v1.json')['objects'];oldmat=rd(P/'material-model-v1.json')
new=rd(B/'new-contacts-v1.json')['objects'];newids={o['id'] for o in new}
oldids={o['id'] for o in rd(B/'retired-material-records-v1.json')['objects']}
gates=[g for g in mat['objects'] if g['id'].startswith('G06R-P')]
byid={g['id']:g for g in mat['objects']}
assert report['status']=='PASS' and objects[:len(parent)]==parent and objects[len(parent):]==new
assert len(gates)==4 and not (set(byid)&oldids)
assert len(new)==33 and sum(o.get('landing_material')=='POLY' for o in new)==8
assert mat['AA_objects']==oldmat['AA_objects']
assert all(byid[g['id']]==g for g in oldmat['objects'] if g['id'] not in oldids)
assert all(o.get('POLY_target') not in oldids for o in objects)
prior=rd('benchmarks/ct-lower-middle-mos-revision-v2/model-v1.json')['objects']
objbyid={o['id']:o for o in objects};parbyid={o['id']:o for o in parent}
assert all(objbyid[o['id']]==parbyid[o['id']] for o in prior)
AA={a['id']:object_polygon(a) for a in mat['AA_objects']}
for g in gates:
    p=Polygon(g['layout_outline']);assert p.is_valid and p.intersection(AA['AA-F01804']).area>0
    assert not any(p.intersects(Polygon(h['layout_outline'])) for h in mat['objects'] if h['id']!=g['id'])
    assert not any(p.intersects(shape) for k,shape in AA.items() if k!='AA-F01804')
    assert len([o for o in new if o.get('POLY_target')==g['id']])==2
assert len(AA['AA-F01804'].difference(unary_union([Polygon(g['layout_outline']) for g in gates])).geoms)==5
for v in spec['inputs'].values():assert sha(v['path'])==v['sha256']
for v in rd(B/'input-inventory-v1.json')['photos']:assert sha(v['path'])==v['sha256']
for name,h in rd(P/'freeze-manifest-v1.json')['locked_files'].items():assert sha(P/name)==h
alias=mat['local_material_revision']['alias_map']
assert alias['AA2-UPPER-COMPLEX-GUARD-AA-0-split01']=='AA2-UPPER-INNER-B-AA-0'
assert len(access['POLY_materials'])==695
assert {p['material_id'] for p in access['POLY_materials'] if not p['contact_ids']}=={'V3_G1','V3_G2'}
missing=[p for p in access['diffusion_regions'] if not p['contact_ids']]
assert len(missing)==1 and missing[0]['AA_target']=='AA-F01744'
canvas=[0,0,*mat['canvas_wh']]
all_material_geometry=unary_union(list(AA.values())+[Polygon(g['layout_outline']) for g in mat['objects']])
assert box(*canvas).covers(all_material_geometry)
assert all(box(*canvas).covers(Polygon(o['layout_outline'])) for o in objects)
wr(B/'canvas-coverage-check-v1.json',dict(status='PASS',canonical_canvas_wh=mat['canvas_wh'],native_photo_wh=list(Image.open('data/test_chip/tile_full/poly.jpg').size),
                                      display_bounds=canvas,material_bounds=list(all_material_geometry.bounds),all_material_and_CT_covered=True,
                                      photo_size_not_used_as_design_canvas=True))
preserve=dict(status='PASS',all10254_parent_CT_records_exact_equal=True,original7044_records_exact_equal_to_v4=True,
              all334_AA_records_exact_equal=True,unrelated691_POLY_records_exact_equal=True,
              five_old_unaccepted_POLY_retired=sorted(oldids),four_new_POLY=[g['id'] for g in gates],
              new_CT_count=len(new),parent_aliases_retained=alias,raw8photos_unchanged=True,parent_frozen_files_verified=True)
wr(B/'preservation-check-v1.json',preserve)
limits=rd(B/'unknown-sites-v1.json')['unknown_scopes']
exceptions=dict(
    source_limitations=limits,
    historical_fragment_exceptions=[dict(material_id=k,status='historical_reviewed_terminal_representation_preserved_not_new_missing_CT',
                                         evidence_refs=[ref('benchmarks/local-terminal-review-v1.json'),ref('benchmarks/block-case-v1-v3.json')]) for k in ['V3_G1','V3_G2']],
    no_auto_holes_from_pattern=True,no_claim_of_zero_physical_holes_in_unknown_regions=True,
    unresolved_source_limits_remain_open_not_silently_passed=True)
wr(B/'exceptions-v1.json',exceptions)
checklist=dict(status='PASS_engineering_closeout_with_explicit_limits',checks=[
    dict(id='four_gate_joint_match',status='PASS',four_POLY=4,diffusion_columns=5,gate_CT=8,SD_CT=25),
    dict(id='whole_layer_CT_geometry',status='PASS',contacts=10287,overlaps=0,gap_violations=0,minimum_edge_gap_px=report['minimum_edge_gap_px']),
    dict(id='parent_and_prior_human_scope_preservation',status='PASS',evidence=ref(B/'preservation-check-v1.json')),
    dict(id='raw_source_support_and_ownership',status='PASS',new_points=33,source_conflicts_within3px=0),
    dict(id='material_alias_continuation',status='PASS',alias_count=len(alias)),
    dict(id='terminal_access_inventory',status='PASS_with_named_exceptions',diffusion_regions=845,with_candidate_CT=844,
         without_direct_CT=1,remaining_source='AA-F01744 photo-clipped locator',historical_POLY_fragments=2),
    dict(id='source_limited_scopes',status='OPEN_evidence_limits_recorded',count=len(limits),CT_reconstruction_not_claimed_here=True),
    dict(id='physical_PDK_DRC_and_100_percent_recovery',status='NOT_ESTABLISHED',not_required_for_bounded_work_layer_closeout=True),
],mandatory_human_questions_now=[],repeated_global_CT_review_required=False)
wr(B/'acceptance-checklist-v1.json',checklist)
contract=dict(schema_version=1,purpose='CT material-landing geometry work layer for evidence-guided continuation',
              units='relative_pixels',authoritative_model=ref(B/'model-v1.json') if (B/'model-v1.json').exists() else None,
              use_reviewed_source_supported_records=True,confirmed_M1_connectivity=False,confirmed_netlist=False,
              new_geometry_human_pixel_approved=False,physical_all_CT_recovered=False,
              restrictions=[dict(scope_id=x['id'],bounds=x['layout_bounds'],AA_target=x.get('AA_target'),policy=x['tracing_policy']) for x in limits],
              limitation_reopen_triggers=['new photograph','validated local correspondence','requested trace depends on limited material'],
              blanket_automatic_network_export_allowed=False,notes='Contract is metadata for the next workflow; current work does not implement a new network exporter.')
stage=dict(status='WORK_LAYER_V1_CLOSED_WITH_LIMITATIONS',engineering_closeout_complete=True,
           geometry_status='PASS',source_supported_work_layer_ready=True,
           closed_cases=['R1A','R1B','R2','R1B-COUNT'],count_review_basis='AI_raw_photo_recheck_plus_user_authorized_implementation',
           blocking_human_cases=[],requires_user_action_now=False,
           source_limitations_open=[x['id'] for x in limits],whole_frame_complete=False,
           physical_all_CT_recovered=False,overall_human_acceptance=False,
           human_acceptance_scope='prior scoped decisions inherited; user authorized engineering closeout, not a new per-pixel full-layer approval',
           CT_count=10287,AA_count=334,POLY_count=695,physical_PDK_DRC=False,
           physical_limitations_not_relabelled_as_pass=True)
wr(B/'stage-gate-v1.json',stage)
model.update(stage_status=stage['status'],engineering_closeout_complete=True,whole_frame_complete=False,
             unresolved_material_ids=[],source_review_required_for_contact_ids=[],stage_gate_ref=ref(B/'stage-gate-v1.json'),
             source_limitations_ref=ref(B/'exceptions-v1.json'),new_geometry_human_pixel_approved=False)
mat['working_layer_closeout']=dict(stage_status=stage['status'],retired_material_ref=ref(B/'retired-material-records-v1.json'),
                                  current_POLY_count=695,current_AA_count=334,exact_new_geometry='AI_source_checked_not_new_human_pixel_annotation')
report.update(stage_status=stage['status'],engineering_closeout_complete=True,whole_frame_complete=False,
              human_acceptance=False,source_correspondence_status='four_gate_conflict_resolved_by_source_recheck',
              source_limits_remain_open=[x['id'] for x in limits])
for k,v in [('model',model),('material-model',mat),('report',report),('terminal-access',access),('ledger',rd(R/'ledger.json'))]:wr(B/(k+'-v1.json'),v)
contract['authoritative_model']=ref(B/'model-v1.json');wr(B/'use-contract-v1.json',contract)
wr(B/'access-summary-v1.json',dict(diffusion_region_count=845,with_candidate_CT=844,without_direct_CT=missing,
                                  POLY_without_direct_CT=[p for p in access['POLY_materials'] if not p['contact_ids']],
                                  counts_not_device_totals_or_recall=True,CT_to_M1_still_unknown=True))
for k in ['model','material-model','report','terminal-access','ledger','stage-gate','preservation-check','human-review','exceptions','acceptance-checklist','use-contract','access-summary']:
    shutil.copyfile(B/(k+'-v1.json'),A/(k+'.json'))
photo=Image.open('data/test_chip/tile_full/poly.jpg').convert('RGB')
protected=set(parbyid)
cards=''
cases=copy.deepcopy(spec['cases'])
for c in rd('benchmarks/ct-work-layer-closeout-v3/review-windows-v1.json')['cases']:
    if c['id'] in ['O','U','R1A','R1B','R2']:continue
    c=copy.deepcopy(c);c.pop('additional_modes',None);c['scope']='同一最终工作模型的抽查窗口；已审范围继承，不要求逐孔重审。原图与规则几何分别显示。';cases.append(c)
for c in cases:
    if c['id']=='RIGHT4':c['additional_modes']=[['before','svg','修订前五栅（该块无CT）'],['caps','png','宽视野栅端1～4编号']]
    if c['id']=='LIMITS':c['additional_modes']=[['aa','png','AA原图：旧定位诊断框，非已验证配准'],['bandAA','png','AA原图：长条观察上下文']]
    cards+=render_case(c,mat,objects,protected,photo,A)
wr(B/'review-windows-v1.json',dict(cases=cases,all_windows_use_same_full_frame_model=True))
before=svg(oldmat,cases[0]['layout_bbox'])
(A/'RIGHT4-before.svg').write_text(before)
im=photo.crop((3500,110,4120,375)).resize((1240,530));d=ImageDraw.Draw(im);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
for i,(x,y) in enumerate([(3771,187),(3816,190),(3871,192),(3922,195)],1):
    x,y=(x-3500)*2,(y-110)*2;d.rectangle((x-30,y-19,x+30,y+19),outline='#45bfff',width=3);d.text((x-4,y-42),str(i),font=font,fill='#45bfff')
im.save(A/'RIGHT4-caps.png')
Image.open('data/test_chip/tile_full/aa.jpg').crop((1730,180,2120,410)).resize((1170,690)).save(A/'LIMITS-aa.png')
# Mark only the old source locator; the caption explicitly excludes correspondence acceptance.
im=Image.open(A/'LIMITS-aa.png');d=ImageDraw.Draw(im)
for u in limits:
    if 'AA_legacy_locator_native_bounds' not in u:continue
    l,t,r,b=u['AA_legacy_locator_native_bounds'];d.rectangle(((l-1730)*3,(t-180)*3,(r-1730)*3,(b-180)*3),outline='#ffb45b',width=2)
im.save(A/'LIMITS-aa.png')
Image.open('data/test_chip/tile_full/aa.jpg').crop((1300,160,2250,410)).save(A/'LIMITS-bandAA.png')

# One SVG with stable group IDs is the sole whole-canvas layer-switching view.
root=ET.fromstring(svg(mat,canvas));ns='{http://www.w3.org/2000/svg}'
for child in root:
    if child.get('data-layer') in ['AA','POLY']:child.set('id','layer-'+child.get('data-layer'))
ctg=ET.SubElement(root,ns+'g',{'id':'layer-CT'})
for o in objects:
    e=ET.SubElement(ctg,ns+'polygon',{'points':' '.join(f'{x},{y}' for x,y in o['layout_outline']),
                                   'fill':'#ed8eff' if o.get('landing_material')=='POLY' else '#65baff'})
    ET.SubElement(e,ns+'title').text=o['id']
ug=ET.SubElement(root,ns+'g',{'id':'layer-UNKNOWN'})
for u in limits:
    l,t,r,b=u['layout_bounds'];e=ET.SubElement(ug,ns+'rect',{'x':str(l),'y':str(t),'width':str(r-l),'height':str(b-t),
        'stroke':'#ffb45b','fill':'none','stroke-width':'4','stroke-dasharray':'10 7'});ET.SubElement(e,ns+'title').text=u['id']
whole=ET.tostring(root,encoding='unicode').replace('ns0:','').replace(':ns0','')
(A/'O-layers.svg').write_text(whole)
whole=whole.replace('<svg ','<svg id="whole-layout" ',1)
controls=' '.join(f'<label><input type="checkbox" checked onchange="document.getElementById(\'layer-{k}\').style.display=this.checked?\'\':\'none\'">{k}</label>' for k in ['AA','POLY','CT','UNKNOWN'])

def preview(key,bounds):
    l,t,r,b=bounds;s=min(3,2200/(r-l));im=Image.new('RGB',(round((r-l)*s),round((b-t)*s)),'#111c28');d=ImageDraw.Draw(im)
    def pts(v):return [((x-l)*s,(y-t)*s) for x,y in v]
    geom=unary_union(list(AA.values())).intersection(box(l,t,r,b));parts=list(geom.geoms) if hasattr(geom,'geoms') else [geom]
    for p in sorted([p for p in parts if p.geom_type=='Polygon' and not p.is_empty],key=lambda p:Polygon(p.exterior).area,reverse=True):
        d.polygon(pts(p.exterior.coords),fill='#315548',outline='#86b5a5')
        for h in p.interiors:d.polygon(pts(h.coords),fill='#111c28')
    for p in mat['objects']:
        if Polygon(p['layout_outline']).intersects(box(l,t,r,b)):d.polygon(pts(p['layout_outline']),fill='#9a739d')
    for o in objects:
        if Polygon(o['layout_outline']).intersects(box(l,t,r,b)):d.polygon(pts(o['layout_outline']),fill='#ed8eff' if o.get('POLY_target') else '#65baff')
    for u in limits:
        ul,ut,ur,ub=u['layout_bounds']
        if box(ul,ut,ur,ub).intersects(box(l,t,r,b)):d.rectangle(((ul-l)*s,(ut-t)*s,(ur-l)*s,(ub-t)*s),outline='#ffb45b',width=2)
    im.save(A/f'{key}-preview.png')
preview('O',canvas)
for c in cases:preview(c['id'],c['layout_bbox'])
labels={'U-AA-F01951':'上沿小AA候选1','U-AA-F01952':'上沿小AA候选2','U-H1':'上沿H1长条','U-H2':'上沿H2长条','L-CLIPPED-AA-F01744':'照片外／边界器件片段'}
limitrows=''.join(f'<tr><td>{labels[u["id"]]}</td><td>{html.escape(u["AA_target"])}</td><td>未恢复CT；保留未知，触及此范围的连接须另核</td></tr>' for u in limits)
summary=f'''<!doctype html><html lang="zh"><meta charset="utf-8"><title>CT工作层v1工程收口</title><style>
body{{max-width:1500px;margin:24px auto;background:#111c28;color:#eee;font:17px sans-serif}}section{{border:1px solid #567;padding:16px;margin:20px 0}}a{{color:#65baff}}img{{width:100%;max-height:90vh;object-fit:contain}}select{{padding:10px}}label{{margin:12px}}#whole-layout{{width:100%;height:auto}}.done{{border:2px solid #86b5a5}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #567;padding:10px}}.limit{{color:#ffb45b}}</style>
<h1>CT工作层v1：三项工作已完成工程收口</h1><section class="done"><p><b>右上四栅已修订并补CT；受限范围已复查建档；整层技术验收通过。</b></p>
<p>当前10287条CT、334个AA、695个POLY对象。四栅局部新增8个栅CT和25个源漏CT；原10254条CT和全部AA完整保留，只替换五条旧AI栅模板为四条有原图依据的栅。原7044条已审记录不改。材料别名接续修复并通过回归测试。</p>
<p>工程收口允许继续使用这份有来源、有未知范围的工作层；<b>不代表照片中的物理孔100%恢复，也不是新增的整层人工逐像素批准或真实PDK DRC。</b>本轮不再索要重复四栅裁决或逐孔审批。</p>
<p><a href="stage-gate.json">收口状态</a> · <a href="acceptance-checklist.json">整层验收表</a> · <a href="preservation-check.json">前后保护</a> · <a href="exceptions.json">受限范围</a> · <a href="use-contract.json">后续使用边界</a> · <a href="human-review.json">用户授权与判断边界</a></p></section>
<section id="full"><h2>同一全幅模型：AA／POLY／CT／未知范围开关</h2><p>{controls}</p>{whole}<p><a href="O-layers.svg">单独打开可缩放SVG</a> · <a href="O-preview.png">全幅PNG</a></p></section>
<section><h2 class="limit">仍不能可靠恢复的范围，完整保留</h2><table><tr><th>范围</th><th>材料编号</th><th>处理</th></tr>{limitrows}</table>
<p>小AA的旧全局定位不能独立证明原图对应，长条上的连续亮带与拍屏纹理不能当成逐孔证据；M1连续也不能证明介质中有孔。照片外片段不虚构补全。这些证据限制仍开放，不以“已处理”写成“孔已确认”。将来有新照片、可靠局部对应或走线需要经过此处时再打开。</p>
<p>845个几何扩散区中844个具候选CT，剩一个为照片边界片段；V3_G1／G2是保留历史端子关系的主体片段。该盘点不是器件数量、漏检率或M1连接确认。</p></section>'''
(A/'index.html').write_text(summary+cards+'</html>')
provenance=B/'provenance';provenance.mkdir(exist_ok=True)
for name in ['prepare_ct_final_v5.py','package_ct_final_v5.py']:shutil.copyfile('/tmp/'+name,provenance/name)
(provenance/'README.md').write_text('本目录为工程收口的审计配方，非新增生产案例脚本或CT skill。通用ct_transfer使用spec生成几何，再由审计包装补充阶段状态和使用边界；不得原地重跑冻结目录。物理100%恢复和整层人工像素批准均未声明。\n')
class Resources(HTMLParser):
    def __init__(self):super().__init__();self.paths=[];self.ids=[];self.selects=[];self.inputs=[];self.current=None
    def handle_starttag(self,t,attrs):
        d=dict(attrs)
        if 'id' in d:self.ids.append(d['id'])
        if t=='select':self.current=dict(code=d['onchange'],options=[]);self.selects.append(self.current)
        if t=='option' and self.current is not None:self.current['options'].append(d['value'])
        if t=='input' and d.get('type')=='checkbox':self.inputs.append(d['onchange'])
        for key in ['src','href','value']:
            val=d.get(key,'')
            if val and not val.startswith(('#','http','javascript:')) and '.' in val:self.paths.append(val)
    def handle_endtag(self,t):
        if t=='select':self.current=None
parser=Resources();parser.feed((A/'index.html').read_text());assert len(parser.ids)==len(set(parser.ids))
for path in parser.paths:assert (A/path.split('#')[0]).exists(),path
for p in A.glob('*.svg'):ET.parse(p)
for p in A.glob('*.png'):
    with Image.open(p) as im:im.verify()
counts={k:len(root.find(".//*[@id='layer-"+k+"']")) for k in ['AA','POLY','CT','UNKNOWN']}
assert counts==dict(AA=334,POLY=695,CT=10287,UNKNOWN=5),counts
ui=dict(status='PASS_static_resources',references=len(parser.paths),selectors=len(parser.selects),layer_counts=counts,browser_render_not_automatically_tested=True)
wr(B/'ui-check-v1.json',ui)
Path('/tmp/ct-v5-ui.json').write_text(json.dumps(dict(ids=parser.ids,selects=parser.selects,inputs=parser.inputs)))
print(json.dumps(dict(status=stage['status'],CT=len(objects),parent_CT_exact=len(parent),limitations=len(limits),review_windows=len(cases),UI=ui),ensure_ascii=False))
