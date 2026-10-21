"""Render the R1/R2 scoped revision and a single remaining material-count question.
Run from repo after ct_transfer. Audit packaging only; production input is spec-v1.json.
"""
from pathlib import Path
import copy
import hashlib
import json
import shutil
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from silicon_eye.ct_transfer import render_case
from silicon_eye.geometry_reconstruction import object_polygon
from silicon_eye.poly_closeout import svg

B=Path('benchmarks/ct-work-layer-reviewed-v4')
P=Path('benchmarks/ct-work-layer-closeout-v3')
A=Path('docs/assets/ct-work-layer-reviewed-v4')
R=Path('runs/ct-work-layer-reviewed-v4b')
def rd(p): return json.loads(Path(p).read_text())
def wr(p,x): Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p): return dict(path=str(p),sha256=sha(p))
assert not (B/'freeze-manifest-v1.json').exists()
A.mkdir(exist_ok=True)
spec=rd(B/'spec-v1.json')
for v in spec['inputs'].values(): assert sha(v['path'])==v['sha256']
for n,h in rd(P/'freeze-manifest-v1.json')['locked_files'].items():
    assert sha(P/n)==h,(n,'parent changed')
mat=rd(R/'material-model.json');model=rd(R/'model.json');objects=model['objects'];report=rd(R/'report.json');access=rd(R/'terminal-access.json')
before=rd(P/'model-v1.json')['objects'];before_by={o['id']:o for o in before};after_by={o['id']:o for o in objects}
changes={c['id']:c for c in spec['contact_changes']};source_ids={c['id'] for c in spec['source_correspondence_corrections']}
added_ids=set(after_by)-set(before_by);retired_ids=set(before_by)-set(after_by)
assert report['status']=='PASS'
for k in set(before_by)&set(after_by):
    if k in changes: assert after_by[k]==changes[k]['after']
    elif k in source_ids:
        q=copy.deepcopy(after_by[k]);h=q['source_correspondence_history'];q['source_evidence']=h[-1]['before'];q['source_correspondence_history']=h[:-1]
        if not q['source_correspondence_history']: del q['source_correspondence_history']
        assert q==before_by[k]
    else: assert after_by[k]==before_by[k]
prior=rd('benchmarks/ct-lower-middle-mos-revision-v2/model-v1.json')['objects']
assert all(after_by[o['id']]==before_by[o['id']] for o in prior)
parent_mat=rd(P/'material-model-v1.json')
assert mat['objects']==parent_mat['objects']
merge=rd(B/'material-merge-v1.json');active=merge['surviving_id'];retired_mat=merge['retired_id']
oldaa={o['id']:o for o in parent_mat['AA_objects']};newaa={o['id']:o for o in mat['AA_objects']}
assert set(oldaa)-set(newaa)=={retired_mat}
assert all(o==newaa[k] for k,o in oldaa.items() if k not in [active,retired_mat])
patch=object_polygon(newaa[active]).difference(unary_union([object_polygon(oldaa[active]),object_polygon(oldaa[retired_mat])]))
assert not any(patch.intersects(object_polygon(v)) for k,v in oldaa.items() if k not in [active,retired_mat])
shared=[o for o in objects if o['family'] in ['UP-RING-BOTTOM','R2-SHARED-RAIL-EXTENSION']]
phase=min(o['layout_center'][0] for o in shared)
assert len({round(o['layout_center'][1],8) for o in shared})==1
assert all(abs((o['layout_center'][0]-phase)/13-round((o['layout_center'][0]-phase)/13))<1e-6 for o in shared)
for g in ['G01','G02','G05']:
    gs=[p for p in mat['objects'] if p.get('group_id')==g]
    for p in gs:
        ct=[o for o in objects if o.get('POLY_target')==p['id']]
        assert len(ct)==2
        assert all(o['layout_center'][1]<Polygon(p['layout_outline']).centroid.y for o in ct)
changed_sources=added_ids|source_ids
conflicts=[]
for i,j in cKDTree([o['source_evidence']['native_center'] for o in objects]).query_pairs(3):
    x,y=objects[i],objects[j]
    if {x['id'],y['id']}&changed_sources and x.get('AA_target',x.get('POLY_target'))!=y.get('AA_target',y.get('POLY_target')):
        conflicts.append([x['id'],y['id']])
assert not conflicts,conflicts
preservation=dict(status='PASS',prior7044_records_exact_equal_to_v3=True,all696_POLY_records_exact_equal=True,
                  unaffected333_AA_records_exact_equal=True,unchanged_parent_contacts=report['unchanged_parent_contacts'],
                  retired_unaccepted_contacts=sorted(retired_ids),new_candidate_contacts=sorted(added_ids),
                  material_host_changes=[k for k,v in changes.items() if v['after'] is not None],
                  source_only_corrected_ids=sorted(source_ids),R2_single_row_contacts=len(shared),R2_single_row_pitch_px=13,
                  R2_AA_patch_does_not_touch_other_active_materials=True,source_conflicts_within3px=conflicts,
                  previous_Q1_Q2_Q3_decisions_preserved=True,parent_frozen_files_verified=True)
