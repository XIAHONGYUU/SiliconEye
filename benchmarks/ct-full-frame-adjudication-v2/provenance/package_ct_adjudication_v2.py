"""Package the scoped adjudication results and immutable before/after evidence.
Run from repo with .venv Python after the existing ct_transfer CLI. Audit recipe only.
"""
from pathlib import Path
import json,hashlib,shutil,copy,html,subprocess
from collections import Counter
from html.parser import HTMLParser
import xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial import cKDTree
from PIL import Image,ImageDraw
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from silicon_eye.geometry_reconstruction import object_polygon
B=Path('benchmarks/ct-full-frame-adjudication-v2');P=Path('benchmarks/ct-full-frame-remaining-v1');A=Path('docs/assets/ct-full-frame-adjudication-v2');R=Path('runs/ct-full-frame-adjudication-v2d');A.mkdir(exist_ok=True)
def rd(p):return json.loads(Path(p).read_text())
def wr(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
parent=rd(P/'model-v1.json')['objects'];parent_by={o['id']:o for o in parent};model=rd(R/'model.json');objects=model['objects'];newby={o['id']:o for o in objects};mat=rd(R/'material-model.json');oldmat=rd(P/'material-model-v1.json');spec=rd(B/'spec-v1.json');report=rd(R/'report.json');review=rd(B/'human-review-v1.json');decisions=rd(B/'human-decision-status-v1.json')
assert report['status']=='PASS' and len(objects)==10025
for r in spec['inputs'].values():assert sha(r['path'])==r['sha256']
for n,h in rd(P/'verification-v1.json')['locked_files'].items():assert sha(P/n)==h
assert mat['AA_objects']==oldmat['AA_objects'];assert mat['objects'][:695]==oldmat['objects'];assert len(mat['objects'])==696
retired=set(review['authorized_contact_ids']);corrected=set(review['authorized_source_correspondence_ids']);added=set(review['authorized_new_contact_ids']);assert set(parent_by)-set(newby)==retired;assert set(newby)-set(parent_by)==added
for key in set(parent_by)&set(newby):
 if key in corrected:
  before=parent_by[key];after=copy.deepcopy(newby[key]);history=after.pop('source_correspondence_history');after['source_evidence']=history[-1]['before'];assert after==before
 else:assert newby[key]==parent_by[key],key
prior7044=rd('benchmarks/ct-lower-middle-mos-revision-v2/model-v1.json')['objects'];assert all(o['id'] in newby and newby[o['id']]['layout_outline']==o['layout_outline'] and newby[o['id']]['layout_center']==o['layout_center'] for o in prior7044)
# Additional source ownership check for the changed observations, independent of layout DRC.
allpoints=np.array([o['source_evidence']['native_center'] for o in objects]);tree=cKDTree(allpoints);near=[]
for i,j in sorted(tree.query_pairs(3.0)):
 a,b=objects[i],objects[j]
 if not {a['id'],b['id']}&(added|corrected):continue
 at=a.get('POLY_target',a.get('AA_target'));bt=b.get('POLY_target',b.get('AA_target'))
 if at!=bt:near.append(dict(ids=[a['id'],b['id']],targets=[at,bt],distance=float(np.linalg.norm(allpoints[i]-allpoints[j]))))
assert not near,near
wr(B/'preservation-and-source-check-v1.json',dict(status='PASS',prior_7044_geometry_and_targets_retained=True,prior_7044_exact_records_retained=7039,prior_7044_source_correction_records=5,all335_AA_and695_POLY_records_exact_equal=True,added_POLY_ids=['G68-BOTTOM-BUS-01'],exact_parent10004_records_retained=9994,retired_unaccepted_gate_CT_ids=sorted(retired),source_corrected_CT_ids=sorted(corrected),new_CT_count=len(added),new_or_relocalized_source_conflicts_with_other_targets_within3px=near,all_v1_locked_JSON_unchanged=True,all_input_hashes_valid=True,whole_frame_human_accepted=False))
polys={o['id']:Polygon(o['layout_outline']) for o in mat['objects']};bus=polys['G68-BOTTOM-BUS-01'];assert all(bus.intersection(polys[k]).area>0 for k in ['G68-P01','G68-P02'])
wr(B/'connection-check-v1.json',dict(shared_bus_intersects_both_fingers=True,member_ids=['G68-P01','G68-P02'],shared_CT_ids=['CTA-Q2-BUS-0','CTA-Q2-BUS-1'],exact_bus_geometry_status='AI_candidate',new_M1_or_net_connection_inferred=False))
paths=rd(P/'deferred-source-paths-v1.json')['families'];assert len(paths)==8
status='HOLD_technical_source_path_reinspection'
stage=dict(status=status,human_decision_gate='PASS_Q1_Q2_Q3_scoped_decisions',blocking_human_cases=[],pending_human_questions=[],geometry_status='PASS',whole_frame_complete=False,whole_frame_human_accepted=False,technical_source_paths_pending=paths,deferred_path_count=len(paths),not_automatically_releasing_paths_after_role_confirmation=True,physical_PDK_DRC=False,note='Five human decisions are closed. Eight legacy source-path recipes still need independent reinspection, not another request to approve these five questions.')
wr(B/'stage-gate-v1.json',stage);model.update(stage_status=status,whole_frame_complete=False,stage_gate_ref=ref(B/'stage-gate-v1.json'));report.update(stage_status=status,geometry_status='PASS',whole_frame_complete=False,human_questions_resolved=['Q1','Q2','Q3A','Q3B','Q3C'])
wr(B/'model-v1.json',model);wr(B/'material-model-v1.json',mat);wr(B/'report-v1.json',report);wr(B/'ledger-v1.json',rd(R/'ledger.json'))
# Classify old investigation observations rather than treating every withheld point as a new question.
items=[]
for z in rd(P/'quarantined-observations-v1.json')['objects']:
 o=z['candidate'];gid=o.get('POLY_target','')
 disposition='technical_source_or_geometry_check_retained'
 if o['id'] in added:disposition='released_Q1_dependent_SD_candidate'
 elif gid.startswith('CL2-Q3-AA'):disposition='retired_upper_ring_wrong_gate_role' if '-top-' in o['id'] else 'superseded_by_reinspected_bottom_CT'
 elif o['family'] in paths:disposition='entire_source_path_still_deferred_not_human_question'
 items.append(dict(observation_id=o['id'],disposition=disposition,original_evidence_ref=ref(P/'quarantined-observations-v1.json')))
wr(B/'prior-observation-disposition-v1.json',dict(objects=items,counts=dict(Counter(o['disposition'] for o in items)),not_physical_missing_hole_counts=True))
shutil.copytree(R,A,dirs_exist_ok=True)
for n,f in [('model','model-v1'),('material-model','material-model-v1'),('report','report-v1'),('stage-gate','stage-gate-v1'),('human-decision-status','human-decision-status-v1'),('preservation-and-source-check','preservation-and-source-check-v1'),('connection-check','connection-check-v1'),('optical-reinspection','optical-reinspection-v1'),('prior-observation-disposition','prior-observation-disposition-v1')]:shutil.copyfile(B/(f+'.json'),A/(n+'.json'))
oldids=set(parent_by)-retired;unionAA=unary_union([object_polygon(o) for o in mat['AA_objects']]);shapes=[(o,Polygon(o['layout_outline'])) for o in objects]
refsA={'Q3A':(4964.8549,(389.9474+406.1441)/2,'AA2-TOP-H3-AA-0'),'Q3B':(1287.7228,3239.6125,'AA2-LEFT-GUARD-NETWORK-SHARED-GUARDS-4'),'Q3C':(5082.194,642,'AA2-TOP-STEP-2-AA-0')}
refsG={'Q3A':'G07-P02','Q3B':'G62-P04','Q3C':'SG-U04-080'}
for c in spec['cases']:
 key=c['id'];l,t,r,b=c['layout_bbox'];view=box(l,t,r,b);scale=min(3,1800/(r-l));im=Image.new('RGB',(round((r-l)*scale),round((b-t)*scale)),'#111c28');d=ImageDraw.Draw(im)
 def points(coords):return [((x-l)*scale,(y-t)*scale) for x,y in coords]
 ac=unionAA.intersection(view);parts=list(ac.geoms) if hasattr(ac,'geoms') else [ac]
 for p in sorted([p for p in parts if p.geom_type=='Polygon'],key=lambda p:Polygon(p.exterior).area,reverse=True):
  if p.is_empty:continue
  d.polygon(points(p.exterior.coords),fill='#315548',outline='#86b5a5')
  for ring in p.interiors:d.polygon(points(ring.coords),fill='#111c28')
 for o in mat['objects']:
  p=polys[o['id']]
  if p.intersects(view):d.line(points(p.exterior.coords),fill='#f7c85c',width=2)
 for o,p in shapes:
  if p.intersects(view):d.polygon(points(p.exterior.coords),fill='#829ca6' if o['id'] in oldids else '#ed8eff' if o.get('landing_material')=='POLY' else '#65baff')
 svg= (A/f'{key}-layout.svg').read_text();glyphs=[]
 if key in refsA:
  x,y,aid=refsA[key];g=polys[refsG[key]];gl,gt,gr,gb=g.bounds;glyphs.append(f'<g font-size="12"><path d="M{x-45},{y} L{x+45},{y}" stroke="#56baff" stroke-width="2"/><text x="{x+50}" y="{y+4}" fill="#56baff">A: {aid}</text><text x="{gr+6}" y="{gt+4}" fill="#ffb45b">G</text></g>');d.line(points([(x-45,y),(x+45,y)]),fill='#56baff',width=3);d.text(points([(x+47,y-10)])[0],'A',fill='#56baff');d.text(points([(gr+6,gt+2)])[0],'G',fill='#ffb45b')
  if key=='Q3A':
   glyphs.append(f'<text x="{gl}" y="{gb+16}" font-size="10" fill="#ffb45b">no bottom gate CT</text>');d.text(points([(gl,gb+5)])[0],'no bottom gate CT',fill='#ffb45b')
 if key=='Q1':
  for i,gid in enumerate(['CL2-Q3-AA-F01613-01','CL2-Q3-AA-F01613-02','CL2-Q3-AA-F01614-01','CL2-Q3-AA-F01614-02']):
   p=polys[gid];x,y=p.centroid.x,p.bounds[3]+10;glyphs.append(f'<text x="{x}" y="{y}" fill="#ed8eff" font-size="9">G{i+1}</text>');d.text(points([(x-5,y)])[0],f'G{i+1}',fill='#ed8eff')
 (A/f'{key}-layout.svg').write_text(svg.replace('</svg>',''.join(glyphs)+'</svg>'));im.save(A/f'{key}-preview.png')
 # Independent source photograph coordinates; no projection of design polygons onto the photo.
 bb=c['source_bbox'];raw=Image.open('data/test_chip/tile_full/poly.jpg').crop(bb);draw=ImageDraw.Draw(raw)
 def xy(pt):return (pt[0]-bb[0],pt[1]-bb[1])
 if key in ['Q1','Q2']:
  for o in objects:
   if not o['id'].startswith('CTA-'+key):continue
   x,y=xy(o['source_evidence']['native_center']);draw.ellipse((x-5,y-5,x+5,y+5),outline='#ed8eff',width=2)
  if key=='Q1':draw.line([xy((742,1183)),xy((943,1183))],fill='#65baff',width=2);draw.text((15,15),'Q1: bottom gate CT / upper A guard CT',fill='#ffcf55')
  else:draw.line([xy((2252,1688)),xy((2300,1688))],fill='#ffb45b',width=1);draw.text((12,12),'Q2: shared bottom POLY; circles = observed CT',fill='#ffcf55')
 else:
  g=next(o for o in objects if o.get('POLY_target')==refsG[key] and '-top-' in o['id']);x,y=g['source_evidence']['native_center'];cx,cy=xy((x,y));draw.ellipse((cx-4,cy-4,cx+4,cy+4),outline='#ffb45b',width=2);draw.text((cx+7,cy),'G',fill='#ffb45b');draw.line((cx-80,cy-32,cx+80,cy-32),fill='#56baff',width=2);draw.text((cx-85,cy-49),'A inner guard' if key=='Q3A' else 'A guard',fill='#56baff')
 raw.save(A/f'{key}-inspection.png')
# Keep selectors from existing renderer; add before and annotated/PNG modes without mutating v1.
page=(A/'index.html').read_text()
for c in spec['cases']:
 key=c['id'];needle=f'<option value="{key}-layout.svg">';pos=page.index('</option>',page.index(needle))+len('</option>');page=page[:pos]+f'<option value="{key}-preview.png">修订后PNG备用图</option><option value="{key}-inspection.png">原图＋裁决位置</option><option value="../ct-full-frame-remaining-v1/{key}-preview.png">修订前联合图（历史候选）</option>'+page[pos:]
summary='''<section class="summary"><h2>五项裁决已记录并执行</h2><p>Q1四管下端栅CT，上方原红X为环CT；Q2共用下端POLY，孔在连接处；Q3A仅上端栅CT，A对应更靠近栅极的内环；Q3B/C身份对应保持。</p><p>原始裁决与精确重建分开：新增26条候选（Q1栅8、Q2共用端2、恢复源漏16），撤回5条未审下端栅CT，5条G18照片来源纠正并保留原始证据；共10025条工作记录。原7044条几何和目标不变，全部335 AA与原695 POLY逐条保留，另加1个共用端POLY对象。新精确孔数及边界未获得人工像素验收。</p><p><b>本页不要求重审这五项。</b>人审问题已关闭；几何检查PASS，但整层仍HOLD：旧版有8条来源路径需要技术回查，不因身份确认直接整段释放。旧文写7条，实际锁定清单是8条，历史原件不改。没有新M1/net推断，也不宣称真实PDK DRC通过。</p><p>各视图使用各自原生／设计坐标，切换用于对应比较，不是精准叠投影。可以切换修订前／后、原图和裁决标记；双击放大。</p><p><a href="human-review.json">裁决原文与范围</a> · <a href="stage-gate.json">阶段门</a> · <a href="preservation-and-source-check.json">前后保护与来源检查</a> · <a href="connection-check.json">共用POLY连接检查</a> · <a href="prior-observation-disposition.json">旧调查候选处置</a></p></section>'''
pos=page.index('<section>');page=page[:pos]+summary+page[pos:];(A/'index.html').write_text(page)
# Freeze audit recipes with a warning that they are not production entrypoints.
prov=B/'provenance';prov.mkdir(exist_ok=True)
for src in ['/tmp/prepare_ct_adjudication_v2.py','/tmp/package_ct_adjudication_v2.py']:shutil.copyfile(src,prov/Path(src).name)
(prov/'README.md').write_text('本目录为2026-10-21局部裁决执行的审计配方，不是新增生产案例脚本或CT skill。已验收／冻结目录不得原地重跑覆盖。正式执行复用ct_transfer的受控修订接口；人审语义和AI测量分开。\n')
wr(B/'correspondence-references-v1.json',dict(A_layout_references=refsA,G_material_references=refsG,Q3A_prior_outer_A_label_replaced_only=True,Q3_reference_native_coordinates_unchanged=True))
ids=[];links=[]
class Check(HTMLParser):
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if a.get('id'):ids.append(a['id'])
  for k in ['src','href','value']:
   v=a.get(k,'')
   if v.endswith(('.png','.jpg','.svg','.json','.html')):links.append(v)
Check().feed(page)
assert len(ids)==len(set(ids))
for link in links:assert (A/link).exists(),link
for p in A.glob('*.svg'):ET.parse(p)
for p in A.glob('*.png'):
 with Image.open(p) as image:image.verify()
print('PACKAGED',dict(total=len(objects),human_gate='PASS_scoped',geometry='PASS',whole_frame=status,local_links=len(links),AA_unchanged=335,POLY_unchanged=695))
