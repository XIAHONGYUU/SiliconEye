"""Package final candidate snapshot, explicit HOLD review gate and static/visual QA outputs."""
from pathlib import Path
import json,hashlib,shutil,re,xml.etree.ElementTree as ET
from html.parser import HTMLParser
from collections import Counter
from PIL import Image,ImageDraw
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from silicon_eye.geometry_reconstruction import object_polygon
root=Path.cwd();b=Path('benchmarks/ct-full-frame-remaining-v1');a=Path('docs/assets/ct-full-frame-remaining-v1');run=Path('runs/ct-full-frame-remaining-v1f');parent=Path('benchmarks/ct-lower-middle-mos-revision-v2')
def rd(p):return json.loads(Path(p).read_text())
def wr(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
s=rd(run/'spec.json');model=rd(run/'model.json');mat=rd(run/'material-model.json');report=rd(run/'report.json');gate=rd(b/'stage-gate-v1.json');old=rd(parent/'model-v1.json')['objects'];oldmat=rd(parent/'material-model-v1.json');new=model['objects'][len(old):]
assert len(old)==7044 and model['objects'][:7044]==old
assert mat['objects']==oldmat['objects'] and mat['AA_objects']==oldmat['AA_objects']
assert report['status']=='PASS' and gate['status'].startswith('HOLD') and gate['whole_frame_human_accepted'] is False
assert len(new)==gate['new_candidate_count'] and len(model['objects'])==gate['working_snapshot_count']
for ref in s['inputs'].values():assert sha(ref['path'])==ref['sha256']
for name,h in rd(parent/'verification-v1.json')['locked_files'].items():assert sha(parent/name)==h
for name,h in rd(parent/'acceptance-v1.json')['locked_files'].items():assert sha(parent/name)==h
shutil.copytree(run,a,dirs_exist_ok=True)
for name in ['model','material-model','report','ledger']:shutil.copyfile(run/f'{name}.json',b/f'{name}-v1.json')
# A geometric PASS must never masquerade as full-layer acceptance in a machine-readable snapshot.
model=dict(stage_status=gate['status'],whole_frame_complete=False,stage_gate_ref=dict(path=str(b/'stage-gate-v1.json'),sha256=sha(b/'stage-gate-v1.json')),objects=model['objects']);report.update(stage_status=gate['status'],geometry_status=report['status'],whole_frame_complete=False)
wr(b/'model-v1.json',model);wr(a/'model.json',model);wr(b/'report-v1.json',report);wr(a/'report.json',report)
for name in ['review-questions','stage-gate','quarantined-observations','deferred-source-paths','final-material-coverage','AA-band-audit','SD-recovery','last-SD-body-inspection','AI-terminal-direction-review','special-terminals']:shutil.copyfile(b/f'{name}-v1.json',a/f'{name}.json')
shutil.copyfile(b/'source-correspondence-repair-v2.json',a/'source-correspondence-repair.json')
shutil.copyfile(b/'source-context/compact-AA-context.jpg',a/'compact-AA-context.jpg')
# Show whole deferred source paths, not hundreds of hypothetical contact squares.
deferred=set(rd(b/'deferred-source-paths-v1.json')['families']);paths=[z for obj in rd(b/'AA-band-audit-v1.json')['AA_objects'] for z in obj.get('strips',[]) if z['id'] in deferred]
for file in a.glob('*-layout.svg'):
 text=file.read_text();overlays=[]
 for z in paths:
  p1,p2=z['layout_path'];overlays.append(f'<g><title>{z["id"]}: entire source correspondence HOLD, not CT</title><path d="M{p1[0]},{p1[1]} L{p2[0]},{p2[1]}" stroke="#ffb45b" stroke-width="2" stroke-dasharray="5 3"/></g>')
 if file.name.startswith('Q3'):
  key=file.name.split('-')[0];gid={'Q3A':'G07-P02','Q3B':'G62-P04','Q3C':'SG-U04-080'}[key];g=next(o for o in mat['objects'] if o['id']==gid);l,t,r,bt=Polygon(g['layout_outline']).bounds;ax,ay={'Q3A':(4964.8549,377),'Q3B':(1287.7228,3239.6125),'Q3C':(5082.194,642)}[key];overlays.append(f'<g font-size="12" font-family="sans-serif"><circle cx="{(l+r)/2}" cy="{t+4}" r="5" fill="none" stroke="#ffb45b"/><text x="{r+7}" y="{t+9}" fill="#ffb45b">G</text><text x="{ax+7}" y="{ay-6}" fill="#56baff">A</text></g>')
 text=text.replace('</svg>',''.join(overlays)+'</svg>');file.write_text(text)
oldids={o['id'] for o in old};allaa=unary_union([object_polygon(o) for o in mat['AA_objects']]);viewport_shapes=[(o,Polygon(o['layout_outline'])) for o in model['objects']]
for c in s['cases']:
 l,t,r,bt=c['layout_bbox'];view=box(l,t,r,bt);scale=min(3,1800/(r-l));im=Image.new('RGB',(round((r-l)*scale),round((bt-t)*scale)),'#111c28');d=ImageDraw.Draw(im)
 def pts(ring):return [((x-l)*scale,(y-t)*scale) for x,y in ring.coords]
 active=allaa.intersection(view);polys=list(active.geoms) if hasattr(active,'geoms') else [active];polys=[p for p in polys if p.geom_type=='Polygon']
 for p in sorted(polys,key=lambda p:Polygon(p.exterior).area,reverse=True):
  if p.is_empty:continue
  d.polygon(pts(p.exterior),fill='#315548',outline='#86b5a5')
  for h in p.interiors:d.polygon(pts(h),fill='#111c28')
 for o in mat['objects']:
  p=Polygon(o['layout_outline'])
  if p.intersects(view):d.line(pts(p.exterior),fill='#f7c85c',width=2)
 for o,p in viewport_shapes:
  if p.intersects(view):d.polygon(pts(p.exterior),fill='#829ca6' if o['id'] in oldids else '#ed8eff' if o.get('landing_material')=='POLY' else '#65baff')
 for z in paths:
  aa1,aa2=z['layout_path'];q=__import__('shapely').geometry.LineString([aa1,aa2])
  if q.intersects(view):d.line([((x-l)*scale,(y-t)*scale) for x,y in [aa1,aa2]],fill='#ffb45b',width=2)
 if c['id'].startswith('Q3'):
  gid={'Q3A':'G07-P02','Q3B':'G62-P04','Q3C':'SG-U04-080'}[c['id']];g=next(o for o in mat['objects'] if o['id']==gid);gl,gt,gr,gb=Polygon(g['layout_outline']).bounds;ax,ay={'Q3A':(4964.8549,377),'Q3B':(1287.7228,3239.6125),'Q3C':(5082.194,642)}[c['id']];d.text(((gr+6-l)*scale,(gt+4-t)*scale),'G',fill='#ffb45b');d.text(((ax+6-l)*scale,(ay-10-t)*scale),'A',fill='#56baff')
 im.save(a/f'{c["id"]}-preview.png')
questions=rd(b/'review-questions-v1.json')['questions'];qs=''.join('<li><a href="#'+q['id']+'"><b>'+q['id']+' '+q['title']+'</b></a>：'+q['question']+'</li>' for q in questions)
summary=f'''<section style="border:2px solid #ffb45b"><h2>HOLD：剩余范围已补查，整层尚未定稿</h2><p>本页新增<b>{len(new)}</b>个CT候选（AA {sum(o['landing_material']=='AA' for o in new)}、POLY {sum(o['landing_material']=='POLY' for o in new)}），工作快照共<b>{len(model['objects'])}</b>条。原7044条完整记录、695个POLY及335个AA对象逐条保持。新增候选不是已确认孔数，也不是器件数。</p><p><b>请只先回答以下三组关键问题，原批准不重审，也无需逐孔审批。</b></p><ol>{qs}</ol><p>Q3的三处对照：<a href="#Q3A">A 上方右MOS</a> · <a href="#Q3B">B 左下MOS</a> · <a href="#Q3C">C 上方右侧小MOS</a>。蓝A为拟对应的环参考，橙G为AI辨认的栅端。请核对来源对应，不是要求重审每个孔。</p><pre>Q1：真实栅端CT位于……
Q2：分别引出／共用端部；实际孔位在……
Q3-A：对应／需改……
Q3-B：对应／需改……
Q3-C：对应／需改……</pre><p>灰蓝为原工作记录；蓝／紫为新增AA／POLY接触假设。橙虚线是整段来源待核，<b>不是孔，也不是等待整批补满的格点</b>。Q1红叉表示“该亮点不能归这组栅”，不是说亮点本身不是CT。各视图保持自己的原生/设计坐标，切换不等于精确像素叠图。M1仅独立坐标宽视野参考。</p><p>安全子集通过方孔、间距、包围及沟道避让检查；另有{len(rd(b/'quarantined-observations-v1.json')['objects'])}条调查候选保留在隔离台账（含整段来源无效的候选，不能当真实漏孔数）。7条AA路径因来源反例整段暂缓；Q1的依赖源漏也不导出，不能删掉几个冲突点就宣布整段合格。</p><p><a href="stage-gate.json">整层HOLD质量门</a> · <a href="review-questions.json">裁决清单</a> · <a href="final-material-coverage.json">全部695个材料对象接续状态</a> · <a href="quarantined-observations.json">隔离观察台账</a> · <a href="SD-recovery.json">局部源漏补查</a> · <a href="compact-AA-context.jpg">11处未关联AA的源图定位缩览（位置仍待核，不据此推断有孔）</a></p></section>'''
page=a/'index.html';txt=page.read_text();pos=txt.index('<section');txt=txt[:pos]+summary+txt[pos:];txt=txt.replace('<section><h2>Q3A ','<span id="Q3"></span><section><h2>Q3A ',1)
# A group anchor is needed even on renderers whose section markup differs.
if 'id="Q3"' not in txt:txt=txt.replace(summary,summary+'<span id="Q3"></span>')
for c in s['cases']:
 needle=f'<option value="{c["id"]}-layout.svg">';start=txt.index(needle);end=txt.index('</option>',start)+len('</option>');txt=txt[:end]+f'<option value="{c["id"]}-preview.png">规则图PNG预览（SVG不可用时）</option>'+txt[end:]
page.write_text(txt)
# Record concrete Agent counterexamples; they are development cases, not an independent held-out evaluation.
wr(b/'agent-evaluation-v1.json',dict(dataset_kind='single_session_development_counterexamples_not_held_out_accuracy_test',cases=[dict(id='CE-source-host',observation='Q3 four-gate endpoint search reused source points already assigned in existing G18 and guard records',failure='one optical point has incompatible host assignments; correct ownership remains undecided',action='withhold four gate assignments and dependent16 SD records; request actual terminal source landmark'),dict(id='CE-ring-row',observation='G49 photo contains three neighbouring upper rows; initial POLY-end and ring locators selected the wrong row',action='independent frame-row and13 SD-column reinspection; upper row assigned to AA guard, only bottom gate contacts exported'),dict(id='CE-native-box',observation='109 weak/missing SD columns reinspected within bounded source windows;142 further optical candidates found; three tiny-body source maps recovered from gate-bar anchors',action='source geometry is a locator, not a material truth mask; source peaks still pass whole-model ownership/spacing gate'),dict(id='CE-quality',observation='geometric safety alone can pass a partial/inaccurate layer',action='separate safe-subset PASS from whole-frame HOLD; block entire source-path recipe after ownership counterexample')],human_truth_status='Q1/Q2/Q3 pending; no accuracy or recall claim'))
# Check all local links, graphics, JSON and selector behavior. Browser file navigation is not used as a workaround.
ids=[];callbacks=[]
class Check(HTMLParser):
 def handle_starttag(self,tag,attrs):
  attrs=dict(attrs)
  if 'id' in attrs:ids.append(attrs['id'])
  if 'onchange' in attrs:callbacks.append(attrs['onchange'])
  for k in ['src','href','value']:
   v=attrs.get(k,'')
   if v and re.search(r'\.(svg|png|jpg|json|html)$',v):assert (a/v).exists(),v
Check().feed(txt);assert len(ids)==len(set(ids))
for target in re.findall(r'href="#([^"]+)"',txt):assert target in ids,target
for file in a.glob('*.svg'):ET.parse(file)
for file in list(a.glob('*.png'))+list(a.glob('*.jpg')):
 with Image.open(file) as im:im.verify()
for file in b.glob('*.json'):rd(file)
Path('/tmp/check-ct-remaining-ui.cjs').write_text('const elements=Object.fromEntries('+json.dumps(ids)+'.map(id=>[id,{src:""}]));\n'+'\n'.join('new Function("document",'+json.dumps(c)+').call({value:"Q1-raw.png"},{getElementById:id=>elements[id]});' for c in callbacks)+'\nif(Object.entries(elements).some(([id,e])=>id!=="Q3" && e.src!=="Q1-raw.png"))throw Error("switch failed");console.log("PASS simulated select callbacks");')
wr(b/'packaging-check-v1.json',dict(status='PASS',parent7044_records_unchanged=True,AA335_POLY695_records_unchanged=True,new_CT=len(new),total_CT=len(model['objects']),all_input_hashes_valid=True,parent_acceptance_and_verification_hashes_valid=True,stage_status='HOLD',safe_subset_geometry='PASS',source_decision_cases=['Q1','Q2','Q3'],static='SVG_XML_PNG_decode_JSON_links_anchors_PASS',browser_render='not_automatically_tested_known_file_URL_security_restriction',snapshot_sha256={n:sha(b/n) for n in ['model-v1.json','material-model-v1.json','spec-v1.json','report-v1.json','selected-contacts-v1.json','quarantined-observations-v1.json','stage-gate-v1.json']}))
print('PACKAGED',len(new),'new',len(model['objects']),'total; input and parent hashes, SVG/PNG/JSON/links/anchors PASS; whole stage HOLD')