wr(B/'preservation-check-v1.json',preservation)
stage=dict(status='HOLD_R1B_material_count_and_overall_acceptance',geometry_status='PASS',
           closed_human_cases=['R1A','R1B','R2'],closed_scope='terminal side, SD regularity and R2 AA continuity / one CT row',
           blocking_human_cases=['R1B-COUNT'],unresolved_material_ids=[f'G06-P{i:02}' for i in range(6,11)],
           CT_count=len(objects),AA_count=len(mat['AA_objects']),POLY_count=len(mat['objects']),
           whole_frame_complete=False,overall_human_acceptance=False,physical_PDK_DRC=False,
           frozen_kind='review_candidate_not_accepted_work_layer',
           no_synthetic_CT_on_unmatched_POLY=True,raw_photos_unchanged=True)
wr(B/'stage-gate-v1.json',stage)
model.update(stage_status=stage['status'],whole_frame_complete=False,source_review_required_for_contact_ids=[],
             unresolved_material_ids=stage['unresolved_material_ids'],stage_gate_ref=ref(B/'stage-gate-v1.json'))
report.update(stage_status=stage['status'],whole_frame_complete=False,human_acceptance=False,
              source_correspondence_status='R1_R2_directions_closed_R1B_material_count_open')
for k,v in [('model',model),('material-model',mat),('report',report),('terminal-access',access),('ledger',rd(R/'ledger.json'))]:wr(B/(k+'-v1.json'),v)
shutil.copytree(R,A,dirs_exist_ok=True)
for name in ['O-raw.png','O-source.png']:
    (A/name).unlink(missing_ok=True)  # Unlinked full-photo derivatives stay in the run.
for k in ['model','material-model','report','terminal-access','ledger','stage-gate','preservation-check','review-questions','human-review','material-merge','optical-observations','source-ownership-check']:
    shutil.copyfile(B/(k+'-v1.json'),A/(k+'.json'))

photo=Image.open('data/test_chip/tile_full/poly.jpg').convert('RGB')
protected={k for k in before_by if k not in changes}
cases=spec['cases']
cards=''.join(render_case(c,mat,objects,protected,photo,A) for c in cases if c['id']!='O')
count_case=dict(id='COUNT',title='唯一新增核对：右上末段的POLY数量',source_bbox=[3500,110,4120,375],layout_bbox=[3700,410,4000,565],
                scope='原图目前可分辨4组上端栅亮条、5列源漏CT；旧规则模型为5条POLY。引出方向已确认，这里只核对数量，不要求逐孔复核。',
                additional_modes=[['caps','png','原图：4组栅端编号'],['context','png','宽视野无标记原图'],['alternative','svg','4条替代方案（未进入工作模型）'],['inset','png','较大窗口放大原图']])
cards=render_case(count_case,mat,objects,protected,photo,A)+cards
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
bb=count_case['source_bbox'];im=photo.crop(bb).resize((1240,530));draw=ImageDraw.Draw(im)
for i,(x,y) in enumerate([(3771,187),(3816,190),(3871,192),(3922,195)],1):
    sx,sy=(x-bb[0])*2,(y-bb[1])*2
    draw.rectangle([sx-30,sy-19,sx+30,sy+19],outline='#45bfff',width=3)
    draw.text((sx-5,sy-44),str(i),font=font,fill='#45bfff')
draw.text((20,10),'Confirmed: upper gate terminals. Count to check: 4 caps vs 5 old POLY.',font=font,fill='#45bfff')
im.save(A/'COUNT-caps.png')
photo.crop(bb).resize((1240,530)).save(A/'COUNT-context.png')
photo.crop((3670,140,4000,350)).resize((1320,840)).save(A/'COUNT-inset.png')
alternative=copy.deepcopy(mat)
alternative['objects']=[p for p in alternative['objects'] if p['id'] not in stage['unresolved_material_ids']]
for i,cx in enumerate(np.linspace(3770,3931,4),1):
    alternative['objects'].append(dict(id=f'COUNT-ALT-{i:02}',kind='MOS_gate',layout_outline=[[cx-16,431],[cx+16,431],[cx+16,546],[cx-16,546]],acceptance=dict(joint_geometry='candidate_only_not_in_work_layer')))
(A/'COUNT-alternative.svg').write_text(svg(alternative,count_case['layout_bbox']))
cards=cards.replace('<img id="COUNT" src="COUNT-layout.svg"','<img id="COUNT" src="COUNT-caps.png"')
cards=cards.replace('<option value="COUNT-caps.png">','<option value="COUNT-caps.png" selected>')

# Native-photo observations are annotated in their own frame; no canonical overlay is
# projected back through an unvalidated transform.
for c in cases:
    if c['id']=='O':continue
    key=c['id'];l,t,r,b=c['source_bbox'];im=photo.crop((l,t,r,b));d=ImageDraw.Draw(im)
    if key in ['R1A','R1B']:
        groups=['G01','G02'] if key=='R1A' else ['G05','G06']
        for o in objects:
            if o.get('POLY_target','').split('-')[0] not in groups:continue
            x,y=o['source_evidence']['native_center'];x-=l;y-=t
            if 0<=x<im.width and 0<=y<im.height:d.ellipse((x-3,y-3,x+3,y+3),outline='#ed8eff',width=1)
        if key=='R1B':d.rectangle((3720-l,155-t,3960-l,300-t),outline='#ffb45b',width=2)
        im.save(A/f'{key}-terminals.png')
        cards=cards.replace(f'<option value="{key}-raw.png">',f'<option value="{key}-terminals.png">上端栅CT重新定位</option><option value="{key}-before.svg">修订前联合图</option><option value="{key}-raw.png">')
    (A/f'{key}-before.svg').write_text(svg(parent_mat,c['layout_bbox']).replace('</svg>',''.join(
        '<polygon points="'+' '.join(f'{x},{y}' for x,y in o['layout_outline'])+'" fill="#829ca6"/>' for o in before
    )+'</svg>'))
    if key=='R2':
        cards=cards.replace('<option value="R2-raw.png">','<option value="R2-before.svg">修订前：两条相邻AA</option><option value="R2-aa.png">AA原图独立坐标参考</option><option value="R2-raw.png">')
        Image.open('data/test_chip/tile_full/aa.jpg').crop((700,850,1750,1300)).save(A/'R2-aa.png')

aa_shapes=[object_polygon(o) for o in mat['AA_objects']]
whole=svg(mat,[0,0,5712,4284])
# Existing svg renderer emits AA paths then per-POLY polygons. Assign explicit layers
# structurally, so all four switchable layers retain a common native design canvas.
root=ET.fromstring(whole)
ns='{http://www.w3.org/2000/svg}'
for child in list(root):
    if child.tag==ns+'g' and child.get('data-layer') in ['AA','POLY']:
        child.set('id','layer-'+child.get('data-layer'))
assert len(root.find(".//*[@id='layer-AA']"))==len(mat['AA_objects'])
assert len(root.find(".//*[@id='layer-POLY']"))==len(mat['objects'])
ct_group=ET.SubElement(root,ns+'g',{'id':'layer-CT'})
for o in objects:
    ET.SubElement(ct_group,ns+'polygon',{'points':' '.join(f'{x},{y}' for x,y in o['layout_outline']),
                                      'fill':'#ed8eff' if o.get('POLY_target') else '#65baff'})
unknown_group=ET.SubElement(root,ns+'g',{'id':'layer-UNKNOWN'})
for u in rd(B/'unknown-sites-v1.json')['unknown_scopes']:
    l,t,r,b=u['layout_bounds'];ET.SubElement(unknown_group,ns+'rect',{'x':str(l),'y':str(t),'width':str(r-l),'height':str(b-t),'fill':'none','stroke':'#ffb45b','stroke-width':'3','stroke-dasharray':'8 5'})
whole=ET.tostring(root,encoding='unicode').replace('ns0:','').replace(':ns0','')
(A/'O-layers.svg').write_text(whole)
controls=' '.join(f'<label><input type="checkbox" checked onchange="document.getElementById(\'layer-{k}\').style.display=this.checked?\'\':\'none\'">{k}</label>' for k in ['AA','POLY','CT','UNKNOWN'])
whole=whole.replace('<svg ','<svg id="whole-layout" ',1)
# Raster previews facilitate visual QA without a browser or an invented projection.
for c in cases+[count_case]:
    key=c['id'];l,t,r,b=c['layout_bbox'];scale=min(3,2200/(r-l));im=Image.new('RGB',(round((r-l)*scale),round((b-t)*scale)),'#111c28');d=ImageDraw.Draw(im)
    def pts(v):return [((x-l)*scale,(y-t)*scale) for x,y in v]
    g=unary_union(aa_shapes).intersection(box(l,t,r,b));parts=list(g.geoms) if hasattr(g,'geoms') else [g]
    for p in sorted([p for p in parts if p.geom_type=='Polygon' and not p.is_empty],key=lambda p:Polygon(p.exterior).area,reverse=True):
        d.polygon(pts(p.exterior.coords),fill='#315548',outline='#86b5a5')
        for h in p.interiors:d.polygon(pts(h.coords),fill='#111c28')
    for p in mat['objects']:
        if Polygon(p['layout_outline']).intersects(box(l,t,r,b)):d.polygon(pts(p['layout_outline']),fill='#9a739d')
    for o in objects:
        if Polygon(o['layout_outline']).intersects(box(l,t,r,b)):d.polygon(pts(o['layout_outline']),fill='#ed8eff' if o.get('POLY_target') else '#65baff')
    im.save(A/f'{key}-preview.png')
header=f'''<!doctype html><html lang="zh"><meta charset="utf-8"><title>CT裁决落地与局部数量核对</title>
<style>body{{max-width:1500px;margin:24px auto;background:#111c28;color:#eee;font:17px sans-serif}}section{{border:1px solid #567;padding:16px;margin:20px 0}}img{{width:100%;max-height:90vh;object-fit:contain}}a{{color:#65baff}}select{{padding:10px}}#whole-layout{{width:100%;height:auto}}.hold{{border:2px solid #ffb45b}}label{{margin:12px}}</style>
<h1>R1A／R1B／R2裁决已记录并局部修订</h1><p>R1A／R1B栅CT只从上端引出；源漏按共同排列重新测量。R2为连续AA、一排CT，撤回此前AI拆成两条隔离环的解释，仅修订这一处。旧Q1／Q2／Q3裁决及原7044条已审记录完整继承，无关材料不重跑。</p>
<p>本轮替换211条未审CT，新增239条规则候选；R2的241条记录改用统一AA身份，其中106条未审侧段CT对齐至保留的中央行。82条未审H3环记录只纠正原图来源，保留原几何与完整来源历史。当前共10254条CT、334个AA、696个POLY记录；这些是几何对象与候选数量，不是器件数或准确率。</p>
<section class="hold"><h2>只剩一处新增人工核对：右上末段是4条栅，还是旧模型的5条？</h2><p>上端引出方向已经确认，不再重问。重新定位时，原图可分辨4组栅端亮条及其间的5列源漏孔；旧POLY排了5条。这一块已停止导出CT，保留旧材料并标为数量冲突，没有为多余栅补孔。下方可切换宽视野、放大原图、旧模型与4条替代方案。替代方案尚未进入工作层。</p><p><a href="#COUNT">查看唯一问题</a> · <a href="#full">全幅分层视图</a> · <a href="human-review.json">裁决原文</a> · <a href="stage-gate.json">阶段门</a> · <a href="preservation-check.json">前后保护检查</a> · <a href="ledger.json">逐项变更</a></p></section>
<section id="full"><h2>统一全幅：同一模型、四层独立开关</h2><p>{controls}</p>{whole}<p><a href="O-preview.png">全幅PNG</a> · <a href="../ct-work-layer-closeout-v3/index.html">上一版待审候选</a></p></section>
<p>原图和规则几何使用各自坐标，未做未经验证的回投影。5px方孔／3px孔距／1px包围及避让预算保持；几何通过不等于真实PDK DRC或全层人工验收。两小AA、上沿长条及无直接CT的内部扩散仍按证据保留未知，不补虚构孔；未知范围不等于全部有漏孔。M1和新net未扩展。</p>'''
(A/'index.html').write_text(header+cards+'</html>')
provenance=B/'provenance';provenance.mkdir(exist_ok=True)
for name in ['prepare_ct_reviewed_v4.py','package_ct_reviewed_v4.py']:shutil.copyfile('/tmp/'+name,provenance/name)
(provenance/'README.md').write_text('这些是本次审计配方，不是新增生产案例接口或已封装skill。生产执行使用冻结spec与通用ct_transfer命令，输出到新的runs目录。禁止在已冻结v4目录重跑配方。\n')
class Resources(HTMLParser):
    def __init__(self):super().__init__();self.paths=[]
    def handle_starttag(self,t,a):
        d=dict(a)
        for f in ['src','href','value']:
            v=d.get(f,'')
            if v and not v.startswith(('#','http','javascript:')) and ('.' in v):self.paths.append(v)
parser=Resources();parser.feed((A/'index.html').read_text())
for path in parser.paths:assert (A/path.split('#')[0]).exists(),path
for f in A.glob('*.svg'):ET.parse(f)
for f in A.glob('*.png'):
    with Image.open(f) as im:im.verify()
ui=dict(status='PASS_static_assets_and_structure',local_resource_references=len(parser.paths),
        selector_count=(A/'index.html').read_text().count('<select'),layer_count=4,browser_render_not_automatically_tested=True)
wr(B/'ui-check-v1.json',ui)
print(json.dumps(dict(status='PASS',CT=len(objects),prior7044_exact=True,new_sources=len(source_ids),R2_single_row=len(shared),resources=ui['local_resource_references']),ensure_ascii=False))
